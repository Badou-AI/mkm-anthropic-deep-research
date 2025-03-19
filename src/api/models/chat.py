from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

class Message(BaseModel):
    role: Literal["user", "assistant", "system"] 
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "claude-3-7-sonnet-latest"
    max_tokens: Optional[int] = 2048
    system_prompt: Optional[str] = None
    
class ChatResponse(BaseModel):
    message: Message
    stop_reason: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
