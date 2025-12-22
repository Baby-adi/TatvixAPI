from fastapi import APIRouter,HTTPException,Depends
from app.utils.db_util import SQLSessionDep
from app.db_models.models import User
from app.payload_models.authenticate import Auth,Token
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.security import security
from sqlmodel import select
from datetime import timedelta
from app.settings import settings
from typing import Annotated

router = APIRouter(prefix="/api/auth")

@router.post("/signup",status_code=201)
def signup(data:Auth, db_session:SQLSessionDep):
    """
    SignUp logic ->
        args -> data : type(Auth) validated by Auth Pydantic BaseModel
                db_session : a dependency of database session per request
    """
    try:
        hashed_password = security.hash_password(password=data.password) #hash your password using security object
        user = User(username=data.username,password=hashed_password)
        # Add user record to db with current session objcet
        db_session.add(user)
        db_session.commit()

        return {"code":"USER_CREATED","message":"Username created successfully!"}

    except HTTPException as e:
        raise e


@router.post("/login",status_code=200)
def login(data:Annotated[OAuth2PasswordRequestForm, Depends()], db_session:SQLSessionDep):
    """
    Login logic ->
        args -> data : OAuth2PasswordRequestForm that has a dependency on the input data.(It is used as a base class OAuth format for collecting user data)
                db_session : a dependency of database session per request
    """
    try:
        user = db_session.exec(select(User).where(User.username == data.username)).first()
        if not user:
            raise HTTPException(status_code=401,detail={"code":"WRONG_CREDENTIALS","message":"Username or password is wrong!"})
        
        if not security.verify_password(password=data.password,hashed_password=user.password):
            raise HTTPException(status_code=401,detail={"code":"WRONG_CREDENTIALS","message":"Username or password is wrong!"})

        access_token_expiry = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data = {"usr":user.username}, expire_time=access_token_expiry
        )
        return Token(access_token=access_token,token_type="bearer")

    except HTTPException as e:
        raise e