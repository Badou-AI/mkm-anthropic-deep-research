from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta
from beanie import PydanticObjectId

from ..database import get_db
from ..models.chat import UserModel, UserCreate, UserResponse, Token
from ..auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(tags=["users"])

@router.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    # Check if username exists
    db_user = await UserModel.find_one(UserModel.username == user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    db_email = await UserModel.find_one(UserModel.email == user.email)
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    
    await new_user.insert()
    
    return UserResponse(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email
    )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email
    )