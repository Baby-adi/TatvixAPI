from fastapi import APIRouter,Depends,Request,HTTPException
from app.utils.security import security
from typing import Annotated,Literal
from app.db_models.models import User,Chat,Message
from app.agent.graph import LegalAgent
from app.utils.db_util import SQLSessionDep
from sqlmodel import select
from app.payload_models.chat import ChatPayload

router = APIRouter(prefix="/api")

def get_legal_agent(request: Request):
    """ Dependency to inject agent instance with correctly initialized global checkpointer. """
    agent = LegalAgent()
    agent.checkpointer = request.app.state.checkpointer
    return agent


@router.get("/chat",status_code=200)
def find_chat(
    request: Request,
    current_user: Annotated[User,Depends(security.get_current_user)],
    session: SQLSessionDep,
    chat_id: None|str = None
):
    if chat_id is None:
        try:
            new_chat_id = security.create_chat_hash(current_user.id)
            new_chat = Chat(id=new_chat_id, owner_id=current_user.id)
            try:
                session.add(new_chat)
                session.commit()
            except Exception as e:
                print(e) #LOG
                session.rollback()
                raise HTTPException(500, {"code": "DB_ERROR", "message": "Failed to start chat"})

        except Exception as e:
            print(e) #LOG
            raise HTTPException(status_code=500,detail={"code":"INTERNAL_SERVER_ERROR","message":"Could not create record"})

        return {
                "code":"CHAT_CREATED",
                "message":"chat created successfully",
                "chat_id":new_chat_id
            }

    else:
        try:
            is_chat = session.exec(select(Chat).where(Chat.id == chat_id)).first()
            if not is_chat:
                raise HTTPException(status_code=403,detail={"code":"UNAUTHORIZED","message":"chat does not belong to the right user"})
            

            if is_chat.owner_id != current_user.id:
                raise HTTPException(403, {"code": "UNAUTHORIZED", "message": "chat does not belong to the right user"})

            #Returns a list of instances of messages of human and ai ordered by time created
            messages = session.exec(select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)).all()
        
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500,detail={"code":"INTERNAL_SERVER_ERROR","message":"Could not load record"})
        
        return {
                "code":"CHAT_RETRIEVED",
                "message":"chat history found successfully",
                "messages":messages,
                "chat_id": chat_id
            }



@router.post("/chat/{chat_id}",status_code=200)
async def talk_chat(
    request: Request,
    current_user: Annotated[User,Depends(security.get_current_user)],
    legal_agent: Annotated[LegalAgent,Depends(get_legal_agent)],
    session: SQLSessionDep,
    chat_id: str,
    chat: ChatPayload
):
    try:
        # Retrieve chat id to check if it exists or not.
        is_chat = session.exec(select(Chat).where(Chat.id == chat_id)).first()
        if not is_chat:
            raise HTTPException(status_code=404,detail={"code":"NOT_FOUND","message":"chat could not be found"})

        # Check user authenticity.
        if current_user.id != is_chat.owner_id:
            raise HTTPException(status_code=403,detail={"code":"UNAUTHORIZED","message":"chat does not belong to the right user"})
        
        user_query = chat.user_query
        if not user_query:
            raise HTTPException(status_code=500,detail={"code":"INTERNAL_SERVER_ERROR","message":"user query is not passed"})
        
        response = await legal_agent.get_response(message=user_query,session_id=chat_id)
        content = response.get("messages",[])
        if not content:
            raise HTTPException(500, detail={"code": "INTERNAL_SERVER_ERROR", "message": "No messages in model response, try again"})

        print(content[-1].text) #LOG

        if response:
            human_message = Message(chat_id=chat_id,role="human",content=user_query)
            ai_message = Message(chat_id=chat_id,role="ai",content=content[-1].text)
            try:
                session.add(human_message)
                session.add(ai_message)
                session.commit()
            except Exception as e:
                session.rollback()
                print(e) #LOG
                raise HTTPException(500, {"code": "DB_ERROR", "message": "Failed to save messages"})
        
    
    except Exception as e:
        print(e) #LOG
        raise HTTPException(status_code=500,detail={"code":"INTERNAL_SERVER_ERROR","message":"There was a problem processing the model"})
    
    return {
            "code":"MODEL_RESPONSE_SUCCESS",
            "message":"Model has successfully returned a response",
            "content":content[-1].text,
            "chat_id":chat_id
        }



