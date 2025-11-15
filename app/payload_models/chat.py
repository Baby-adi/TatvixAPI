from pydantic import BaseModel

class ChatPayload(BaseModel):
    user_query: str