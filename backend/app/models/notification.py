from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class NotificationType(str, enum.Enum):
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRATION_WARNING = "expiration_warning"
    SYSTEM_ALERT = "system_alert"
    ORDER_CONFIRMATION = "order_confirmation"
    WASTE_ALERT = "waste_alert"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), index=True)  # Optional location filter
    item_category = Column(String(50), index=True)  # Optional category filter
    
    # Rule conditions (stored as JSON for flexibility)
    conditions = Column(JSON, nullable=False)  # e.g., {"stock_threshold": 5, "days_until_expiration": 3}
    
    # Notification preferences
    channels = Column(JSON, nullable=False)  # List of channels: ["email", "sms", "push"]
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    
    # Schedule settings
    is_active = Column(Boolean, default=True, nullable=False)
    quiet_hours_start = Column(String(5))  # "22:00" format
    quiet_hours_end = Column(String(5))    # "08:00" format
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notification_rules")
    location = relationship("Location", back_populates="notification_rules")
    notifications = relationship("Notification", back_populates="rule")

    def __repr__(self):
        return f"<NotificationRule(id={self.id}, name='{self.name}', type='{self.notification_type}')>"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("notification_rules.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    priority = Column(Enum(NotificationPriority), nullable=False)
    
    # Related entities
    item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), index=True)
    
    # Metadata
    data = Column(JSON)  # Additional context data
    
    # Delivery tracking
    channels_sent = Column(JSON, default=list)  # List of channels where notification was sent
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration for time-sensitive alerts

    # Relationships
    rule = relationship("NotificationRule", back_populates="notifications")
    user = relationship("User", back_populates="notifications")
    item = relationship("InventoryItem", back_populates="notifications")
    location = relationship("Location", back_populates="notifications")
    delivery_logs = relationship("NotificationDeliveryLog", back_populates="notification", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.notification_type}', user_id={self.user_id})>"


class NotificationDeliveryLog(Base):
    __tablename__ = "notification_delivery_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=False, index=True)
    channel = Column(Enum(NotificationChannel), nullable=False)
    status = Column(Enum(NotificationStatus), nullable=False, index=True)
    
    # Delivery details
    recipient = Column(String(255), nullable=False)  # email address, phone number, device token
    external_id = Column(String(255))  # ID from external service (Twilio, SendGrid, etc.)
    
    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    notification = relationship("Notification", back_populates="delivery_logs")

    def __repr__(self):
        return f"<NotificationDeliveryLog(id={self.id}, channel='{self.channel}', status='{self.status}')>"


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Contact information
    phone_number = Column(String(20))
    push_token = Column(String(255))  # For mobile push notifications
    
    # Global preferences
    email_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(5), default="22:00")
    quiet_hours_end = Column(String(5), default="08:00")
    
    # Notification type preferences (JSON object with type -> enabled mapping)
    type_preferences = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self):
        return f"<UserNotificationPreference(id={self.id}, user_id={self.user_id})>"