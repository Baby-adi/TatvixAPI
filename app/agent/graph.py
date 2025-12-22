from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph,START,END,MessagesState
from langchain_core.messages import HumanMessage,SystemMessage,AIMessage,ToolMessage
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain_core.messages.utils import trim_messages,count_tokens_approximately
from langchain.messages import RemoveMessage
from typing import Literal,Optional,List
import certifi,os
from langgraph.prebuilt import ToolNode,tools_condition
from app.agent.utils.states import ChatState
from app.agent.utils.mcp_client import McpClient
from langgraph.graph.state import CompiledStateGraph
from app.agent.utils.prompts import prompt_templates
from app.settings import settings
from typing import ClassVar

# Force Python to use certifi's CA bundle so TLS/HTTPS validation works
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


class LegalAgent():
    _cahced_tools: ClassVar[Optional[List]] = None #Global class cache for MCP tools.
    
    def __init__(self):
        self.tools = None
        self.model = None
        self.checkpointer:Optional[MongoDBSaver] = None
        self._graph:Optional[CompiledStateGraph] = None
        
    @classmethod
    async def init_legal_agent(cls):
        """ Method to get mcp tools while creating class instance consistently. """
        self = cls()
        if cls._cahced_tools is None:
            cls._cahced_tools = await self._get_mcp_tools()
        self.tools = cls._cahced_tools
        self.model = self._initialize_model()
        print(self.tools)
        return self

    async def _get_mcp_tools(self):
        """ Method to get mcp tools from mcp server. """
        client = McpClient()
        return await client._init_tools()

    def _initialize_model(self):
        """ Method to initialize chat model """
        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            max_retries=2
        ).bind_tools(self.tools)
        return model

    def _append_query(self, state: ChatState) -> ChatState:
        """ Node to append user query to messages reducer """
        query = state.get("user_query") #Get user query
        messages = state.get("messages") #Get overall message state
        messages.append(HumanMessage(content=query)) #Append user query to message state reducer
        return {"messages":messages} #Return message state object as the node output

    def _tool_node(self, state: ChatState) -> ToolNode:
        """ Node to wrap retrieved tool list with a prebuilt ToolNode class for an appropriate Tool function in the compilable graph """
        return ToolNode(tools=self.tools)

    def _should_summarize(self, state:ChatState) -> Literal["summary_node","chat_node"]:
        """ conditional edge to make sure if more than n messages have accumilated, summarize chat history """
        user_msg = [m for m in state.get("messages") if isinstance(m, HumanMessage)] #Count only the number of pormpts asked by the user.
        if len(user_msg) > 3: #Set to 3 for test purposes.
            return "summary_node"
        return "trim_input_context"

    def _summary_node(self, state: ChatState) -> ChatState:
        """ Node to build summaries of accumilated messages in message state reducer to improve checkpointer performance/Model performance """
        summary = state.get("summary","")
        if summary:
            summary_message = (
                f"This is the summary of the conversation to date: {summary}\n"
                "Extend the summary by taking into account the new messages above:\n"
                "Make sure the summary is no more than 100 tokens in length please"
            )
        else:
            summary_message = "Create a summary of the conversation above:"
        #Add the summary to the state reducer and invoke the model for summarized input
        messages = state.get("messages") + [HumanMessage(content=summary_message)]
        try:
            response = self.model.invoke(messages)
            print(response.content)
            #Remove everything but the last 2 messages as a summary already exists now
            delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
            return {"summary": response.content, "messages": delete_messages}

        except Exception as e:
            print(f"Exception -> {e}")
            raise e

    def _trim_tool_output(self, state: ChatState) -> ChatState:
        """ Node to explicitly trim tool message length"""
        default_messages = state.get("messages")
        history_to_trim = default_messages[-2:] #The last 2 messages is always AI message followed by tool call output, hence trimming pipeline is deterministically made.
        to_trim = [x for x in history_to_trim if type(x) is ToolMessage or AIMessage] #Tool output messages to trim.
        try:
            trimmed_tool_output = trim_messages(
                to_trim,
                strategy = "last",
                token_counter = count_tokens_approximately, #Passes an estimated token count of the base message input.
                max_tokens = 7000,
                start_on = "ai",
                end_on = ("tool")
            )

            trimmed = [] #Make sure sequence of trimmedoutput is in the correct sequence our LLM expects the input in. (Human/System Message followed by AI/Tool Message)
            for msg in default_messages:
                if isinstance(msg, (HumanMessage, SystemMessage)):
                    trimmed.append(msg)
                elif isinstance(msg, (AIMessage, ToolMessage)):
                    if msg in trimmed_tool_output:
                        trimmed.append(msg)

        except Exception as e:
            raise e

        return {"messages": trimmed }

    def _trim_input_context(self, state: ChatState) -> ChatState:
        """ Node to trim input context to make sure context window size is not exceeded by the token length of the input for the large language model input"""
        try:
            trimmed_messages = trim_messages(
                state.get("messages"),
                strategy="last",
                token_counter=count_tokens_approximately, #Passes an estimated token count of the base message input.
                max_tokens=3000,
                start_on="human",
                end_on=("human","tool")
            )

        except Exception as e:
            raise e

        return {"messages": trimmed_messages}

    def _chat_node(self, state: ChatState) -> ChatState:
        """ Node to initiate conversation with the chat model """
        default_messages = state.get("messages")
        final_message = [SystemMessage(content=prompt_templates.system_template)] + default_messages
        summary = state.get("summary")
        if summary:
            print(f"Summary so far: {summary}")
            system_message = f"Summary of previous conversation is : {summary}"
            messages = [SystemMessage(content=system_message), *final_message]
        else:
            messages = [*final_message]

        try:
            response = self.model.invoke(messages)

        except Exception as e:
            raise e

        return {"messages": [response]}

    def _build_graph(self):
        """ Create langgraph agent workflow and complie it """
        if self._graph is None:
            try:
                builder = StateGraph(ChatState)
                builder.add_node("append_query",self._append_query)
                builder.add_node("tools",self._tool_node)
                builder.add_node("trim_input_context",self._trim_input_context)
                builder.add_node("trim_tool_output",self._trim_tool_output)
                builder.add_node("summary_node",self._summary_node)
                builder.add_node("chat_node",self._chat_node)

                builder.add_edge(START,"append_query")
                builder.add_conditional_edges(
                    "append_query",
                    self._should_summarize,
                    {"trim_input_context":"trim_input_context","summary_node":"summary_node"}
                )
                builder.add_edge("summary_node","trim_input_context")
                builder.add_edge("trim_input_context","chat_node")
                builder.add_conditional_edges("chat_node",tools_condition)
                builder.add_edge("tools","trim_tool_output")
                builder.add_edge("trim_tool_output","chat_node")

                if self.checkpointer is None:
                    raise RuntimeError("checkpointer not initialized! Use app.state.legal_agent.checkpointer")

                self._graph = builder.compile(checkpointer=self.checkpointer)

            except Exception as e:
                print(f"Exception -> {e}") #Log
                raise e

        return self._graph

    async def get_response(self, message:str, session_id:str):
        """ Get response from the LLM for user question """
        if self.checkpointer is None:
            raise RuntimeError("No Memory for the agent to go with, make sure checkpointer is set!")
        
        if self._graph is None:
            self._graph = self._build_graph()

        config = {
            "configurable" : {"thread_id" : session_id}
        }

        try:
            response = await self._graph.ainvoke({"user_query": message},config)
            print(response["messages"]) #LOG
            """tool_messages = [
                m for m in response["messages"]
                if isinstance(m, ToolMessage)
            ] #Extract all the tool messages from the messages list from graph state.
            print(tool_messages)
            """
            return response

        except Exception as e:
            raise e

    def clear_chat(self, session_id:str):
        """ Clear current session from lang graph checkpointer """
        try:
            response = self.checkpointer.delete_thread(session_id)
            return response
        except Exception as e:
            raise e