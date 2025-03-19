from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from ..models.search import SearchRequest, SearchResponse
from anthropic_openai import AgentLoop
from anthropic_openai.settings import Credentials

router = APIRouter(prefix="/search", tags=["search"])

def get_agent_loop():
    credentials = Credentials()
    return AgentLoop(
        openai_api_key=credentials.openai_api_key,
        anthropic_api_key=credentials.anthropic_api_key
    )

@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest):
    agent_loop = get_agent_loop()
    
    try:
        if request.search_type == "simple":
            # Parse query into expanded queries (assuming comma-separated)
            expanded_queries = [q.strip() for q in request.query.split(",")]
            search_context_size = "auto"  # or "comprehensive" or "detailed"
            
            # Call simple web search
            results = agent_loop.simple_web_search(
                expanded_queries=expanded_queries,
                search_context_size=search_context_size
            )
        else:  # deep_iterative
            # Call deep iterative search
            results = agent_loop.deep_iterative_web_search(
                query=request.query,
                user_contraints=request.constraints or "",
                task_complexity=request.complexity or "medium",
                max_iterations=request.max_iterations or 3
            )
        
        # Process results
        text_results = []
        raw_data = ""
        
        for result in results:
            if result.get("type") == "text":
                raw_data = result.get("text", "")
                # Split by delimiter and add to results
                for item in raw_data.split("\n\n---$$$---\n\n"):
                    text_results.append(item)
        
        return SearchResponse(
            results=text_results,
            raw_data=raw_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
