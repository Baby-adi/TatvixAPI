from langgraph.graph.message import MessagesState

class ChatState(MessagesState):
    """
    Messages State: Has a default add_message reducer to buil message history dynamically.
        (messages : Annotated[list[AnyMessage],add_messages])
    """
    user_query : str
    summary : str = "" # Seperate state to maintain current summary state rather then completely depending on messages.
    heading : str # Seperate state for the model which generates a heading on the conversation that is on-going.
    #document_data: str #Seperate state to maintain current document text data.



