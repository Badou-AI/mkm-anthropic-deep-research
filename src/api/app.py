from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.chat import router as chat_router
from .routers.search import router as search_router
from .routers.conversations import router as conversations_router
from .routers.users import router as users_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Anthropic-OpenAI Agent API",
        description="API for the Anthropic-OpenAI Agent System",
        version="0.1.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For production, restrict to your frontend domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add routers
    app.include_router(chat_router)
    app.include_router(search_router)
    app.include_router(conversations_router)
    app.include_router(users_router)
    
    return app