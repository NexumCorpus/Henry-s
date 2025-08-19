import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.models.notification import (
    NotificationRule, Notification, NotificationDeliveryLog, UserNotificationPreference,
    NotificationType, NotificationChannel, NotificationPriority, NotificationStatus
)
from app.models.user import User
from app.models.inventory import InventoryItem, StockLevel
from app.models.location import Location
from app.schemas.notification import (
    NotificationCreate, NotificationDeliveryLogCreate, BulkNotificationCreate
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.twilio_client = None
        self.sendgrid_client = None
        
        # Initialize external service clients if credentials are available
        if hasattr(settings, 'TWILIO_ACCOUNT_SID') and hasattr(settings, 'TWILIO_AUTH_TOKEN'):
            self.twilio_client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        if hasattr(settings, 'SENDGRID_API_KEY'):
            self.sendgrid_client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

    async def create_notification_rule(
        self, 
        db: Session, 
        user_id: UUID, 
        rule_data: dict
    ) -> NotificationRule:
        """Create a new notification rule"""
        rule = NotificationRule(
            user_id=user_id,
            **rule_data
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    async def update_notification_rule(
        self, 
        db: Session, 
        rule_id: UUID, 
        user_id: UUID, 
        update_data: dict
    ) -> Optional[NotificationRule]:
        """Update an existing notification rule"""
        rule = db.query(NotificationRule).filter(
            and_(NotificationRule.id == rule_id, NotificationRule.user_id == user_id)
        ).first()
        
        if not rule:
            return None
        
        for field, value in update_data.items():
            if value is not None:
                setattr(rule, field, value)
        
        db.commit()
        db.refresh(rule)
        return rule

    async def delete_notification_rule(
        self, 
        db: Session, 
        rule_id: UUID, 
        user_id: UUID
    ) -> bool:
        """Delete a notification rule"""
        rule = db.query(NotificationRule).filter(
            and_(NotificationRule.id == rule_id, NotificationRule.user_id == user_id)
        ).first()
        
        if not rule:
            return False
        
        db.delete(rule)
        db.commit()
        return True

    async def get_user_notification_rules(
        self, 
        db: Session, 
        user_id: UUID
    ) -> List[NotificationRule]:
        """Get all notification rules for a user"""
        return db.query(NotificationRule).filter(
            NotificationRule.user_id == user_id
        ).all()

    async def create_notification(
        self, 
        db: Session, 
        notification_data: NotificationCreate
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(**notification_data.dict())
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Trigger delivery asynchronously
        asyncio.create_task(self._deliver_notification(db, notification))
        
        return notification

    async def create_bulk_notifications(
        self, 
        db: Session, 
        bulk_data: BulkNotificationCreate
    ) -> List[Notification]:
        """Create notifications for multiple users"""
        notifications = []
        
        for user_id in bulk_data.user_ids:
            notification_data = NotificationCreate(
                rule_id=None,  # Bulk notifications don't have specific rules
                user_id=user_id,
                title=bulk_data.title,
                message=bulk_data.message,
                notification_type=bulk_data.notification_type,
                priority=bulk_data.priority,
                item_id=bulk_data.item_id,
                location_id=bulk_data.location_id,
                data=bulk_data.data,
                expires_at=bulk_data.expires_at
            )
            
            notification = await self.create_notification(db, notification_data)
            notifications.append(notification)
        
        return notifications

    async def check_stock_alerts(self, db: Session):
        """Check for stock level alerts and create notifications"""
        # Get all active low stock rules
        low_stock_rules = db.query(NotificationRule).filter(
            and_(
                NotificationRule.notification_type == NotificationType.LOW_STOCK,
                NotificationRule.is_active == True
            )
        ).all()
        
        for rule in low_stock_rules:
            await self._check_low_stock_rule(db, rule)
        
        # Check for out of stock items
        out_of_stock_rules = db.query(NotificationRule).filter(
            and_(
                NotificationRule.notification_type == NotificationType.OUT_OF_STOCK,
                NotificationRule.is_active == True
            )
        ).all()
        
        for rule in out_of_stock_rules:
            await self._check_out_of_stock_rule(db, rule)

    async def check_expiration_alerts(self, db: Session):
        """Check for expiration alerts and create notifications"""
        expiration_rules = db.query(NotificationRule).filter(
            and_(
                NotificationRule.notification_type == NotificationType.EXPIRATION_WARNING,
                NotificationRule.is_active == True
            )
        ).all()
        
        for rule in expiration_rules:
            await self._check_expiration_rule(db, rule)

    async def _check_low_stock_rule(self, db: Session, rule: NotificationRule):
        """Check a specific low stock rule"""
        threshold = rule.conditions.get('stock_threshold', 0)
        
        # Build query based on rule filters
        query = db.query(StockLevel).join(InventoryItem)
        
        if rule.location_id:
            query = query.filter(StockLevel.location_id == rule.location_id)
        
        if rule.item_category:
            query = query.filter(InventoryItem.category == rule.item_category)
        
        # Find items below threshold
        low_stock_items = query.filter(
            StockLevel.current_stock <= threshold
        ).all()
        
        for stock_level in low_stock_items:
            # Check if we already sent a notification recently (avoid spam)
            recent_notification = db.query(Notification).filter(
                and_(
                    Notification.user_id == rule.user_id,
                    Notification.item_id == stock_level.item_id,
                    Notification.location_id == stock_level.location_id,
                    Notification.notification_type == NotificationType.LOW_STOCK,
                    Notification.created_at > datetime.utcnow() - timedelta(hours=24)
                )
            ).first()
            
            if not recent_notification:
                await self._create_stock_alert_notification(
                    db, rule, stock_level, NotificationType.LOW_STOCK
                )

    async def _check_out_of_stock_rule(self, db: Session, rule: NotificationRule):
        """Check a specific out of stock rule"""
        # Similar to low stock but for zero stock
        query = db.query(StockLevel).join(InventoryItem)
        
        if rule.location_id:
            query = query.filter(StockLevel.location_id == rule.location_id)
        
        if rule.item_category:
            query = query.filter(InventoryItem.category == rule.item_category)
        
        out_of_stock_items = query.filter(StockLevel.current_stock <= 0).all()
        
        for stock_level in out_of_stock_items:
            recent_notification = db.query(Notification).filter(
                and_(
                    Notification.user_id == rule.user_id,
                    Notification.item_id == stock_level.item_id,
                    Notification.location_id == stock_level.location_id,
                    Notification.notification_type == NotificationType.OUT_OF_STOCK,
                    Notification.created_at > datetime.utcnow() - timedelta(hours=12)
                )
            ).first()
            
            if not recent_notification:
                await self._create_stock_alert_notification(
                    db, rule, stock_level, NotificationType.OUT_OF_STOCK
                )

    async def _check_expiration_rule(self, db: Session, rule: NotificationRule):
        """Check for items approaching expiration"""
        days_threshold = rule.conditions.get('days_until_expiration', 7)
        expiration_date = datetime.utcnow() + timedelta(days=days_threshold)
        
        # This would require tracking expiration dates per stock item
        # For now, we'll use the item's expiration_days field as a proxy
        query = db.query(InventoryItem).filter(
            InventoryItem.expiration_days.isnot(None)
        )
        
        if rule.item_category:
            query = query.filter(InventoryItem.category == rule.item_category)
        
        # This is a simplified check - in a real system, you'd track individual batch expiration dates
        items = query.all()
        
        for item in items:
            if item.expiration_days and item.expiration_days <= days_threshold:
                await self._create_expiration_notification(db, rule, item)

    async def _create_stock_alert_notification(
        self, 
        db: Session, 
        rule: NotificationRule, 
        stock_level: StockLevel, 
        notification_type: NotificationType
    ):
        """Create a stock alert notification"""
        item_name = stock_level.item.name
        location_name = stock_level.location.name
        current_stock = stock_level.current_stock
        
        if notification_type == NotificationType.LOW_STOCK:
            title = f"Low Stock Alert: {item_name}"
            message = f"{item_name} is running low at {location_name}. Current stock: {current_stock}"
        else:  # OUT_OF_STOCK
            title = f"Out of Stock: {item_name}"
            message = f"{item_name} is out of stock at {location_name}. Immediate restocking needed."
        
        notification_data = NotificationCreate(
            rule_id=rule.id,
            user_id=rule.user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=rule.priority,
            item_id=stock_level.item_id,
            location_id=stock_level.location_id,
            data={
                "current_stock": current_stock,
                "threshold": rule.conditions.get('stock_threshold', 0)
            }
        )
        
        await self.create_notification(db, notification_data)

    async def _create_expiration_notification(
        self, 
        db: Session, 
        rule: NotificationRule, 
        item: InventoryItem
    ):
        """Create an expiration warning notification"""
        title = f"Expiration Warning: {item.name}"
        message = f"{item.name} will expire in {item.expiration_days} days. Consider using soon."
        
        notification_data = NotificationCreate(
            rule_id=rule.id,
            user_id=rule.user_id,
            title=title,
            message=message,
            notification_type=NotificationType.EXPIRATION_WARNING,
            priority=rule.priority,
            item_id=item.id,
            data={"days_until_expiration": item.expiration_days}
        )
        
        await self.create_notification(db, notification_data)

    async def _deliver_notification(self, db: Session, notification: Notification):
        """Deliver notification through configured channels"""
        # Get user preferences
        user_prefs = db.query(UserNotificationPreference).filter(
            UserNotificationPreference.user_id == notification.user_id
        ).first()
        
        if not user_prefs:
            # Create default preferences if none exist
            user_prefs = UserNotificationPreference(user_id=notification.user_id)
            db.add(user_prefs)
            db.commit()
        
        # Check if we're in quiet hours
        if self._is_quiet_hours(user_prefs) and notification.priority != NotificationPriority.URGENT:
            logger.info(f"Skipping notification {notification.id} due to quiet hours")
            return
        
        # Get user's email from User model
        user = db.query(User).filter(User.id == notification.user_id).first()
        if not user:
            logger.error(f"User {notification.user_id} not found for notification {notification.id}")
            return
        
        # Determine which channels to use based on rule and user preferences
        rule = db.query(NotificationRule).filter(NotificationRule.id == notification.rule_id).first()
        channels_to_use = []
        
        if rule and rule.channels:
            for channel in rule.channels:
                # Convert string to enum if needed
                if isinstance(channel, str):
                    channel = NotificationChannel(channel)
                if self._is_channel_enabled(channel, user_prefs, notification.notification_type):
                    channels_to_use.append(channel)
        
        # Deliver through each channel
        for channel in channels_to_use:
            try:
                if channel == NotificationChannel.EMAIL and user_prefs.email_enabled:
                    await self._send_email(db, notification, user.email)
                elif channel == NotificationChannel.SMS and user_prefs.sms_enabled and user_prefs.phone_number:
                    await self._send_sms(db, notification, user_prefs.phone_number)
                elif channel == NotificationChannel.PUSH and user_prefs.push_enabled and user_prefs.push_token:
                    await self._send_push(db, notification, user_prefs.push_token)
                elif channel == NotificationChannel.IN_APP:
                    await self._create_in_app_notification(db, notification)
                    
            except Exception as e:
                logger.error(f"Failed to deliver notification {notification.id} via {channel}: {str(e)}")

    def _is_quiet_hours(self, user_prefs: UserNotificationPreference) -> bool:
        """Check if current time is within user's quiet hours"""
        if not user_prefs.quiet_hours_enabled:
            return False
        
        now = datetime.utcnow().time()
        start_time = time.fromisoformat(user_prefs.quiet_hours_start)
        end_time = time.fromisoformat(user_prefs.quiet_hours_end)
        
        if start_time <= end_time:
            return start_time <= now <= end_time
        else:  # Quiet hours span midnight
            return now >= start_time or now <= end_time

    def _is_channel_enabled(
        self, 
        channel: NotificationChannel, 
        user_prefs: UserNotificationPreference, 
        notification_type: NotificationType
    ) -> bool:
        """Check if a channel is enabled for the user and notification type"""
        # Check global channel preference
        if channel == NotificationChannel.EMAIL and not user_prefs.email_enabled:
            return False
        elif channel == NotificationChannel.SMS and not user_prefs.sms_enabled:
            return False
        elif channel == NotificationChannel.PUSH and not user_prefs.push_enabled:
            return False
        elif channel == NotificationChannel.IN_APP and not user_prefs.in_app_enabled:
            return False
        
        # Check type-specific preferences
        type_prefs = user_prefs.type_preferences or {}
        type_key = f"{notification_type.value}_{channel.value}"
        
        return type_prefs.get(type_key, True)  # Default to enabled

    async def _send_email(self, db: Session, notification: Notification, email: str):
        """Send email notification"""
        if not self.sendgrid_client:
            logger.warning("SendGrid client not configured, skipping email notification")
            return
        
        try:
            message = Mail(
                from_email=getattr(settings, 'FROM_EMAIL', 'noreply@henrysonmarket.com'),
                to_emails=email,
                subject=notification.title,
                html_content=self._generate_email_template(notification)
            )
            
            response = self.sendgrid_client.send(message)
            
            # Log delivery attempt
            delivery_log = NotificationDeliveryLog(
                notification_id=notification.id,
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.SENT,
                recipient=email,
                external_id=response.headers.get('X-Message-Id'),
                sent_at=datetime.utcnow()
            )
            db.add(delivery_log)
            db.commit()
            
            logger.info(f"Email sent for notification {notification.id} to {email}")
            
        except Exception as e:
            # Log failure
            delivery_log = NotificationDeliveryLog(
                notification_id=notification.id,
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.FAILED,
                recipient=email,
                error_message=str(e),
                failed_at=datetime.utcnow()
            )
            db.add(delivery_log)
            db.commit()
            
            logger.error(f"Failed to send email for notification {notification.id}: {str(e)}")

    async def _send_sms(self, db: Session, notification: Notification, phone_number: str):
        """Send SMS notification"""
        if not self.twilio_client:
            logger.warning("Twilio client not configured, skipping SMS notification")
            return
        
        try:
            message = self.twilio_client.messages.create(
                body=f"{notification.title}\n\n{notification.message}",
                from_=getattr(settings, 'TWILIO_PHONE_NUMBER', '+1234567890'),
                to=phone_number
            )
            
            # Log delivery attempt
            delivery_log = NotificationDeliveryLog(
                notification_id=notification.id,
                channel=NotificationChannel.SMS,
                status=NotificationStatus.SENT,
                recipient=phone_number,
                external_id=message.sid,
                sent_at=datetime.utcnow()
            )
            db.add(delivery_log)
            db.commit()
            
            logger.info(f"SMS sent for notification {notification.id} to {phone_number}")
            
        except Exception as e:
            # Log failure
            delivery_log = NotificationDeliveryLog(
                notification_id=notification.id,
                channel=NotificationChannel.SMS,
                status=NotificationStatus.FAILED,
                recipient=phone_number,
                error_message=str(e),
                failed_at=datetime.utcnow()
            )
            db.add(delivery_log)
            db.commit()
            
            logger.error(f"Failed to send SMS for notification {notification.id}: {str(e)}")

    async def _send_push(self, db: Session, notification: Notification, push_token: str):
        """Send push notification (placeholder - would integrate with FCM/APNS)"""
        # This would integrate with Firebase Cloud Messaging or Apple Push Notification Service
        # For now, just log the delivery attempt
        delivery_log = NotificationDeliveryLog(
            notification_id=notification.id,
            channel=NotificationChannel.PUSH,
            status=NotificationStatus.SENT,
            recipient=push_token,
            sent_at=datetime.utcnow()
        )
        db.add(delivery_log)
        db.commit()
        
        logger.info(f"Push notification logged for notification {notification.id}")

    async def _create_in_app_notification(self, db: Session, notification: Notification):
        """Create in-app notification (just mark as delivered since it's stored in DB)"""
        delivery_log = NotificationDeliveryLog(
            notification_id=notification.id,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.DELIVERED,
            recipient=str(notification.user_id),
            sent_at=datetime.utcnow(),
            delivered_at=datetime.utcnow()
        )
        db.add(delivery_log)
        db.commit()

    def _generate_email_template(self, notification: Notification) -> str:
        """Generate HTML email template"""
        priority_colors = {
            NotificationPriority.LOW: "#28a745",
            NotificationPriority.MEDIUM: "#ffc107", 
            NotificationPriority.HIGH: "#fd7e14",
            NotificationPriority.URGENT: "#dc3545"
        }
        
        color = priority_colors.get(notification.priority, "#6c757d")
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px;">
                    <h1 style="margin: 0; font-size: 24px;">{notification.title}</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Henry's SmartStock AI</p>
                </div>
                <div style="padding: 30px;">
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin: 0 0 20px 0;">
                        {notification.message}
                    </p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 14px; color: #6c757d;">
                            <strong>Priority:</strong> {notification.priority.value.title()}<br>
                            <strong>Type:</strong> {notification.notification_type.value.replace('_', ' ').title()}<br>
                            <strong>Time:</strong> {notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                    </div>
                </div>
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #dee2e6;">
                    <p style="margin: 0; font-size: 12px; color: #6c757d;">
                        This is an automated notification from Henry's SmartStock AI system.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    async def get_user_notifications(
        self, 
        db: Session, 
        user_id: UUID, 
        limit: int = 50, 
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            # Check if notification has been read (has a read delivery log)
            read_notification_ids = db.query(NotificationDeliveryLog.notification_id).filter(
                NotificationDeliveryLog.read_at.isnot(None)
            ).subquery()
            
            query = query.filter(~Notification.id.in_(read_notification_ids))
        
        return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    async def mark_notification_read(self, db: Session, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read"""
        notification = db.query(Notification).filter(
            and_(Notification.id == notification_id, Notification.user_id == user_id)
        ).first()
        
        if not notification:
            return False
        
        # Update in-app delivery log to mark as read
        delivery_log = db.query(NotificationDeliveryLog).filter(
            and_(
                NotificationDeliveryLog.notification_id == notification_id,
                NotificationDeliveryLog.channel == NotificationChannel.IN_APP
            )
        ).first()
        
        if delivery_log:
            delivery_log.read_at = datetime.utcnow()
            delivery_log.status = NotificationStatus.READ
            db.commit()
        
        return True

    async def get_notification_summary(self, db: Session, user_id: UUID) -> dict:
        """Get notification summary for dashboard"""
        # Get unread notifications
        unread_notifications = await self.get_user_notifications(db, user_id, unread_only=True)
        
        # Count by type and priority
        by_type = {}
        by_priority = {}
        
        for notification in unread_notifications:
            by_type[notification.notification_type] = by_type.get(notification.notification_type, 0) + 1
            by_priority[notification.priority] = by_priority.get(notification.priority, 0) + 1
        
        # Get recent notifications (last 10)
        recent_notifications = await self.get_user_notifications(db, user_id, limit=10)
        
        return {
            "total_unread": len(unread_notifications),
            "by_type": by_type,
            "by_priority": by_priority,
            "recent_notifications": recent_notifications
        }


# Global service instance
notification_service = NotificationService()