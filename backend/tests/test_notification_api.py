import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import patch, AsyncMock

from app.main import app
from app.models.user import User, UserRole
from app.models.location import Location, LocationType
from app.models.inventory import InventoryItem, ItemCategory, UnitOfMeasure
from app.models.notification import (
    NotificationRule, Notification, UserNotificationPreference,
    NotificationType, NotificationChannel, NotificationPriority
)
from app.core.dependencies import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.BARTENDER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    user = User(
        id=uuid4(),
        username="adminuser",
        email="admin@example.com",
        hashed_password="hashed_password",
        full_name="Admin User",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_location(db_session):
    location = Location(
        id=uuid4(),
        name="Main Bar",
        type=LocationType.BAR
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location


@pytest.fixture
def test_notification_rule(db_session, test_user, test_location):
    rule = NotificationRule(
        id=uuid4(),
        name="Test Rule",
        description="Test description",
        notification_type=NotificationType.LOW_STOCK,
        user_id=test_user.id,
        location_id=test_location.id,
        conditions={"stock_threshold": 5},
        channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        priority=NotificationPriority.MEDIUM,
        is_active=True
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def test_notification(db_session, test_user, test_notification_rule):
    notification = Notification(
        id=uuid4(),
        rule_id=test_notification_rule.id,
        user_id=test_user.id,
        title="Test Notification",
        message="This is a test notification",
        notification_type=NotificationType.LOW_STOCK,
        priority=NotificationPriority.MEDIUM
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


class TestNotificationRulesAPI:
    
    def test_create_notification_rule(self, client, test_user, test_location):
        """Test creating a notification rule"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            rule_data = {
                "name": "New Test Rule",
                "description": "New test description",
                "notification_type": "low_stock",
                "location_id": str(test_location.id),
                "conditions": {"stock_threshold": 3},
                "channels": ["email", "in_app"],
                "priority": "high",
                "is_active": True
            }
            
            response = client.post("/api/v1/notifications/rules", json=rule_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Test Rule"
            assert data["notification_type"] == "low_stock"
            assert data["conditions"]["stock_threshold"] == 3
            assert data["priority"] == "high"
            
            # Clean up
            app.dependency_overrides.clear()

    def test_get_notification_rules(self, client, test_user, test_notification_rule):
        """Test getting notification rules"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.get("/api/v1/notifications/rules")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == str(test_notification_rule.id)
            assert data[0]["name"] == "Test Rule"
            
            # Clean up
            app.dependency_overrides.clear()

    def test_get_notification_rule_by_id(self, client, test_user, test_notification_rule):
        """Test getting a specific notification rule"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.get(f"/api/v1/notifications/rules/{test_notification_rule.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(test_notification_rule.id)
            assert data["name"] == "Test Rule"
            
            # Clean up
            app.dependency_overrides.clear()

    def test_get_notification_rule_not_found(self, client, test_user):
        """Test getting a non-existent notification rule"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            fake_id = uuid4()
            response = client.get(f"/api/v1/notifications/rules/{fake_id}")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
            
            # Clean up
            app.dependency_overrides.clear()

    def test_update_notification_rule(self, client, test_user, test_notification_rule):
        """Test updating a notification rule"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            update_data = {
                "name": "Updated Rule Name",
                "priority": "urgent",
                "conditions": {"stock_threshold": 2}
            }
            
            response = client.put(
                f"/api/v1/notifications/rules/{test_notification_rule.id}", 
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Rule Name"
            assert data["priority"] == "urgent"
            assert data["conditions"]["stock_threshold"] == 2
            
            # Clean up
            app.dependency_overrides.clear()

    def test_delete_notification_rule(self, client, test_user, test_notification_rule):
        """Test deleting a notification rule"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.delete(f"/api/v1/notifications/rules/{test_notification_rule.id}")
            
            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]
            
            # Clean up
            app.dependency_overrides.clear()


class TestNotificationsAPI:
    
    def test_get_notifications(self, client, test_user, test_notification):
        """Test getting user notifications"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.get("/api/v1/notifications/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == str(test_notification.id)
            assert data[0]["title"] == "Test Notification"
            
            # Clean up
            app.dependency_overrides.clear()

    def test_get_notifications_with_pagination(self, client, test_user, test_notification):
        """Test getting notifications with pagination"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.get("/api/v1/notifications/?limit=10&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 10
            
            # Clean up
            app.dependency_overrides.clear()

    def test_get_unread_notifications_only(self, client, test_user, test_notification):
        """Test getting only unread notifications"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.get("/api/v1/notifications/?unread_only=true")
            
            assert response.status_code == 200
            data = response.json()
            # All notifications should be unread by default
            assert len(data) >= 1
            
            # Clean up
            app.dependency_overrides.clear()

    def test_get_notification_summary(self, client, test_user, test_notification):
        """Test getting notification summary"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.get("/api/v1/notifications/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_unread" in data
            assert "by_type" in data
            assert "by_priority" in data
            assert "recent_notifications" in data
            
            # Clean up
            app.dependency_overrides.clear()

    def test_mark_notification_read(self, client, test_user, test_notification):
        """Test marking a notification as read"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.put(f"/api/v1/notifications/{test_notification.id}/read")
            
            assert response.status_code == 200
            assert "marked as read" in response.json()["message"]
            
            # Clean up
            app.dependency_overrides.clear()

    def test_create_bulk_notifications_as_admin(self, client, admin_user, test_user):
        """Test creating bulk notifications as admin"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: admin_user):
            app.dependency_overrides[get_current_user] = lambda: admin_user
            
            bulk_data = {
                "title": "System Maintenance",
                "message": "System will be down for maintenance",
                "notification_type": "system_alert",
                "priority": "high",
                "user_ids": [str(test_user.id), str(admin_user.id)],
                "channels": ["email", "in_app"]
            }
            
            response = client.post("/api/v1/notifications/bulk", json=bulk_data)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2  # Two notifications created
            
            # Clean up
            app.dependency_overrides.clear()

    def test_create_bulk_notifications_forbidden_for_non_admin(self, client, test_user):
        """Test that non-admin users cannot create bulk notifications"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            bulk_data = {
                "title": "Test Bulk",
                "message": "Test bulk message",
                "notification_type": "system_alert",
                "priority": "medium",
                "user_ids": [str(test_user.id)],
                "channels": ["email"]
            }
            
            response = client.post("/api/v1/notifications/bulk", json=bulk_data)
            
            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]
            
            # Clean up
            app.dependency_overrides.clear()


class TestNotificationPreferencesAPI:
    
    def test_get_notification_preferences_creates_default(self, client, test_user):
        """Test getting notification preferences creates default if none exist"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.get("/api/v1/notifications/preferences")
            
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == str(test_user.id)
            assert data["email_enabled"] is True
            assert data["sms_enabled"] is False
            assert data["push_enabled"] is True
            assert data["in_app_enabled"] is True
            
            # Clean up
            app.dependency_overrides.clear()

    def test_update_notification_preferences(self, client, test_user):
        """Test updating notification preferences"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            update_data = {
                "phone_number": "+1234567890",
                "sms_enabled": True,
                "quiet_hours_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
                "type_preferences": {
                    "low_stock_email": True,
                    "low_stock_sms": False
                }
            }
            
            response = client.put("/api/v1/notifications/preferences", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["phone_number"] == "+1234567890"
            assert data["sms_enabled"] is True
            assert data["quiet_hours_enabled"] is True
            assert data["type_preferences"]["low_stock_email"] is True
            
            # Clean up
            app.dependency_overrides.clear()

    def test_update_notification_preferences_invalid_phone(self, client, test_user):
        """Test updating preferences with invalid phone number"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            update_data = {
                "phone_number": "invalid-phone"
            }
            
            response = client.put("/api/v1/notifications/preferences", json=update_data)
            
            assert response.status_code == 422  # Validation error
            
            # Clean up
            app.dependency_overrides.clear()


class TestNotificationSystemAPI:
    
    def test_trigger_stock_alerts_check_as_admin(self, client, admin_user):
        """Test triggering stock alerts check as admin"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: admin_user):
            app.dependency_overrides[get_current_user] = lambda: admin_user
            
            response = client.post("/api/v1/notifications/check/stock-alerts")
            
            assert response.status_code == 200
            assert "Stock alerts check triggered" in response.json()["message"]
            
            # Clean up
            app.dependency_overrides.clear()

    def test_trigger_stock_alerts_check_forbidden_for_non_admin(self, client, test_user):
        """Test that non-admin users cannot trigger system checks"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            response = client.post("/api/v1/notifications/check/stock-alerts")
            
            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]
            
            # Clean up
            app.dependency_overrides.clear()

    def test_trigger_expiration_alerts_check_as_admin(self, client, admin_user):
        """Test triggering expiration alerts check as admin"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: admin_user):
            app.dependency_overrides[get_current_user] = lambda: admin_user
            
            response = client.post("/api/v1/notifications/check/expiration-alerts")
            
            assert response.status_code == 200
            assert "Expiration alerts check triggered" in response.json()["message"]
            
            # Clean up
            app.dependency_overrides.clear()

    def test_test_notification_delivery_as_admin(self, client, admin_user):
        """Test notification delivery testing as admin"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: admin_user):
            app.dependency_overrides[get_current_user] = lambda: admin_user
            
            test_data = {
                "channel": "email",
                "recipient": "test@example.com",
                "title": "Test Notification",
                "message": "This is a test"
            }
            
            response = client.post("/api/v1/notifications/test", json=test_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "Test notification created" in data["message"]
            assert "notification_id" in data
            
            # Clean up
            app.dependency_overrides.clear()

    def test_webhook_endpoints_exist(self, client):
        """Test that webhook endpoints exist and return success"""
        # Test Twilio webhook
        response = client.post("/api/v1/notifications/webhooks/twilio")
        assert response.status_code == 200
        assert response.json()["status"] == "received"
        
        # Test SendGrid webhook
        response = client.post("/api/v1/notifications/webhooks/sendgrid")
        assert response.status_code == 200
        assert response.json()["status"] == "received"


class TestNotificationValidation:
    
    def test_create_rule_with_invalid_conditions(self, client, test_user):
        """Test creating rule with invalid conditions for notification type"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            # LOW_STOCK notification without stock_threshold
            rule_data = {
                "name": "Invalid Rule",
                "notification_type": "low_stock",
                "conditions": {},  # Missing stock_threshold
                "channels": ["email"],
                "priority": "medium"
            }
            
            response = client.post("/api/v1/notifications/rules", json=rule_data)
            
            assert response.status_code == 422  # Validation error
            
            # Clean up
            app.dependency_overrides.clear()

    def test_create_rule_with_invalid_quiet_hours(self, client, test_user):
        """Test creating rule with invalid quiet hours format"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            rule_data = {
                "name": "Invalid Hours Rule",
                "notification_type": "low_stock",
                "conditions": {"stock_threshold": 5},
                "channels": ["email"],
                "priority": "medium",
                "quiet_hours_start": "25:00"  # Invalid time format
            }
            
            response = client.post("/api/v1/notifications/rules", json=rule_data)
            
            assert response.status_code == 422  # Validation error
            
            # Clean up
            app.dependency_overrides.clear()

    def test_create_rule_with_empty_channels(self, client, test_user):
        """Test creating rule with empty channels list"""
        with patch.object(app.dependency_overrides, 'get', return_value=lambda: test_user):
            app.dependency_overrides[get_current_user] = lambda: test_user
            
            rule_data = {
                "name": "No Channels Rule",
                "notification_type": "low_stock",
                "conditions": {"stock_threshold": 5},
                "channels": [],  # Empty channels
                "priority": "medium"
            }
            
            response = client.post("/api/v1/notifications/rules", json=rule_data)
            
            assert response.status_code == 422  # Validation error
            
            # Clean up
            app.dependency_overrides.clear()