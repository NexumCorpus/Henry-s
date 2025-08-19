from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole
from app.schemas.auth import TokenData
from app.services.auth import AuthService

# Security scheme for JWT tokens
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        Current authenticated User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    # Extract username from token
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Get user from database
    user = AuthService.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get current active user (redundant check for clarity).
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current active User object
    """
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory to require specific user role.
    
    Args:
        required_role: Required user role
        
    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role.value} role"
            )
        return current_user
    
    return role_checker


def require_role_or_higher(minimum_role: UserRole):
    """
    Dependency factory to require minimum user role or higher.
    Role hierarchy: barback < bartender < manager < admin
    
    Args:
        minimum_role: Minimum required user role
        
    Returns:
        Dependency function that checks user role hierarchy
    """
    role_hierarchy = {
        UserRole.BARBACK: 1,
        UserRole.BARTENDER: 2,
        UserRole.MANAGER: 3,
        UserRole.ADMIN: 4
    }
    
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(minimum_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {minimum_role.value} role or higher"
            )
        return current_user
    
    return role_checker


async def get_current_user_websocket(token: str) -> Optional[User]:
    """Get current authenticated user from JWT token for WebSocket connections"""
    try:
        # Verify and decode token
        payload = verify_token(token)
        if not payload:
            return None
        
        # Get username from token
        username = payload.get("sub")
        if not username:
            return None
        
        # Get database session
        db = next(get_db())
        try:
            user = AuthService.get_user_by_username(db, username)
            if not user or not user.is_active:
                return None
            
            return user
        finally:
            db.close()
            
    except Exception as e:
        print(f"WebSocket authentication error: {e}")
        return None


# Common role dependencies
require_bartender = require_role_or_higher(UserRole.BARTENDER)
require_manager = require_role_or_higher(UserRole.MANAGER)
require_admin = require_role(UserRole.ADMIN)