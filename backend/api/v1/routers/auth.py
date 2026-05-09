"""Authentication router."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta

from services.auth_service import (
    authenticate_user,
    create_access_token,
    get_all_users,
    seed_users,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    role: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "student"


@router.on_event("startup")
async def startup():
    await seed_users()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token."""
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(
        data={"username": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=User)
async def register(req: RegisterRequest, token: str = Depends(oauth2_scheme)):
    """Register new user (admin only or first user)."""
    from services.auth_service import get_user_from_token
    
    current_user = get_user_from_token(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check role - only admin can create users, or first user
    if current_user["role"] != "admin":
        # Check if any users exist
        users = await get_all_users()
        if len(users) > 0:
            raise HTTPException(status_code=403, detail="Only admins can create users")
    
    # Create user
    try:
        from database.users import create_user as db_create_user
        from passlib.hash import argon2
        
        new_user = await db_create_user(
            req.username,
            argon2.hash(req.password),
            req.role
        )
        return {"username": new_user["username"], "role": new_user["role"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.get("/me", response_model=User)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user info from token."""
    from services.auth_service import get_user_from_token
    
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"username": user["username"], "role": user["role"]}


@router.get("/users")
async def list_users():
    """List available users."""
    users = await get_all_users()
    return {"users": users}