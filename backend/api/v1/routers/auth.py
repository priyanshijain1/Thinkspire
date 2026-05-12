"""Authentication router."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token,
    invalidate_token,
    validate_password_strength,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class User(BaseModel):
    username: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class PasswordValidation(BaseModel):
    valid: bool
    message: str


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login - returns short-lived access + long-lived refresh token."""
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(user["username"])
    refresh_token = create_refresh_token(user["username"])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str):
    """Refresh - exchange refresh token for new access token."""
    payload = verify_token(refresh_token, "refresh")
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    username = payload.get("username")
    new_access = create_access_token(username)
    new_refresh = create_refresh_token(username)
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Logout - invalidate current token."""
    invalidate_token(token)
    return {"message": "Logged out successfully"}


@router.post("/signup", response_model=User)
async def signup(req: RegisterRequest):
    """Self-signup - anyone can create an account."""
    # Validate password strength
    is_valid, message = validate_password_strength(req.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    try:
        from database.users import create_user as db_create_user
        from passlib.hash import argon2
        
        new_user = await db_create_user(
            req.username,
            argon2.hash(req.password),
        )
        return {"username": new_user["username"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database unavailable. Try again.")


@router.post("/validate-password")
async def validate_password(password: str):
    """Check password strength (for frontend meter)."""
    from services.auth_service import get_password_strength
    
    is_valid, message = validate_password_strength(password)
    strength = get_password_strength(password)
    
    return {
        "valid": is_valid,
        "message": message,
        "strength": strength,
    }


@router.get("/me", response_model=User)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user info from token."""
    from services.auth_service import get_user_from_token
    
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {"username": user["username"]}