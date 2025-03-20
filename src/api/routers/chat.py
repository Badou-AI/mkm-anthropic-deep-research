from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, AsyncGenerator
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from beanie import PydanticObjectId

from ..models.chat import ChatRequest, ChatResponse, Message, ConversationModel, MessageModel, UserModel
from ..database import get_db
from ..auth import get_current_active_user, get_current_user, JWTError
from anthropic_openai import AgentLoop, Role, ChatMessage, StopReason
from anthropic_openai.settings import Credentials

router = APIRouter(prefix="/chat", tags=["chat"])

def get_agent_loop():
    credentials = Credentials()
    return AgentLoop(
        openai_api_key=credentials.openai_api_key,
        anthropic_api_key=credentials.anthropic_api_key
    )

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    agent_loop = get_agent_loop()
    
    # Convert from API models to internal models
    conversation_history = [
        ChatMessage(
            role=message.role,
            content=message.content
        ) for message in request.messages
    ]
    
    # Handle chat conversation
    system_prompt = request.system_prompt or "You are a helpful assistant."
    completion_stream = agent_loop.handle_conversation(
        conversation_history=conversation_history,
        system=system_prompt,
        model=request.model,
        max_tokens=request.max_tokens
    )
    
    # Process response
    stop_reason, history_delta = agent_loop.consume_stream(completion_stream)
    
    # Extract response content
    assistant_message = next((msg for msg in history_delta if msg.role == Role.ASSISTANT), None)
    if not assistant_message:
        raise HTTPException(status_code=500, detail="Failed to get response from AI")
    
    # Extract tool calls if any
    tool_calls = None
    if isinstance(assistant_message.content, list):
        tool_calls = [item for item in assistant_message.content if item.get("type") == "tool_use"]
    
    # Create response
    text_content = ""
    if isinstance(assistant_message.content, str):
        text_content = assistant_message.content
    elif isinstance(assistant_message.content, list):
        for item in assistant_message.content:
            if item.get("type") == "text":
                text_content += item.get("text", "")
    
    response_message = Message(
        role="assistant",
        content=text_content
    )
    
    # Save conversation if conversation_id provided or create new one
    conversation_id = request.conversation_id
    conversation = None
    
    if conversation_id:
        # Get existing conversation
        try:
            object_id = PydanticObjectId(conversation_id)
            conversation = await ConversationModel.find_one(
                ConversationModel.id == object_id,
                ConversationModel.user_id == current_user.id
            )
            
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        except:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    else:
        # Create new conversation with first user message as title (truncated)
        title = request.messages[0].content if request.messages else "New Conversation"
        title = (title[:50] + "...") if len(title) > 50 else title
        
        conversation = ConversationModel(
            title=title,
            user_id=current_user.id
        )
        await conversation.insert()
        conversation_id = str(conversation.id)
    
    # Save messages to database
    # First check if messages are already in the database
    for message in request.messages:
        # Skip saving if message might already exist
        if conversation_id:
            # Look for exact match to avoid duplicates
            existing_msgs = await MessageModel.find(
                MessageModel.conversation_id == conversation.id,
                MessageModel.role == message.role,
                MessageModel.content == message.content
            ).to_list()
            
            if existing_msgs:
                continue  # Skip if found
        
        # Add message to database
        db_message = MessageModel(
            role=message.role,
            content=message.content,
            conversation_id=conversation.id,
            timestamp=message.timestamp or datetime.now()
        )
        await db_message.insert()
    
    # Save assistant response
    db_assistant_message = MessageModel(
        role=response_message.role,
        content=response_message.content,
        conversation_id=conversation.id,
        timestamp=response_message.timestamp or datetime.now()
    )
    await db_assistant_message.insert()
    
    # Update conversation timestamp
    await conversation.update({"$set": {"updated_at": datetime.now()}})
    
    return ChatResponse(
        message=response_message,
        stop_reason=stop_reason,
        tool_calls=tool_calls,
        conversation_id=conversation_id
    )

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict] = {}
        
    async def connect(self, websocket: WebSocket, user_id: PydanticObjectId):
        await websocket.accept()
        self.active_connections[websocket] = {"user_id": user_id}
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
    
    async def send_json(self, websocket: WebSocket, data: Dict):
        if websocket in self.active_connections:
            await websocket.send_text(json.dumps(data))

