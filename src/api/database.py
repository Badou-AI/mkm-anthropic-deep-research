import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import asyncio
from typing import Optional, List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGODB_DB", "anthropic_chatbot")

# MongoDB client instance
client: Optional[AsyncIOMotorClient] = None

async def connect_to_mongo():
    """Creates connection to MongoDB and initializes document models"""
    global client
    try:
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        await client.server_info()  # Validate connection
        logger.info("Connected to MongoDB")
        
        # Import models here to avoid circular imports
        from .models.chat import (
            UserModel,
            ProjectModel,
            ConversationModel,
            MessageModel
        )
        
        # Initialize beanie with document models
        await init_beanie(
            database=client[DATABASE_NAME],
            document_models=[
                UserModel,
                ProjectModel,
                ConversationModel,
                MessageModel
            ]
        )
        logger.info("Initialized Beanie ODM with document models")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        client = None
        logger.info("Closed MongoDB connection")

# Get DB as a dependency
async def get_db():
    if client is None:
        await connect_to_mongo()
    return client[DATABASE_NAME]

# Initialize DB on startup
async def init_db():
    """Initialize MongoDB connection asynchronously (for startup)"""
    await connect_to_mongo()

# Don't initialize DB here - we'll do it in the FastAPI startup event
try:
    pass  # Removed synchronous init_db() call
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise e