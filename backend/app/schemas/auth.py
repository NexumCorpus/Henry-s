from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from app.models.user import UserRole


class UserLogin(BaseModel):
    """Schema for user login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
    """Schema for user registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.BARBACK


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        if hasattr(v, '__str__'):
            return str(v)
        return v


class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token payload data"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[UserRole] = None


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset with token"""
    token: str
    new_password: str = Field(..., min_length=6)


class PasswordChange(BaseModel):
    """Schema for password change (authenticated user)"""
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None