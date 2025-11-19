from pwdlib import PasswordHash
from datetime import datetime,timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException
from app.db_models.models import User
from sqlmodel import select
from app.utils.db_util import SQLSessionDep
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from app.settings import settings
import jwt
import uuid

oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")

class Security():
    
    def __init__(self):
        self.hash_object = PasswordHash.recommended() #Use the reccomended password hash settings

    def hash_password(self,password:str):
        """ Utility to hash user password """
        return self.hash_object.hash(password)

    def verify_password(self,password:str, hashed_password:str):
        """ Utility to verify user password """
        return self.hash_object.verify(password, hashed_password)
    
    def create_access_token(self, data:dict, expire_time: timedelta):
        """
        Utility to create access token for user authentication and authorization
        args -> data : dict -> a dictionary of user info to be encoded in jwt
                expire_time : timedelta -> expire time for the token
        """
        to_encode = data.copy()
        if expire_time:
            expire = datetime.now() + expire_time

        to_encode.update({"exp" : expire})
        encoded_jwt = jwt.encode(to_encode,settings.JWT_SECRET_KEY,algorithm=settings.ENC_ALGORITHM)
        return encoded_jwt
    
    def get_current_user(self, token: Annotated[str, Depends(oauth2_schema)], db_session: SQLSessionDep):
        """
        Utility to get current user for every protected endpoint
        It Authorizes if the user access bearer token is valid or not

        args -> token : Annotated[str, Depends(oauth2_schema)], a dependency on oauth2_schema object (has url encoded info too)
                db_session : SessionDep, a database session dependency object for executing db operation per request
        """
        try:
            payload = jwt.decode(token,settings.JWT_SECRET_KEY, algorithms=[settings.ENC_ALGORITHM])
            username = payload.get("usr")
            expiry = payload.get("exp")

            if datetime.fromtimestamp(expiry) - datetime.now() < timedelta(0):
                raise HTTPException(status_code=401,detail={"code":"TOKEN_EXPIRY","message":"Session has expired!"})
            
            if username is None:
                raise HTTPException(status_code=401,detail={"code":"UNAUTHORIZED_ACCESS","message":"Unauthorized Access!"})
            
            user = db_session.exec(select(User).where(User.username == username)).first()

            if user is None:
                raise HTTPException(status_code=401,detail={"code":"UNAUTHORIZED_ACCESS","message":"Unauthorized Access!"})
            
            return user

        except InvalidTokenError as e:
            raise e
        
    @staticmethod
    def create_chat_hash(userid) -> str:
        """ Method to create unique user id combination for chat session. """
        return f"{userid}-{uuid.uuid4()}"

security = Security()