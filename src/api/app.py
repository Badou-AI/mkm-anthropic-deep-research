from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.chat import router as chat_router
from .routers.search import router as search_router
from .routers.conversations import router as conversations_router
from .routers.users import router as users_router
from .database import connect_to_mongo, close_mongo_connection

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
    
    # Add event handlers for MongoDB connection
    @app.on_event("startup")
    async def startup_db_client():
        await connect_to_mongo()
    
    @app.on_event("shutdown")
    async def shutdown_db_client():
        await close_mongo_connection()
    
    # Add routers
    app.include_router(chat_router)
    app.include_router(search_router)
    app.include_router(conversations_router)
    app.include_router(users_router)
    
    return app