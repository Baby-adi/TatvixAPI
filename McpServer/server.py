from fastmcp import FastMCP
import weaviate,requests
from McpServer.weaviate_client import get_weaviate_client
from weaviate.classes.query import MetadataQuery
from dotenv import load_dotenv
import os
from collections import defaultdict
from McpServer.utils.query_structure import SearchResponse,SearchResult
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".mcp.env"
load_dotenv(env_path, override=True)

WEAVIATE_SERVER=os.getenv("WEAVIATE_SERVER")
GOOGLE_SEARCH_KEY=os.getenv("GOOGLE_SEARCH_KEY")
CX=os.getenv("CX")
GOOGLE_SEARCH_ENGINE = os.getenv("GOOGLE_SEARCH_ENGINE")

mcp = FastMCP(__name__)

weaviate_client = get_weaviate_client()
print(f"\n\n\n{WEAVIATE_SERVER}\n\n\n")

@mcp.tool
def document_search(query:str) -> dict:
    """ Tool to perform near vector search using gemma 300m embedding model with the help of weaviate vector db. """
    try:
        print(f"\n\n\n{WEAVIATE_SERVER}\n\n\n")
        documents = weaviate_client.collections.use("Vectorbase")
        query_params = {
            'embed_type':'query'
        }
        response = requests.post(WEAVIATE_SERVER,params=query_params,json={"text":[query]})
        data = response.json()
        vector = data["vectors"][0]

        top_k_response = documents.query.near_vector(
            near_vector=vector,
            limit=5,
            return_metadata=MetadataQuery(distance=True),
        )

        final_response = defaultdict(list)

        for o in top_k_response.objects:
            final_response["text"].append(o.properties["text"])
            final_response["document_name"].append(o.properties["doc_name"])
            final_response["image_id"].append(o.properties["image_id"])
            #Logs for testing.
            print(o.properties["doc_name"])
            print(o.metadata.distance)


        return final_response

    except Exception as e:
        return {"Error":f"Exception -> {e}"}

@mcp.tool
def search_engine(query :str) -> SearchResponse:
    """ Tool to perform google search for online refernces to the use case of users. """
    search_params = {
        "key":GOOGLE_SEARCH_KEY,
        "cx":CX,
        "q":query
    }
    try:
        response = requests.get(GOOGLE_SEARCH_ENGINE, params=search_params, timeout=10)
        response.raise_for_status()
        search_results = response.json()
    
    except Exception as e:
        return SearchResponse(results=[]) # Make sure Agent workflow does not break if tool call fails.

    items = search_results.get("items")
    content = []

    for item in items:
        content.append(SearchResult(
            title=item.get('title',''),
            link=item.get('link',''),
            snippet=item.get('snippet','')
        ))
    
    return SearchResponse(results=content)


if __name__ == "__main__": #For dev use case to run the file as script, so we define file specific entry point, can be run through CLI.
    mcp.run(transport="http",port=5050)
