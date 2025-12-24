from app.settings import settings
from sqlmodel import create_engine,SQLModel,Session
from mongoengine import connect,disconnect
import weaviate
from weaviate import WeaviateClient
from pymongo import MongoClient
from fastapi import Request


class SQLiteConfig():
    def __init__(self):
        self.file_name=settings.SQLITE_DB_NAME
        self.url=f"sqlite:///{self.file_name}"
        self.connection_args = {
            "check_same_thread":False #Make sure multi-threaded sessions are possible
        }
        self.engine = create_engine(self.url,connect_args=self.connection_args)
        self._create_db_and_tables()

    def _create_db_and_tables(self):
        """ Method to create database and all default tables if not created. """
        SQLModel.metadata.create_all(self.engine)
    
class MongoDBConfig():
    def __init__(self):
        connect(host=settings.MONGODB_URI,alias="TatvixDB")
    
    def disconnect(self):
        """ Method to release MongoEngine connection object to database. """
        disconnect(alias="TatvixDB")

class PyMongoConfig():
    def __init__(self):
        self.pymongo_client = MongoClient(settings.MONGODB_URI)


class WeaviateConfig():
    def __init__(self):
        self.client = self._get_weaviate_client()

    @staticmethod
    def _get_weaviate_client() -> WeaviateClient:
        """ Get weaviate client object """
        client =  weaviate.connect_to_custom(
            http_host="localhost",
            http_secure=False,
            http_port=8080,
            grpc_host="localhost",
            grpc_port=50051,
            grpc_secure=False,
        )
        return client


def get_sqlite_config():
    return SQLiteConfig()

def get_mongo_config():
    return MongoDBConfig()

def get_weaviate_client():
    return WeaviateConfig()

def get_pymongo_client():
    return PyMongoConfig()

