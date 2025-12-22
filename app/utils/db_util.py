from fastapi import Request,Depends
from sqlmodel import Session
from typing import Annotated
from app.db_models.models import PDFImage


def get_sql_session(request: Request):
        """ Method to initialize database session object """
        with Session(request.app.state.sqlite_config.engine) as session:
            yield session

def reconstruct_text_to_image(request: Request):
    pass

#Build session dependency object to inject the appropriate session per user request
SQLSessionDep = Annotated[Session, Depends(get_sql_session)]