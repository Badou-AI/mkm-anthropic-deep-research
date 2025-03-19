from pydantic import BaseModel
from typing import List, Optional, Literal

class SearchRequest(BaseModel):
    query: str
    search_type: Literal["simple", "deep_iterative"] = "simple"
    constraints: Optional[str] = None
    complexity: Optional[Literal["low", "medium", "high"]] = "medium"
    max_iterations: Optional[int] = 3

class SearchResponse(BaseModel):
    results: List[str]
    raw_data: Optional[str] = None
