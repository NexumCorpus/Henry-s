import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import schedule
import time
from threading import Thread

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.notification import notification_service

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """Background scheduler for periodic notification checks"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread: Optional[Thread] = None
        
    def start(self):
        """Start the notification scheduler"""
        if self.running:
            logger.warning("Notification scheduler is already running")
            return
            
        logger.info("Starting notification scheduler")
        self.running = True
        
        # Schedule periodic checks
        schedule.every(5).minutes.do(self._check_stock_alerts)
        schedule.every(1).hours.do(self._check_expiration_alerts)
        schedule.every().day.at("09:00").do(self._daily_summary)
        schedule.every().day.at("02:00").do(self._cleanup_old_notifications)
        
        # Start scheduler in background thread
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
    def stop(self):
        """Stop the notification scheduler"""
        if not self.running:
            return
            
        logger.info("Stopping notification scheduler")
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
            
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in notification scheduler: {str(e)}")
                time.sleep(60)  # Wait longer on error
                
    def _check_stock_alerts(self):
        """Check for stock level alerts"""
        try:
            logger.info("Running stock alerts check")
            db = SessionLocal()
            try:
                # Run the async function in a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(notification_service.check_stock_alerts(db))
                loop.close()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error checking stock alerts: {str(e)}")
            
    def _check_expiration_alerts(self):
        """Check for expiration alerts"""
        try:
            logger.info("Running expiration alerts check")
            db = SessionLocal()
            try:
                # Run the async function in a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(notification_service.check_expiration_alerts(db))
                loop.close()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error checking expiration alerts: {str(e)}")
            
    def _daily_summary(self):
        """Send daily summary notifications to managers"""
        try:
            logger.info("Generating daily summary notifications")
            db = SessionLocal()
            try:
                from app.models.user import User, UserRole
                from app.schemas.notification import BulkNotificationCreate
                from app.models.notification import NotificationType, NotificationPriority, NotificationChannel
                
                # Get all managers and admins
                managers = db.query(User).filter(
                    User.role.in_([UserRole.MANAGER, UserRole.ADMIN]),
                    User.is_active == True
                ).all()
                
                if not managers:
                    return
                    
                # Create daily summary notification
                bulk_data = BulkNotificationCreate(
                    title="Daily Inventory Summary",
                    message="Your daily inventory summary is ready. Check the dashboard for detailed analytics.",
                    notification_type=NotificationType.SYSTEM_ALERT,
                    priority=NotificationPriority.LOW,
                    user_ids=[manager.id for manager in managers],
                    channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
                )
                
                # Run the async function in a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    notification_service.create_bulk_notifications(db, bulk_data)
                )
                loop.close()
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error generating daily summary: {str(e)}")
            
    def _cleanup_old_notifications(self):
        """Clean up old notifications and delivery logs"""
        try:
            logger.info("Cleaning up old notifications")
            db = SessionLocal()
            try:
                from app.models.notification import Notification, NotificationDeliveryLog
                
                # Delete notifications older than 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                # Delete old delivery logs first (due to foreign key constraints)
                old_delivery_logs = db.query(NotificationDeliveryLog).join(Notification).filter(
                    Notification.created_at < cutoff_date
                ).delete(synchronize_session=False)
                
                # Delete old notifications
                old_notifications = db.query(Notification).filter(
                    Notification.created_at < cutoff_date
                ).delete(synchronize_session=False)
                
                db.commit()
                
                logger.info(f"Cleaned up {old_notifications} old notifications and {old_delivery_logs} delivery logs")
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {str(e)}")
            
    def force_check_stock_alerts(self):
        """Force an immediate stock alerts check"""
        logger.info("Force checking stock alerts")
        self._check_stock_alerts()
        
    def force_check_expiration_alerts(self):
        """Force an immediate expiration alerts check"""
        logger.info("Force checking expiration alerts")
        self._check_expiration_alerts()


# Global scheduler instance
notification_scheduler = NotificationScheduler()


def start_notification_scheduler():
    """Start the notification scheduler (called from main app)"""
    notification_scheduler.start()
    

def stop_notification_scheduler():
    """Stop the notification scheduler (called on app shutdown)"""
    notification_scheduler.stop()