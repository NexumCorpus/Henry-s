from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.notification import (
    NotificationType, NotificationChannel, NotificationPriority, NotificationStatus
)


class NotificationRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    notification_type: NotificationType
    location_id: Optional[UUID] = None
    item_category: Optional[str] = None
    conditions: Dict[str, Any] = Field(..., description="Rule conditions as JSON")
    channels: List[NotificationChannel] = Field(..., min_items=1)
    priority: NotificationPriority = NotificationPriority.MEDIUM
    is_active: bool = True
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

    @field_validator('conditions')
    @classmethod
    def validate_conditions(cls, v, info):
        """Validate conditions based on notification type"""
        notification_type = info.data.get('notification_type')
        
        if notification_type == NotificationType.LOW_STOCK:
            if 'stock_threshold' not in v:
                raise ValueError('LOW_STOCK notifications require stock_threshold in conditions')
            if not isinstance(v['stock_threshold'], (int, float)) or v['stock_threshold'] < 0:
                raise ValueError('stock_threshold must be a non-negative number')
        
        elif notification_type == NotificationType.EXPIRATION_WARNING:
            if 'days_until_expiration' not in v:
                raise ValueError('EXPIRATION_WARNING notifications require days_until_expiration in conditions')
            if not isinstance(v['days_until_expiration'], (int, float)) or v['days_until_expiration'] < 0:
                raise ValueError('days_until_expiration must be a non-negative number')
        
        return v


class NotificationRuleCreate(NotificationRuleBase):
    pass


class NotificationRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    channels: Optional[List[NotificationChannel]] = None
    priority: Optional[NotificationPriority] = None
    is_active: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")


class NotificationRuleResponse(NotificationRuleBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType
    priority: NotificationPriority
    item_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    data: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class NotificationCreate(NotificationBase):
    rule_id: UUID
    user_id: UUID


class NotificationResponse(NotificationBase):
    id: UUID
    rule_id: UUID
    user_id: UUID
    channels_sent: List[NotificationChannel] = []
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationDeliveryLogBase(BaseModel):
    channel: NotificationChannel
    status: NotificationStatus
    recipient: str
    external_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class NotificationDeliveryLogCreate(NotificationDeliveryLogBase):
    notification_id: UUID


class NotificationDeliveryLogUpdate(BaseModel):
    status: NotificationStatus
    external_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


class NotificationDeliveryLogResponse(NotificationDeliveryLogBase):
    id: UUID
    notification_id: UUID
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserNotificationPreferenceBase(BaseModel):
    phone_number: Optional[str] = Field(None, pattern=r"^\+?1?[0-9]{10,15}$")
    push_token: Optional[str] = None
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    in_app_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = Field("22:00", pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: str = Field("08:00", pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    type_preferences: Dict[str, bool] = {}


class UserNotificationPreferenceCreate(UserNotificationPreferenceBase):
    user_id: UUID


class UserNotificationPreferenceUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, pattern=r"^\+?1?[0-9]{10,15}$")
    push_token: Optional[str] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    type_preferences: Optional[Dict[str, bool]] = None


class UserNotificationPreferenceResponse(UserNotificationPreferenceBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationSummary(BaseModel):
    """Summary of notifications for dashboard display"""
    total_unread: int
    by_type: Dict[NotificationType, int]
    by_priority: Dict[NotificationPriority, int]
    recent_notifications: List[NotificationResponse]


class BulkNotificationCreate(BaseModel):
    """For creating notifications for multiple users"""
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    user_ids: List[UUID] = Field(..., min_items=1)
    channels: List[NotificationChannel] = Field(..., min_items=1)
    item_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    data: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class NotificationTestRequest(BaseModel):
    """For testing notification delivery"""
    channel: NotificationChannel
    recipient: str
    title: str = "Test Notification"
    message: str = "This is a test notification from Henry's SmartStock AI"