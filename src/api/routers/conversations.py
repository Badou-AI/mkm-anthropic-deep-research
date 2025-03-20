from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId

from ..database import get_db
from ..models.chat import (
    UserModel, ProjectModel, ConversationModel, MessageModel,
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
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_project = ProjectModel(
        name=project.name,
        description=project.description,
        user_id=current_user.id
    )
    await db_project.insert()
    
    return ProjectResponse(
        id=str(db_project.id),
        name=db_project.name,
        description=db_project.description,
        created_at=db_project.created_at
    )

@router.get("/projects/", response_model=List[ProjectResponse])
async def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    projects = await ProjectModel.find(
        ProjectModel.user_id == current_user.id
    ).skip(skip).limit(limit).to_list()
    
    return [
        ProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            created_at=project.created_at
        ) for project in projects
    ]

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def read_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        object_id = PydanticObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    
    project = await ProjectModel.find_one(
        ProjectModel.id == object_id,
        ProjectModel.user_id == current_user.id
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        created_at=project.created_at
    )

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        object_id = PydanticObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    
    project = await ProjectModel.find_one(
        ProjectModel.id == object_id,
        ProjectModel.user_id == current_user.id
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update any conversations to remove project_id
    await ConversationModel.find(
        ConversationModel.project_id == object_id
    ).update({"$set": {"project_id": None}})
    
    await project.delete()
    
    return None

# Conversations endpoints
@router.post("/conversations/", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Verify project exists and belongs to user if provided
    project_id = None
    if conversation.project_id:
        try:
            project_id = PydanticObjectId(conversation.project_id)
            project = await ProjectModel.find_one(
                ProjectModel.id == project_id,
                ProjectModel.user_id == current_user.id
            )
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        except:
            raise HTTPException(status_code=400, detail="Invalid project ID format")
    
    db_conversation = ConversationModel(
        title=conversation.title,
        project_id=project_id,
        user_id=current_user.id
    )
    await db_conversation.insert()
    
    return ConversationResponse(
        id=str(db_conversation.id),
        title=db_conversation.title,
        is_pinned=db_conversation.is_pinned,
        project_id=str(db_conversation.project_id) if db_conversation.project_id else None,
        created_at=db_conversation.created_at,
        updated_at=db_conversation.updated_at
    )

@router.get("/conversations/", response_model=List[ConversationResponse])
async def read_conversations(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = None,
    pinned_only: bool = False,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Build query
    query = {"user_id": current_user.id}
    
    if project_id:
        try:
            query["project_id"] = PydanticObjectId(project_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid project ID format")
    
    if pinned_only:
        query["is_pinned"] = True
    
    # Find and sort conversations
    conversations = await ConversationModel.find(query).sort([
        ("is_pinned", -1),  # Sort pinned first
        ("updated_at", -1)   # Then by recent update
    ]).skip(skip).limit(limit).to_list()
    
    return [
        ConversationResponse(
            id=str(conv.id),
            title=conv.title,
            is_pinned=conv.is_pinned,
            project_id=str(conv.project_id) if conv.project_id else None,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        ) for conv in conversations
    ]

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def read_conversation(
    conversation_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        object_id = PydanticObjectId(conversation_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    
    conversation = await ConversationModel.find_one(
        ConversationModel.id == object_id,
        ConversationModel.user_id == current_user.id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Fetch messages for this conversation
    messages = await MessageModel.find(
        MessageModel.conversation_id == object_id
    ).sort("+timestamp").to_list()
    
    # Convert to API messages
    api_messages = [
        Message(
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp
        ) for msg in messages
    ]
    
    return ConversationDetail(
        id=str(conversation.id),
        title=conversation.title,
        is_pinned=conversation.is_pinned,
        project_id=str(conversation.project_id) if conversation.project_id else None,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=api_messages
    )

@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        object_id = PydanticObjectId(conversation_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    
    # Verify conversation exists and belongs to user
    conversation = await ConversationModel.find_one(
        ConversationModel.id == object_id,
        ConversationModel.user_id == current_user.id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Verify project exists and belongs to user if updating project_id
    if conversation_update.project_id is not None:
        if conversation_update.project_id:
            try:
                project_id = PydanticObjectId(conversation_update.project_id)
                project = await ProjectModel.find_one(
                    ProjectModel.id == project_id,
                    ProjectModel.user_id == current_user.id
                )
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")
            except:
                raise HTTPException(status_code=400, detail="Invalid project ID format")
    
    # Build update data
    update_data = {}
    if conversation_update.title is not None:
        update_data["title"] = conversation_update.title
    
    if conversation_update.is_pinned is not None:
        update_data["is_pinned"] = conversation_update.is_pinned
    
    if conversation_update.project_id is not None:
        update_data["project_id"] = PydanticObjectId(conversation_update.project_id) if conversation_update.project_id else None
    
    # Only update if we have something to update
    if update_data:
        update_data["updated_at"] = datetime.now()
        await conversation.update({"$set": update_data})
        await conversation.fetch()  # Refresh from DB
    
    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        is_pinned=conversation.is_pinned,
        project_id=str(conversation.project_id) if conversation.project_id else None,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        object_id = PydanticObjectId(conversation_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    
    conversation = await ConversationModel.find_one(
        ConversationModel.id == object_id,
        ConversationModel.user_id == current_user.id
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete associated messages first
    await MessageModel.find(MessageModel.conversation_id == object_id).delete_many()
    
    # Delete the conversation
    await conversation.delete()
    
    return None