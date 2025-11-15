from sqlmodel import Field,SQLModel,Relationship
import mongoengine as me
from datetime import datetime,timezone
import uuid

class PDFImage(me.DynamicDocument):
    filename = me.StringField(required=True)  # Store filename
    file = me.FileField(required=True)  # Store image in GridFS
    image_id = me.UUIDField(required=True,default=uuid.uuid4,binary=False) # Generate a unique id for each image

class ExtractedText(me.DynamicDocument):
    image = me.ReferenceField(PDFImage)  # Link to image
    text = me.StringField(required=True)
    time_stamp = me.DateTimeField(default=lambda: datetime.now(timezone.utc))  # Store timestamp of extraction


class User(SQLModel, table=True):
    id: int|None = Field(primary_key=True,default=None) #Set to none for initialize use, db uses an auto generated primary key
    username: str = Field(unique=True)
    password: str
    chats: list["Chat"] = Relationship(back_populates="user") #Defines one to many relationship with chat table.


class Chat(SQLModel, table=True):
    id: str = Field(primary_key=True) #Chat id, each user chat has a subsequent chat id
    owner_id: int|None = Field(default=None,foreign_key="user.id")

    user: User = Relationship(back_populates="chats") #When i call user.chats, i will get the full chat instance for that particular user.
    messages: list["Message"] = Relationship(back_populates="chat")

class Message(SQLModel, table=True):
    id: int|None = Field(primary_key=True,default=None)

    chat_id: str = Field(foreign_key="chat.id")
    role: str
    content: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    chat: Chat = Relationship(back_populates="messages")




