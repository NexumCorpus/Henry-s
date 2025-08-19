from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.notification import NotificationRule, Notification, UserNotificationPreference
from app.schemas.notification import (
    NotificationRuleCreate, NotificationRuleUpdate, NotificationRuleResponse,
    NotificationResponse, NotificationSummary, BulkNotificationCreate,
    UserNotificationPreferenceCreate, UserNotificationPreferenceUpdate, 
    UserNotificationPreferenceResponse, NotificationTestRequest
)
from app.services.notification import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


# Notification Rules endpoints
@router.post("/rules", response_model=NotificationRuleResponse)
async def create_notification_rule(
    rule_data: NotificationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification rule"""
    try:
        rule = await notification_service.create_notification_rule(
            db, current_user.id, rule_data.dict()
        )
        return rule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules", response_model=List[NotificationRuleResponse])
async def get_notification_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notification rules for the current user"""
    rules = await notification_service.get_user_notification_rules(db, current_user.id)
    return rules


@router.get("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def get_notification_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification rule"""
    rule = db.query(NotificationRule).filter(
        NotificationRule.id == rule_id,
        NotificationRule.user_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Notification rule not found")
    
    return rule


@router.put("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def update_notification_rule(
    rule_id: UUID,
    rule_update: NotificationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a notification rule"""
    rule = await notification_service.update_notification_rule(
        db, rule_id, current_user.id, rule_update.dict(exclude_unset=True)
    )
    
    if not rule:
        raise HTTPException(status_code=404, detail="Notification rule not found")
    
    return rule


@router.delete("/rules/{rule_id}")
async def delete_notification_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification rule"""
    success = await notification_service.delete_notification_rule(
        db, rule_id, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification rule not found")
    
    return {"message": "Notification rule deleted successfully"}


# Notifications endpoints
@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user"""
    notifications = await notification_service.get_user_notifications(
        db, current_user.id, limit, offset, unread_only
    )
    return notifications


@router.get("/summary", response_model=NotificationSummary)
async def get_notification_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification summary for dashboard"""
    summary = await notification_service.get_notification_summary(db, current_user.id)
    return summary


@router.post("/bulk", response_model=List[NotificationResponse])
async def create_bulk_notifications(
    bulk_data: BulkNotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create notifications for multiple users (admin only)"""
    # Check if user has admin privileges
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions to create bulk notifications"
        )
    
    notifications = await notification_service.create_bulk_notifications(db, bulk_data)
    return notifications


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    success = await notification_service.mark_notification_read(
        db, notification_id, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


# User Notification Preferences endpoints
@router.get("/preferences", response_model=UserNotificationPreferenceResponse)
async def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's notification preferences"""
    preferences = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences
        preferences = UserNotificationPreference(user_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences


@router.put("/preferences", response_model=UserNotificationPreferenceResponse)
async def update_notification_preferences(
    preferences_update: UserNotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's notification preferences"""
    preferences = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create new preferences
        preferences_data = preferences_update.dict(exclude_unset=True)
        preferences_data['user_id'] = current_user.id
        preferences = UserNotificationPreference(**preferences_data)
        db.add(preferences)
    else:
        # Update existing preferences
        for field, value in preferences_update.dict(exclude_unset=True).items():
            setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    return preferences


# System endpoints for triggering checks
@router.post("/check/stock-alerts")
async def trigger_stock_alerts_check(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger stock alerts check (admin only)"""
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions to trigger system checks"
        )
    
    background_tasks.add_task(notification_service.check_stock_alerts, db)
    return {"message": "Stock alerts check triggered"}


@router.post("/check/expiration-alerts")
async def trigger_expiration_alerts_check(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger expiration alerts check (admin only)"""
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions to trigger system checks"
        )
    
    background_tasks.add_task(notification_service.check_expiration_alerts, db)
    return {"message": "Expiration alerts check triggered"}


@router.post("/test")
async def test_notification_delivery(
    test_request: NotificationTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test notification delivery (admin only)"""
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions to test notifications"
        )
    
    try:
        # Create a test notification
        from app.schemas.notification import NotificationCreate
        from app.models.notification import NotificationType, NotificationPriority
        
        test_notification_data = NotificationCreate(
            rule_id=None,
            user_id=current_user.id,
            title=test_request.title,
            message=test_request.message,
            notification_type=NotificationType.SYSTEM_ALERT,
            priority=NotificationPriority.LOW
        )
        
        notification = await notification_service.create_notification(db, test_notification_data)
        
        return {
            "message": "Test notification created and delivery attempted",
            "notification_id": notification.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to send test notification: {str(e)}")


# Webhook endpoints for external services
@router.post("/webhooks/twilio")
async def twilio_webhook(
    # Twilio webhook data would be processed here
    db: Session = Depends(get_db)
):
    """Handle Twilio delivery status webhooks"""
    # This would process Twilio webhook data to update delivery status
    # Implementation depends on Twilio webhook format
    return {"status": "received"}


@router.post("/webhooks/sendgrid")
async def sendgrid_webhook(
    # SendGrid webhook data would be processed here
    db: Session = Depends(get_db)
):
    """Handle SendGrid delivery status webhooks"""
    # This would process SendGrid webhook data to update delivery status
    # Implementation depends on SendGrid webhook format
    return {"status": "received"}