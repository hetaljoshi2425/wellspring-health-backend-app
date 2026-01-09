import os
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User
from app.schemas import *

from app.utils.send_email import send_reset_email
from app.utils.auth_utils import *
from app.log_config import get_logger

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi import Depends, APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

logger = get_logger("users")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/users")
async def list_users(
    role: Optional[str] = Query(None, description="Filter users by role"),
    search: Optional[str] = Query(None, description="Search by user name or email"),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Fetch paginated list of users.
    """
    try:
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == role)
            
        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(or_(User.user_name.ilike(search_term), User.email.ilike(search_term)))
        
        stmt = stmt.order_by(User.id.desc())
        
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
        
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        return {
            "success": True,
            "message": "Users fetched successfully.",
            "count": len(users),
            "page": page,
            "page_size": page_size,
            "data": [
                {
                    "id": user.id,
                    "email": user.email,
                    "user_name": user.user_name,
                    "role": user.role,
                    "gender": user.gender,
                    "created_at": getattr(user, "created_at", None)
                }
                for user in users
            ]
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Unexpected error occurred {str(e)}.",
            },
        )

@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """ Create a new user account.
        Args:
            user(UserCreate): The user create user payload containing email, password, and role.
    """
    try:
        # Check if email already exists
        existing = await db.execute(select(User).where(User.email == user.email))
        existing_user = existing.scalar_one_or_none()

        if existing_user:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "Email already exists. Please use another email."
                }
            )

        hashed_password = hash_password(user.password)
        
        # create user 
        new_user = User(
            email=user.email,
            user_name=user.user_name,
            full_name="",        
            role=user.role,
            gender=user.gender,
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
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Unexpected error occurred {str(e)}.",
            },
        )


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update user details.
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "User not found"})


        update_data = payload.model_dump(exclude_unset=True)
        
        if "email" in update_data:
            email = update_data["email"].lower().strip()

            email_check = await db.execute(select(User).where(User.email == email, User.id != user_id))
            existing_user = email_check.scalar_one_or_none()

            if existing_user:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "message": "Email already exists"})

            update_data["email"] = email

        # Update fields
        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        return {
            "success": True,
            "message": "User updated successfully",
            "data": {
                "id": user.id,
                "email": user.email,
                "user_name": user.user_name,
                "full_name": user.full_name,
                "role": user.role,
                "gender": user.gender,
                "is_active": user.is_active,
            },
        }

    except Exception as e:
        print("[Debug-]:",str(e))
        await db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Unexpected error occurred: {str(e)}",
            },
        )


@router.delete("/users/{user_id}/soft-delete")
async def soft_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "User not found"})

    user.is_active = False
    await db.commit()

    return {
        "success": True,
        "message": "User deactivated successfully",
    }
    
@router.delete("/users/{user_id}/hard-delete")
async def hard_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "message": "User not found"})

    await db.delete(user)
    await db.commit()

    return {
        "success": True,
        "message": "User Deleted successfully",
    }


@router.post("/login", )
async def login_user(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """ Authenticate a user and return JWT access/refresh tokens.
        Args:
            data(LoginRequest): The login payload containing email and password.
    """
    normalized_email = data.email.strip().lower()
    logger.info(f"normalized email: {normalized_email}")
    # Check user by email
    query = await db.execute(select(User).where(User.email == normalized_email))
    user = query.scalar_one_or_none()

    if not user:
        logger.error(f"User not found")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "Invalid email or password"}
        )

    # Verify password
    if not verify_password(data.password, user.hashed_password):
        logger.error(f"Password varification failed")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "Invalid email or password"}
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
    
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/user/login/swagger"
)
   
@router.post("/login/swagger")
async def swagger_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    email = form_data.username.lower().strip()
    password = form_data.password

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid credentials"})

    token = create_access_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer"
    }
    

@router.post("/verify-reset-token", status_code=200)
async def verify_reset_token(data: VerifyResetToken, db: AsyncSession = Depends(get_db)):
    """Verify if reset token is valid, exists, and not expired"""

    # Find user by token
    query = await db.execute(select(User).where(User.reset_token == data.token))
    user = query.scalar_one_or_none()

    # Token does not match any user
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "valid": False,
                "message": "Invalid token"
            }
        )

    # Token expired
    if user.reset_token_expires < datetime.utcnow():
        return JSONResponse(
            status_code=status.HTTP_410_GONE,  
            content={
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
    try:
        logger.info(f"forgot password request: {data.email}")
        
        user = await db.execute(select(User).where(User.email == data.email))
        user_data = user.scalar_one_or_none()
        
        if not user_data:
            logger.warning(f"Email not found: {data.email}")
            return JSONResponse(status_code=404, content={"success": False, "message": "Email not found"})

        token = generate_reset_token()
        user_data.reset_token = token
        user_data.reset_token_expires = datetime.utcnow() + timedelta(minutes=30)

        await db.commit()

        reset_link = f"{FRONTEND_URL}?token={token}"
        try:
            email_sent = await send_reset_email(user_data.email, reset_link)
            
            if not email_sent:
                logger.error(f"error sending email.. email not sent:")
                return JSONResponse(status_code=500, content={"success": False, "message": "Failed to send reset email. Please try again later."})
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to send reset email. Please try again later."})
        
        logger.info(f"Reset link sent successfully to {data.email}")
        return {"success": True, "message": "Password reset link sent to email"}
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return JSONResponse( status_code=500, content={"success": False, "message": "Failed to send reset email. Please try again later."})


@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    """ verify user's reset-password token and changed the user's password with new one """
    try:
        user = await db.execute(select(User).where(User.reset_token == data.token))
        user_data = user.scalar_one_or_none()
        
        if not user_data:
            return JSONResponse(status_code=400, content={"success": False, "message": "Invalid token or token Expire"})

        if not user_data.reset_token_expires or user_data.reset_token_expires < datetime.utcnow():
            return JSONResponse(status_code=400, content={"success": False, "message": "Token expired"})

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
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to reset password. Please try again later {str(e)}."}
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_access_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(data.refresh_token)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "Invalid or expired refresh token",}
        )

    user_id = payload.get("sub")

    if not user_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "Invalid token payload",}
        )

    result = await db.execute(
        select(User).where(User.id == int(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"success": False, "message":"User not found or inactive"})

    new_access_token = create_access_token(
        {"sub": str(user.id), "role": user.role}
    )

    new_refresh_token = create_refresh_token(
        {"sub": str(user.id), "role": user.role}
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
    
    
@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        if not verify_password(payload.current_password, current_user.hashed_password):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Current password is incorrect"}
            )

        if payload.new_password != payload.confirm_password:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "New password and confirm password do not match"}
            )

        if verify_password(payload.new_password, current_user.hashed_password):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "New password must be different from current password"}
            )

        current_user.hashed_password = hash_password(payload.new_password)
        await db.commit()

        return {
            "success": True,
            "message": "Password changed successfully"
        }

    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Something went wrong {str(e)}"}
        )