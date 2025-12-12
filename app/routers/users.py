import os
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User
from app.schemas import *

from app.utils.send_email import send_reset_email
from app.utils.auth_utils import *

from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from dotenv import load_dotenv
load_dotenv()

router = APIRouter()


FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """ Create a new user account.
        Args:
            user(UserCreate): The user create user payload containing email, password, and role.
    """
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == user.email))
    existing_user = existing.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "email_exists",
                "message": "Email already exists. Please use another email."
            }
        )

    hashed_password = hash_password(user.password)
    
    # create user 
    new_user = User(
        email=user.email,
        full_name="",        
        role=user.role,
        hashed_password=hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate tokens
    payload = {"sub": str(new_user.id), "role": new_user.role}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    return {
        "success": True,
        "message": "User created successfully.",
        "user_id": new_user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/login", )
async def login_user(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """ Authenticate a user and return JWT access/refresh tokens.
        Args:
            data(LoginRequest): The login payload containing email and password.
    """
    normalized_email = data.email.strip().lower()

    # Check user by email
    query = await db.execute(select(User).where(User.email == normalized_email))
    user = query.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid email or password"}
        )

    # Verify password
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid email or password"}
        )

    # Generate tokens
    payload = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    return {
        "message": "Login successful.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }
    

@router.post("/verify-reset-token", status_code=200)
async def verify_reset_token(data: VerifyResetToken, db: AsyncSession = Depends(get_db)):
    """Verify if reset token is valid, exists, and not expired"""

    # Find user by token
    query = await db.execute(select(User).where(User.reset_token == data.token))
    user = query.scalar_one_or_none()

    # Token does not match any user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "valid": False,
                "message": "Invalid token"
            }
        )

    # Token expired
    if user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,  
            detail={
                "valid": False,
                "message": "Token expired"
            }
        )

    # Token valid
    return {
        "valid": True,
        "message": "Token is valid",
        "email": user.email
    }


@router.post("/forgot-password")
async def request_reset(data: RequestPasswordReset, db: AsyncSession = Depends(get_db)):
    """send reset password link email"""
    
    user = await db.execute(select(User).where(User.email == data.email))
    user_data = user.scalar_one_or_none()
    if not user_data:
        raise HTTPException(status_code=404, detail={"error": "Email not found"})

    token = generate_reset_token()
    expire_time = datetime.utcnow() + timedelta(minutes=30)

    user_data.reset_token = token
    user_data.reset_token_expires = expire_time

    await db.commit()

    reset_link = f"{FRONTEND_URL}?token={token}"
    try:
        email_sent = await send_reset_email(user_data.email, reset_link)
        if not email_sent:
            return {"success": False, "message": "Failed to send reset email. Please try again later."}
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Failed to send reset email. Please try again later."}
        )

    return {"message": "Password reset link sent to email"}


@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    """ verify user's reset-password token and changed the user's password with new one """
    
    user = await db.execute(select(User).where(User.reset_token == data.token))
    user_data = user.scalar_one_or_none()
    
    if not user_data:
        raise HTTPException(status_code=400, detail={"error": "Invalid token or token Expire"})

    if not user_data.reset_token_expires or user_data.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail={"error": "Token expired"})

    # update password
    user_data.hashed_password = hash_password(data.new_password)

    # clear token
    user_data.reset_token = None
    user_data.reset_token_expires = None

    await db.commit()

    return {
        "success": True,
        "message": "Password updated successfully"
    }
