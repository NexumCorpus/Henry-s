import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.dependencies import (
    get_current_user, 
    require_role, 
    require_role_or_higher,
    require_bartender,
    require_manager,
    require_admin
)
from app.models.user import User, UserRole
from app.services.auth import AuthService
from app.schemas.auth import UserRegister

client = TestClient(app)


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def create_user_with_role(self, db_session: Session, client, username: str, role: UserRole) -> tuple[User, str]:
        """Helper method to create user and return user object and token"""
        user_data = UserRegister(
            username=username,
            email=f"{username}@example.com",
            password="password123",
            full_name=f"Test {username}",
            role=role
        )
        user = AuthService.create_user(db_session, user_data)
        
        # Get token by logging in
        login_response = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        return user, token
    
    def test_role_hierarchy(self, db_session: Session, client):
        """Test role hierarchy enforcement"""
        # Create users with different roles
        barback_user, barback_token = self.create_user_with_role(db_session, client, "barback", UserRole.BARBACK)
        bartender_user, bartender_token = self.create_user_with_role(db_session, client, "bartender", UserRole.BARTENDER)
        manager_user, manager_token = self.create_user_with_role(db_session, client, "manager", UserRole.MANAGER)
        admin_user, admin_token = self.create_user_with_role(db_session, client, "admin", UserRole.ADMIN)
        
        # Test admin-only endpoint (list users)
        # Only admin should succeed
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/auth/users", headers=headers_admin)
        assert response.status_code == 200
        
        # Manager should fail
        headers_manager = {"Authorization": f"Bearer {manager_token}"}
        response = client.get("/api/v1/auth/users", headers=headers_manager)
        assert response.status_code == 403
        
        # Bartender should fail
        headers_bartender = {"Authorization": f"Bearer {bartender_token}"}
        response = client.get("/api/v1/auth/users", headers=headers_bartender)
        assert response.status_code == 403
        
        # Barback should fail
        headers_barback = {"Authorization": f"Bearer {barback_token}"}
        response = client.get("/api/v1/auth/users", headers=headers_barback)
        assert response.status_code == 403
    
    def test_user_update_admin_only(self, db_session: Session, client):
        """Test that only admins can update users"""
        # Create admin and regular user
        admin_user, admin_token = self.create_user_with_role(db_session, client, "admin", UserRole.ADMIN)
        regular_user, regular_token = self.create_user_with_role(db_session, client, "regular", UserRole.BARTENDER)
        
        update_data = {
            "full_name": "Updated Name",
            "role": "manager"
        }
        
        # Admin should be able to update
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        response = client.put(f"/api/v1/auth/users/{regular_user.id}", 
                            json=update_data, headers=headers_admin)
        assert response.status_code == 200
        
        # Regular user should not be able to update others
        headers_regular = {"Authorization": f"Bearer {regular_token}"}
        response = client.put(f"/api/v1/auth/users/{admin_user.id}", 
                            json=update_data, headers=headers_regular)
        assert response.status_code == 403
    
    def test_get_specific_user_admin_only(self, db_session: Session, client):
        """Test that only admins can get specific user details"""
        # Create admin and regular user
        admin_user, admin_token = self.create_user_with_role(db_session, client, "admin", UserRole.ADMIN)
        regular_user, regular_token = self.create_user_with_role(db_session, client, "regular", UserRole.BARTENDER)
        
        # Admin should be able to get user details
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"/api/v1/auth/users/{regular_user.id}", headers=headers_admin)
        assert response.status_code == 200
        
        # Regular user should not be able to get other user details
        headers_regular = {"Authorization": f"Bearer {regular_token}"}
        response = client.get(f"/api/v1/auth/users/{admin_user.id}", headers=headers_regular)
        assert response.status_code == 403
    
    def test_password_reset_request_public(self, client):
        """Test that password reset request is publicly accessible"""
        # This endpoint should be accessible without authentication
        response = client.post("/api/v1/auth/password-reset-request", json={
            "email": "test@example.com"
        })
        # Should return 200 regardless of whether email exists (security)
        assert response.status_code == 200
    
    def test_password_reset_public(self, client):
        """Test that password reset is publicly accessible"""
        # This endpoint should be accessible without authentication
        response = client.post("/api/v1/auth/password-reset", json={
            "token": "invalid.token.here",
            "new_password": "newpassword123"
        })
        # Should return 400 for invalid token, not 401 for unauthorized
        assert response.status_code == 400
    
    def test_change_password_requires_auth(self, db_session: Session, client):
        """Test that password change requires authentication"""
        # Create user
        user, token = self.create_user_with_role(db_session, client, "testuser", UserRole.BARTENDER)
        
        password_data = {
            "current_password": "password123",
            "new_password": "newpassword123"
        }
        
        # Should work with valid token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=headers)
        assert response.status_code == 200
        
        # Should fail without token
        response = client.post("/api/v1/auth/change-password", json=password_data)
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 when no token provided
    
    def test_get_current_user_requires_auth(self, db_session: Session, client):
        """Test that getting current user requires authentication"""
        # Create user
        user, token = self.create_user_with_role(db_session, client, "testuser", UserRole.BARTENDER)
        
        # Should work with valid token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"
        
        # Should fail without token
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 when no token provided
        
        # Should fail with invalid token
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestRoleDependencies:
    """Test role dependency functions directly"""
    
    def test_require_role_function(self):
        """Test require_role dependency factory"""
        # Create a role checker for manager role
        manager_checker = require_role(UserRole.MANAGER)
        
        # Create mock users
        manager_user = User(
            username="manager",
            email="manager@example.com",
            hashed_password="hashed",
            full_name="Manager User",
            role=UserRole.MANAGER,
            is_active=True
        )
        
        bartender_user = User(
            username="bartender",
            email="bartender@example.com",
            hashed_password="hashed",
            full_name="Bartender User",
            role=UserRole.BARTENDER,
            is_active=True
        )
        
        # Manager should pass
        result = manager_checker(manager_user)
        assert result == manager_user
        
        # Bartender should fail
        with pytest.raises(Exception):  # Should raise HTTPException
            manager_checker(bartender_user)
    
    def test_require_role_or_higher_function(self):
        """Test require_role_or_higher dependency factory"""
        # Create a role checker for bartender or higher
        bartender_or_higher = require_role_or_higher(UserRole.BARTENDER)
        
        # Create mock users
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        manager_user = User(
            username="manager",
            email="manager@example.com",
            hashed_password="hashed",
            full_name="Manager User",
            role=UserRole.MANAGER,
            is_active=True
        )
        
        bartender_user = User(
            username="bartender",
            email="bartender@example.com",
            hashed_password="hashed",
            full_name="Bartender User",
            role=UserRole.BARTENDER,
            is_active=True
        )
        
        barback_user = User(
            username="barback",
            email="barback@example.com",
            hashed_password="hashed",
            full_name="Barback User",
            role=UserRole.BARBACK,
            is_active=True
        )
        
        # Admin should pass
        result = bartender_or_higher(admin_user)
        assert result == admin_user
        
        # Manager should pass
        result = bartender_or_higher(manager_user)
        assert result == manager_user
        
        # Bartender should pass
        result = bartender_or_higher(bartender_user)
        assert result == bartender_user
        
        # Barback should fail
        with pytest.raises(Exception):  # Should raise HTTPException
            bartender_or_higher(barback_user)