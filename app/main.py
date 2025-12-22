from fastapi import FastAPI,Depends
from contextlib import asynccontextmanager
from app.routes import authenticate,chat
from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings
from langgraph.checkpoint.mongodb import MongoDBSaver

origins = [
    settings.ALLOWED_ORIGIN,
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Method to instantiate/initialize certain objects and parameters during app startup and free them after shutdown """
    from app.dbconfig import get_sqlite_config,get_mongo_config,get_weaviate_client,get_pymongo_client
    app.state.sqlite_config = get_sqlite_config() #This will initialize the database connection string.
    app.state.mongo_config = get_mongo_config()
    app.state.weaviate_client = get_weaviate_client()
    pymongo = get_pymongo_client()
    app.state.checkpointer = MongoDBSaver(pymongo.pymongo_client)
    yield
    app.state.mongo_config.disconnect() #Free mongo db connection string object.
    print("Server Shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authenticate.router)
app.include_router(chat.router)
