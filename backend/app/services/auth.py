from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token
)
from app.core.config import settings


class AuthService:
    """Service class for authentication operations"""
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.
        
        Args:
            db: Database session
            username: Username or email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Try to find user by username or email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
            
        if not user.is_active:
            return None
            
        return user
    
    @staticmethod
    def create_user(db: Session, user_data: UserRegister) -> User:
        """
        Create a new user account.
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Created User object
            
        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username already exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> Token:
        """
        Login a user and return access token.
        
        Args:
            db: Database session
            login_data: Login credentials
            
        Returns:
            Token object with access token and user info
            
        Raises:
            HTTPException: If authentication fails
        """
        user = AuthService.authenticate_user(db, login_data.username, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": str(user.id),
                "role": user.role.value
            },
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def create_password_reset_token_for_email(db: Session, email: str) -> Optional[str]:
        """
        Create password reset token for user email.
        
        Args:
            db: Database session
            email: User email address
            
        Returns:
            Reset token if user exists, None otherwise
        """
        user = AuthService.get_user_by_email(db, email)
        if not user or not user.is_active:
            return None
        
        return create_password_reset_token(email)
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """
        Reset user password using reset token.
        
        Args:
            db: Database session
            token: Password reset token
            new_password: New password
            
        Returns:
            True if password reset successful, False otherwise
        """
        email = verify_password_reset_token(token)
        if not email:
            return False
        
        user = AuthService.get_user_by_email(db, email)
        if not user or not user.is_active:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        return True
    
    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
        """
        Change user password (requires current password verification).
        
        Args:
            db: Database session
            user: User object
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully, False otherwise
        """
        if not verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        return True