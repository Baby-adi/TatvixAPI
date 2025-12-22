from pydantic import BaseModel
from typing import List

class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str
    
class SearchResponse(BaseModel):
    results: List[SearchResult]