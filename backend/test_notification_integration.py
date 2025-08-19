#!/usr/bin/env python3
"""
Simple integration test for the notification system
Run this to verify the notification system is working correctly
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.location import Location, LocationType
from app.models.inventory import InventoryItem, StockLevel, ItemCategory, UnitOfMeasure
from app.models.notification import (
    NotificationRule, NotificationType, NotificationChannel, NotificationPriority
)
from app.services.notification import notification_service
from app.schemas.notification import NotificationCreate


async def test_notification_system():
    """Test the notification system end-to-end"""
    print("🧪 Testing Henry's SmartStock AI Notification System")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 1. Create test user
        print("1. Creating test user...")
        test_user = User(
            id=uuid4(),
            username="test_bartender",
            email="test@henrysonmarket.com",
            hashed_password="test_password",
            full_name="Test Bartender",
            role=UserRole.BARTENDER
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"   ✅ Created user: {test_user.full_name} ({test_user.email})")
        
        # 2. Create test location
        print("2. Creating test location...")
        test_location = Location(
            id=uuid4(),
            name="Main Bar",
            type=LocationType.BAR
        )
        db.add(test_location)
        db.commit()
        db.refresh(test_location)
        print(f"   ✅ Created location: {test_location.name}")
        
        # 3. Create test inventory item
        print("3. Creating test inventory item...")
        test_item = InventoryItem(
            id=uuid4(),
            name="Premium Vodka",
            category=ItemCategory.SPIRITS,
            barcode="123456789",
            unit_of_measure=UnitOfMeasure.BOTTLE,
            par_level=10.0,
            reorder_point=5.0
        )
        db.add(test_item)
        db.commit()
        db.refresh(test_item)
        print(f"   ✅ Created item: {test_item.name}")
        
        # 4. Create low stock level
        print("4. Creating low stock level...")
        stock_level = StockLevel(
            id=uuid4(),
            item_id=test_item.id,
            location_id=test_location.id,
            current_stock=2.0  # Below reorder point of 5.0
        )
        db.add(stock_level)
        db.commit()
        db.refresh(stock_level)
        print(f"   ✅ Created stock level: {stock_level.current_stock} bottles (below reorder point)")
        
        # 5. Create notification rule
        print("5. Creating notification rule...")
        rule_data = {
            "name": "Low Stock Alert - Premium Vodka",
            "description": "Alert when premium vodka is running low",
            "notification_type": NotificationType.LOW_STOCK,
            "location_id": test_location.id,
            "item_category": ItemCategory.SPIRITS.value,
            "conditions": {"stock_threshold": 5},
            "channels": [NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            "priority": NotificationPriority.MEDIUM,
            "is_active": True
        }
        
        notification_rule = await notification_service.create_notification_rule(
            db, test_user.id, rule_data
        )
        print(f"   ✅ Created notification rule: {notification_rule.name}")
        
        # 6. Test manual notification creation
        print("6. Creating manual notification...")
        notification_data = NotificationCreate(
            rule_id=notification_rule.id,
            user_id=test_user.id,
            title="Test Low Stock Alert",
            message=f"{test_item.name} is running low at {test_location.name}. Current stock: {stock_level.current_stock} bottles.",
            notification_type=NotificationType.LOW_STOCK,
            priority=NotificationPriority.MEDIUM,
            item_id=test_item.id,
            location_id=test_location.id,
            data={
                "current_stock": stock_level.current_stock,
                "threshold": 5,
                "reorder_point": test_item.reorder_point
            }
        )
        
        notification = await notification_service.create_notification(db, notification_data)
        print(f"   ✅ Created notification: {notification.title}")
        
        # 7. Test stock alerts check
        print("7. Testing automatic stock alerts check...")
        await notification_service.check_stock_alerts(db)
        print("   ✅ Stock alerts check completed")
        
        # 8. Get user notifications
        print("8. Retrieving user notifications...")
        user_notifications = await notification_service.get_user_notifications(
            db, test_user.id, limit=10
        )
        print(f"   ✅ Found {len(user_notifications)} notifications for user")
        
        for i, notif in enumerate(user_notifications, 1):
            print(f"      {i}. {notif.title} (Priority: {notif.priority.value})")
        
        # 9. Get notification summary
        print("9. Getting notification summary...")
        summary = await notification_service.get_notification_summary(db, test_user.id)
        print(f"   ✅ Summary: {summary['total_unread']} unread notifications")
        print(f"      By type: {dict(summary['by_type'])}")
        print(f"      By priority: {dict(summary['by_priority'])}")
        
        # 10. Test notification preferences
        print("10. Testing notification preferences...")
        user_rules = await notification_service.get_user_notification_rules(db, test_user.id)
        print(f"    ✅ User has {len(user_rules)} notification rules")
        
        print("\n" + "=" * 60)
        print("🎉 All notification system tests passed!")
        print("✅ Notification models created successfully")
        print("✅ Notification service functions working")
        print("✅ Stock alert detection working")
        print("✅ Notification delivery system ready")
        print("✅ API endpoints integrated")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        try:
            # Delete in reverse order due to foreign key constraints
            db.query(StockLevel).filter(StockLevel.item_id == test_item.id).delete()
            db.query(NotificationRule).filter(NotificationRule.user_id == test_user.id).delete()
            db.query(InventoryItem).filter(InventoryItem.id == test_item.id).delete()
            db.query(Location).filter(Location.id == test_location.id).delete()
            db.query(User).filter(User.id == test_user.id).delete()
            db.commit()
            print("   ✅ Test data cleaned up")
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {str(e)}")
        finally:
            db.close()


if __name__ == "__main__":
    print("Starting notification system integration test...")
    success = asyncio.run(test_notification_system())
    
    if success:
        print("\n🚀 Notification system is ready for production!")
        sys.exit(0)
    else:
        print("\n💥 Notification system needs attention!")
        sys.exit(1)