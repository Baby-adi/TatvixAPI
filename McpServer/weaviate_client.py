import weaviate
import os
import certifi
import time

#SSL cert file bundles for python to use for connection to weaviate.
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

def get_weaviate_client():
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


