from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr

# SQLAlchemy models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    projects = relationship("Project", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    conversations = relationship("Conversation", back_populates="project")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    is_pinned = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    project = relationship("Project", back_populates="conversations")
    messages = relationship("MessageDB", back_populates="conversation", order_by="MessageDB.timestamp")

class MessageDB(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20))
    content = Column(Text)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    timestamp = Column(DateTime, default=datetime.now)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

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
    conversation_id: Optional[int] = None
    
class ChatResponse(BaseModel):
    message: Message
    stop_reason: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[int] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: str
    project_id: Optional[int] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    project_id: Optional[int] = None

class ConversationResponse(BaseModel):
    id: int
    title: str
    is_pinned: bool
    project_id: Optional[int]
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