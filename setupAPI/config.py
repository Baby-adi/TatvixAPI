import mongoengine as me
import os
from dotenv import load_dotenv
import weaviate
from weaviate import WeaviateClient
import time

load_dotenv()
os.environ.pop('SSL_CERT_FILE', None) #For overriding TLS check for weaviate client for local development.

class Config():
    def __init__(self):
        me.connect(host=os.getenv("MONGODB_URI"))
        self.weaviate_client = self._get_weaviate_client()


    def _get_weaviate_client(self) -> WeaviateClient:
        retries = 5
        for attempt in range(retries):
            try:
                client = weaviate.connect_to_custom(
                    http_host="localhost",
                    http_port=8080,
                    http_secure=False,
                    grpc_host="localhost",
                    grpc_port=50051,
                    grpc_secure=False,
                )
                return client

            except Exception as e:
                print(f"Weaviate connection failed (attempt {attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(5)
                else:
                    raise RuntimeError("Failed to connect to Weaviate after multiple retries.") from e
