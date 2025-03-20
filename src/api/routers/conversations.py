from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models.chat import (
    User, Project, Conversation, MessageDB,
    ProjectCreate, ProjectResponse,
    ConversationCreate, ConversationUpdate, ConversationResponse, ConversationDetail,
    Message
)
from ..auth import get_current_active_user

router = APIRouter(tags=["conversations"])

# Projects endpoints
@router.post("/projects/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_project = Project(
        name=project.name,
        description=project.description,
        user_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/projects/", response_model=List[ProjectResponse])
async def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    projects = db.query(Project).filter(Project.user_id == current_user.id).offset(skip).limit(limit).all()
    return projects

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def read_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update any conversations to remove project_id
    db.query(Conversation).filter(
        Conversation.project_id == project_id
    ).update({"project_id": None})
    
    db.delete(project)
    db.commit()
    return None

# Conversations endpoints
@router.post("/conversations/", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify project exists and belongs to user if provided
    if conversation.project_id:
        project = db.query(Project).filter(
            Project.id == conversation.project_id,
            Project.user_id == current_user.id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    db_conversation = Conversation(
        title=conversation.title,
        project_id=conversation.project_id,
        user_id=current_user.id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@router.get("/conversations/", response_model=List[ConversationResponse])
async def read_conversations(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    pinned_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    
    if project_id is not None:
        query = query.filter(Conversation.project_id == project_id)
    
    if pinned_only:
        query = query.filter(Conversation.is_pinned == True)
    
    # Sort by pinned first, then by most recent update
    conversations = query.order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    return conversations

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def read_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation

@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify conversation exists and belongs to user
    db_conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Verify project exists and belongs to user if updating project_id
    if conversation_update.project_id is not None:
        project = db.query(Project).filter(
            Project.id == conversation_update.project_id,
            Project.user_id == current_user.id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Update conversation fields
    update_data = conversation_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_conversation, key, value)
    
    db_conversation.updated_at = datetime.now()
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete associated messages first (cascade would work too, but being explicit)
    db.query(MessageDB).filter(MessageDB.conversation_id == conversation_id).delete()
    
    db.delete(conversation)
    db.commit()
    return None