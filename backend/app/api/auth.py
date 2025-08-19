from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.schemas.auth import (
    UserLogin, 
    UserRegister, 
    Token, 
    UserResponse,
    PasswordResetRequest,
    PasswordReset,
    PasswordChange,
    UserUpdate
)
from app.services.auth import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    - **full_name**: User's full name
    - **role**: User role (barback, bartender, manager, admin)
    """
    user = AuthService.create_user(db, user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with username/email and password.
    
    Returns JWT access token and user information.
    
    - **username**: Username or email address
    - **password**: User password
    """
    return AuthService.login_user(db, login_data)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse.model_validate(current_user)


@router.post("/password-reset-request")
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset token for email address.
    
    Sends password reset token (in production, this would be emailed).
    Returns success message regardless of whether email exists (security).
    """
    token = AuthService.create_password_reset_token_for_email(db, request_data.email)
    
    # In production, send email with reset link containing the token
    # For now, we'll return the token directly (development only)
    if token:
        return {
            "message": "Password reset token generated",
            "token": token  # Remove this in production
        }
    
    return {"message": "If the email exists, a password reset token has been sent"}


@router.post("/password-reset")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password (minimum 6 characters)
    """
    success = AuthService.reset_password(db, reset_data.token, reset_data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.
    
    Requires current password verification.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 6 characters)
    """
    success = AuthService.change_password(
        db, 
        current_user, 
        password_data.current_password, 
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user information (admin only).
    
    - **user_id**: UUID of user to update
    - **full_name**: Updated full name (optional)
    - **email**: Updated email address (optional)
    - **role**: Updated user role (optional)
    - **is_active**: Updated active status (optional)
    """
    # Get user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    if user_update.email is not None:
        # Check if email already exists for another user
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_update.email
    
    if user_update.role is not None:
        user.role = user_update.role
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all users (admin only).
    
    Returns list of all users with their information.
    """
    users = db.query(User).all()
    return [UserResponse.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get specific user information (admin only).
    
    - **user_id**: UUID of user to retrieve
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)