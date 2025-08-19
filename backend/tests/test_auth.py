import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.security import (
    create_access_token, 
    verify_token, 
    verify_password, 
    get_password_hash,
    create_password_reset_token,
    verify_password_reset_token
)
from app.services.auth import AuthService
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister, UserLogin

client = TestClient(app)


class TestSecurityFunctions:
    """Test security utility functions"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        
        # Verification should work
        assert verify_password(password, hashed) is True
        
        # Wrong password should fail
        assert verify_password("wrongpassword", hashed) is False
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        data = {"sub": "testuser", "user_id": "123", "role": "bartender"}
        token = create_access_token(data)
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == "123"
        assert payload["role"] == "bartender"
        assert "exp" in payload
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        data = {"sub": "testuser"}
        # Create token that expires in 1 second
        token = create_access_token(data, expires_delta=timedelta(seconds=1))
        
        # Token should be valid immediately
        payload = verify_token(token)
        assert payload is not None
        
        # Wait for token to expire (in real test, we'd mock time)
        # For now, just test with negative expiration
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        payload = verify_token(expired_token)
        assert payload is None
    
    def test_password_reset_token(self):
        """Test password reset token creation and verification"""
        email = "test@example.com"
        token = create_password_reset_token(email)
        
        # Verify token
        verified_email = verify_password_reset_token(token)
        assert verified_email == email
        
        # Invalid token should return None
        invalid_token = "invalid.token.here"
        verified_email = verify_password_reset_token(invalid_token)
        assert verified_email is None


class TestAuthService:
    """Test authentication service functions"""
    
    def test_create_user_success(self, db_session: Session):
        """Test successful user creation"""
        user_data = UserRegister(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.BARTENDER
        )
        
        user = AuthService.create_user(db_session, user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.BARTENDER
        assert user.is_active is True
        assert user.hashed_password != "password123"  # Should be hashed
    
    def test_create_user_duplicate_username(self, db_session: Session):
        """Test user creation with duplicate username"""
        user_data = UserRegister(
            username="testuser",
            email="test1@example.com",
            password="password123",
            full_name="Test User 1",
            role=UserRole.BARTENDER
        )
        
        # Create first user
        AuthService.create_user(db_session, user_data)
        
        # Try to create second user with same username
        user_data2 = UserRegister(
            username="testuser",  # Same username
            email="test2@example.com",
            password="password123",
            full_name="Test User 2",
            role=UserRole.BARTENDER
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            AuthService.create_user(db_session, user_data2)
    
    def test_create_user_duplicate_email(self, db_session: Session):
        """Test user creation with duplicate email"""
        user_data = UserRegister(
            username="testuser1",
            email="test@example.com",
            password="password123",
            full_name="Test User 1",
            role=UserRole.BARTENDER
        )
        
        # Create first user
        AuthService.create_user(db_session, user_data)
        
        # Try to create second user with same email
        user_data2 = UserRegister(
            username="testuser2",
            email="test@example.com",  # Same email
            password="password123",
            full_name="Test User 2",
            role=UserRole.BARTENDER
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            AuthService.create_user(db_session, user_data2)
    
    def test_authenticate_user_success(self, db_session: Session):
        """Test successful user authentication"""
        # Create user
        user_data = UserRegister(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.BARTENDER
        )
        created_user = AuthService.create_user(db_session, user_data)
        
        # Authenticate with username
        authenticated_user = AuthService.authenticate_user(db_session, "testuser", "password123")
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        
        # Authenticate with email
        authenticated_user = AuthService.authenticate_user(db_session, "test@example.com", "password123")
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
    
    def test_authenticate_user_wrong_password(self, db_session: Session):
        """Test authentication with wrong password"""
        # Create user
        user_data = UserRegister(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.BARTENDER
        )
        AuthService.create_user(db_session, user_data)
        
        # Try to authenticate with wrong password
        authenticated_user = AuthService.authenticate_user(db_session, "testuser", "wrongpassword")
        assert authenticated_user is None
    
    def test_authenticate_user_nonexistent(self, db_session: Session):
        """Test authentication with nonexistent user"""
        authenticated_user = AuthService.authenticate_user(db_session, "nonexistent", "password123")
        assert authenticated_user is None
    
    def test_authenticate_user_inactive(self, db_session: Session):
        """Test authentication with inactive user"""
        # Create user
        user_data = UserRegister(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.BARTENDER
        )
        user = AuthService.create_user(db_session, user_data)
        
        # Deactivate user
        user.is_active = False
        db_session.commit()
        
        # Try to authenticate
        authenticated_user = AuthService.authenticate_user(db_session, "testuser", "password123")
        assert authenticated_user is None
    
    def test_login_user_success(self, db_session: Session):
        """Test successful user login"""
        # Create user
        user_data = UserRegister(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.BARTENDER
        )
        AuthService.create_user(db_session, user_data)
        
        # Login
        login_data = UserLogin(username="testuser", password="password123")
        token = AuthService.login_user(db_session, login_data)
        
        assert token.access_token is not None
        assert token.token_type == "bearer"
        assert token.expires_in > 0
        assert token.user.username == "testuser"
        assert token.user.email == "test@example.com"
    
    def test_login_user_failure(self, db_session: Session):
        """Test failed user login"""
        login_data = UserLogin(username="nonexistent", password="password123")
        
        with pytest.raises(Exception):  # Should raise HTTPException
            AuthService.login_user(db_session, login_data)
    
    def test_password_reset_flow(self, db_session: Session):
        """Test complete password reset flow"""
        # Create user
        user_data = UserRegister(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.BARTENDER
        )
        user = AuthService.create_user(db_session, user_data)
        original_password_hash = user.hashed_password
        
        # Request password reset token
        token = AuthService.create_password_reset_token_for_email(db_session, "test@example.com")
        assert token is not None
        
        # Reset password
        success = AuthService.reset_password(db_session, token, "newpassword123")
        assert success is True
        
        # Verify password was changed
        db_session.refresh(user)
        assert user.hashed_password != original_password_hash
        
        # Verify old password doesn't work
        authenticated_user = AuthService.authenticate_user(db_session, "testuser", "password123")
        assert authenticated_user is None
        
        # Verify new password works
        authenticated_user = AuthService.authenticate_user(db_session, "testuser", "newpassword123")
        assert authenticated_user is not None
    
    def test_change_password_success(self, db_session: Session):
        """Test successful password change"""
        # Create user
        user_data = UserRegister(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.BARTENDER
        )
        user = AuthService.create_user(db_session, user_data)
        original_password_hash = user.hashed_password
        
        # Change password
        success = AuthService.change_password(db_session, user, "password123", "newpassword123")
        assert success is True
        
        # Verify password was changed
        db_session.refresh(user)
        assert user.hashed_password != original_password_hash
    
    def test_change_password_wrong_current(self, db_session: Session):
        """Test password change with wrong current password"""
        # Create user
        user_data = UserRegister(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role=UserRole.BARTENDER
        )
        user = AuthService.create_user(db_session, user_data)
        
        # Try to change password with wrong current password
        success = AuthService.change_password(db_session, user, "wrongpassword", "newpassword123")
        assert success is False


class TestAuthAPI:
    """Test authentication API endpoints"""
    
    def test_register_endpoint(self, client):
        """Test user registration endpoint"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "bartender"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["role"] == "bartender"
        assert data["is_active"] is True
        assert "id" in data
    
    def test_login_endpoint(self, client):
        """Test user login endpoint"""
        # First register a user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "bartender"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["username"] == "testuser"
    
    def test_get_current_user_endpoint(self, client):
        """Test get current user endpoint"""
        # Register and login to get token
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "bartender"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Get current user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_unauthorized_access(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 when no token provided
    
    def test_invalid_token_access(self, client):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401