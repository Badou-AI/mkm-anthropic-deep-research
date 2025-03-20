from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from beanie import Document, Link, PydanticObjectId
from beanie.odm.operators.update.general import Set

# MongoDB document models
class UserModel(Document):
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "users"
        use_state_management = True

class ProjectModel(Document):
    name: str
    description: Optional[str] = None
    user_id: PydanticObjectId
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "projects"
        use_state_management = True

class MessageModel(Document):
    role: str  # "user", "assistant", "system"
    content: str
    conversation_id: PydanticObjectId
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "messages"
        use_state_management = True

class ConversationModel(Document):
    title: str
    is_pinned: bool = False
    user_id: PydanticObjectId
    project_id: Optional[PydanticObjectId] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "conversations"
        use_state_management = True
    
    # Helper method to fetch related messages
    async def get_messages(self) -> List[MessageModel]:
        return await MessageModel.find(
            MessageModel.conversation_id == self.id
        ).sort("+timestamp").to_list()
    
    # Helper method to update the timestamp
    async def touch(self):
        await self.update(Set({ConversationModel.updated_at: datetime.now()}))

# Pydantic models for API
class Message(BaseModel):
    role: Literal["user", "assistant", "system"] 
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "claude-3-7-sonnet-latest"
    max_tokens: Optional[int] = 2048
    system_prompt: Optional[str] = None
    conversation_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    message: Message
    stop_reason: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    
    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: str
    project_id: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    project_id: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    is_pinned: bool
    project_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ConversationDetail(ConversationResponse):
    messages: List[Message] = []
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None