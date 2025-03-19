from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, AsyncGenerator
import json
import asyncio

from ..models.chat import ChatRequest, ChatResponse, Message
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
async def chat(request: ChatRequest):
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
    
    return ChatResponse(
        message=Message(
            role="assistant",
            content=text_content
        ),
        stop_reason=stop_reason,
        tool_calls=tool_calls
    )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent_loop = get_agent_loop()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Parse the request
            messages = [Message(**msg) for msg in request_data.get("messages", [])]
            model = request_data.get("model", "claude-3-7-sonnet-latest")
            max_tokens = request_data.get("max_tokens", 2048)
            system_prompt = request_data.get("system_prompt", "You are a helpful assistant.")
            
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
            
            # Stream chunks to the client
            for chunk in completion_stream:
                if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text_delta"):
                    await websocket.send_text(json.dumps({
                        "type": "chunk",
                        "content": chunk.delta.text
                    }))
                elif chunk.type == "message_delta":
                    await websocket.send_text(json.dumps({
                        "type": "stop",
                        "stop_reason": chunk.delta.stop_reason
                    }))
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        print(f"Error: {e}")