manager = ConnectionManager()

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Authenticate the user based on token
        user = await get_current_user(token=token, db=db)
        await manager.connect(websocket, user.id)
    
    except JWTError:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    except Exception as e:
        await websocket.close(code=4000, reason=f"Connection error: {str(e)}")
        return
    
    agent_loop = get_agent_loop()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            try:
                # Parse the request
                messages = [Message(**msg) for msg in request_data.get("messages", [])]
                model = request_data.get("model", "claude-3-7-sonnet-latest")
                max_tokens = request_data.get("max_tokens", 2048)
                system_prompt = request_data.get("system_prompt", "You are a helpful assistant.")
                conversation_id = request_data.get("conversation_id", None)
                
                # Handle conversation in database if conversation_id provided or create new one
                conversation = None
                
                if conversation_id:
                    # Verify conversation exists and belongs to the user
                    try:
                        object_id = PydanticObjectId(conversation_id)
                        conversation = await ConversationModel.find_one(
                            ConversationModel.id == object_id,
                            ConversationModel.user_id == user.id
                        )
                        
                        if not conversation:
                            await manager.send_json(websocket, {
                                "type": "error",
                                "message": "Conversation not found"
                            })
                            continue
                    except:
                        await manager.send_json(websocket, {
                            "type": "error",
                            "message": "Invalid conversation ID format"
                        })
                        continue
                else:
                    # Create new conversation with first user message as title (truncated)
                    title = messages[0].content if messages else "New Conversation"
                    title = (title[:50] + "...") if len(title) > 50 else title
                    
                    conversation = ConversationModel(
                        title=title,
                        user_id=user.id
                    )
                    await conversation.insert()
                    conversation_id = str(conversation.id)
                    
                    # Send back the conversation_id to the client
                    await manager.send_json(websocket, {
                        "type": "conversation_created",
                        "conversation_id": conversation_id
                    })
                
                # Save user messages to database (only the most recent one)
                for message in messages:
                    if message.role == "user":  # Only save the most recent user message
                        # Check if this is the last user message
                        if message == messages[-1] or all(m.role != "user" for m in messages[messages.index(message)+1:]):
                            db_message = MessageModel(
                                role=message.role,
                                content=message.content,
                                conversation_id=conversation.id,
                                timestamp=message.timestamp or datetime.now()
                            )
                            await db_message.insert()
                
                # Convert to internal format
                conversation_history = [ChatMessage(role=msg.role, content=msg.content) for msg in messages]
                
                # Get completion stream
                completion_stream = agent_loop.handle_conversation(
                    conversation_history=conversation_history,
                    system=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    tools=[]
                )
                
                if completion_stream is None:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": "Failed to get completion stream from AI provider"
                    })
                    continue
                
                # Variables to accumulate response
                accumulated_response = ""
                
                # Stream chunks to the client
                for chunk in completion_stream:
                    if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text_delta"):
                        accumulated_response += chunk.delta.text
                        await manager.send_json(websocket, {
                            "type": "chunk",
                            "content": chunk.delta.text
                        })
                    elif chunk.type == "message_delta":
                        # Save complete response to database
                        db_message = MessageModel(
                            role="assistant",
                            content=accumulated_response,
                            conversation_id=conversation.id,
                            timestamp=datetime.now()
                        )
                        await db_message.insert()
                        
                        # Update conversation timestamp
                        await conversation.update({"$set": {"updated_at": datetime.now()}})
                        
                        await manager.send_json(websocket, {
                            "type": "stop",
                            "stop_reason": chunk.delta.stop_reason,
                            "conversation_id": conversation_id
                        })
                        break  # Ensure we exit the loop after stop message
                        
            except Exception as inner_e:
                print(f"Inner processing error: {inner_e}")
                await manager.send_json(websocket, {
                    "type": "error", 
                    "message": f"Processing error: {str(inner_e)}"
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")
    except Exception as e:
        manager.disconnect(websocket)
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Connection error: {str(e)}"
            })) 
        except:
            print(f"Could not send error to client: {e}")
        print(f"WebSocket error: {e}")