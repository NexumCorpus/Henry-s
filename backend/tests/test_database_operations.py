import pytest
from sqlalchemy import text
from app.models import (
    User, Location, Supplier, InventoryItem, StockLevel, Transaction,
    UserRole, LocationType, ItemCategory, UnitOfMeasure, TransactionType
)
from decimal import Decimal


class TestDatabaseOperations:
    """Test database operations and relationships."""
    
    def test_database_connection(self, db_session):
        """Test basic database connectivity."""
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1
    
    def test_user_crud_operations(self, db_session):
        """Test CRUD operations for User model."""
        # Create
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.BARBACK,
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Read
        retrieved_user = db_session.query(User).filter(User.username == "testuser").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        
        # Update
        retrieved_user.full_name = "Updated Name"
        db_session.commit()
        
        updated_user = db_session.query(User).filter(User.username == "testuser").first()
        assert updated_user.full_name == "Updated Name"
        
        # Delete
        db_session.delete(updated_user)
        db_session.commit()
        
        deleted_user = db_session.query(User).filter(User.username == "testuser").first()
        assert deleted_user is None
    
    def test_inventory_item_supplier_relationship(self, db_session):
        """Test relationship between InventoryItem and Supplier."""
        # Create supplier
        supplier = Supplier(
            name="Test Supplier",
            contact_name="John Doe",
            email="supplier@example.com",
            is_active=True,
            is_preferred=False
        )
        db_session.add(supplier)
        db_session.commit()
        
        # Create inventory item with supplier
        item = InventoryItem(
            name="Test Vodka",
            category=ItemCategory.SPIRITS,
            barcode="123456789",
            unit_of_measure=UnitOfMeasure.BOTTLE,
            cost_per_unit=Decimal("25.99"),
            par_level=10.0,
            reorder_point=5.0,
            supplier_id=supplier.id,
            is_active="true"
        )
        db_session.add(item)
        db_session.commit()
        
        # Test relationship
        assert item.supplier.name == "Test Supplier"
        assert supplier.inventory_items[0].name == "Test Vodka"
    
    def test_stock_level_relationships(self, db_session):
        """Test relationships for StockLevel model."""
        # Create dependencies
        location = Location(
            name="Main Bar",
            type=LocationType.BAR,
            is_active=True
        )
        
        item = InventoryItem(
            name="Test Beer",
            category=ItemCategory.BEER,
            unit_of_measure=UnitOfMeasure.BOTTLE,
            par_level=24.0,
            reorder_point=12.0,
            is_active="true"
        )
        
        db_session.add(location)
        db_session.add(item)
        db_session.commit()
        
        # Create stock level
        stock_level = StockLevel(
            item_id=item.id,
            location_id=location.id,
            current_stock=18.0,
            reserved_stock=2.0
        )
        db_session.add(stock_level)
        db_session.commit()
        
        # Test relationships
        assert stock_level.item.name == "Test Beer"
        assert stock_level.location.name == "Main Bar"
        assert item.stock_levels[0].current_stock == 18.0
        assert location.stock_levels[0].current_stock == 18.0
    
    def test_transaction_relationships(self, db_session):
        """Test relationships for Transaction model."""
        # Create dependencies
        user = User(
            username="bartender1",
            email="bartender@example.com",
            full_name="Bartender One",
            role=UserRole.BARTENDER,
            hashed_password="hashed_password"
        )
        
        location = Location(
            name="Rooftop Bar",
            type=LocationType.ROOFTOP,
            is_active=True
        )
        
        item = InventoryItem(
            name="Premium Whiskey",
            category=ItemCategory.SPIRITS,
            unit_of_measure=UnitOfMeasure.BOTTLE,
            par_level=5.0,
            reorder_point=2.0,
            is_active="true"
        )
        
        db_session.add(user)
        db_session.add(location)
        db_session.add(item)
        db_session.commit()
        
        # Create transaction
        transaction = Transaction(
            item_id=item.id,
            location_id=location.id,
            user_id=user.id,
            transaction_type=TransactionType.SALE,
            quantity=-1.0,
            unit_cost=Decimal("45.00"),
            total_cost=Decimal("45.00"),
            notes="Sale to customer"
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Test relationships
        assert transaction.item.name == "Premium Whiskey"
        assert transaction.location.name == "Rooftop Bar"
        assert transaction.user.username == "bartender1"
        assert user.transactions[0].quantity == -1.0
        assert location.transactions[0].transaction_type == TransactionType.SALE
        assert item.transactions[0].total_cost == Decimal("45.00")
    
    def test_complex_query_operations(self, db_session):
        """Test complex database queries."""
        # Create test data
        user = User(
            username="manager1",
            email="manager@example.com",
            full_name="Manager One",
            role=UserRole.MANAGER,
            hashed_password="hashed_password"
        )
        
        location1 = Location(name="Main Bar", type=LocationType.BAR, is_active=True)
        location2 = Location(name="Storage", type=LocationType.STORAGE, is_active=True)
        
        supplier = Supplier(name="Premium Spirits Co", is_active=True, is_preferred=True)
        
        item1 = InventoryItem(
            name="Vodka A", category=ItemCategory.SPIRITS,
            unit_of_measure=UnitOfMeasure.BOTTLE, par_level=10.0,
            reorder_point=5.0, is_active="true"
        )
        item2 = InventoryItem(
            name="Beer B", category=ItemCategory.BEER,
            unit_of_measure=UnitOfMeasure.BOTTLE, par_level=24.0,
            reorder_point=12.0, is_active="true"
        )
        
        db_session.add_all([user, location1, location2, supplier, item1, item2])
        db_session.commit()
        
        # Create stock levels
        stock1 = StockLevel(item_id=item1.id, location_id=location1.id, current_stock=8.0)
        stock2 = StockLevel(item_id=item2.id, location_id=location1.id, current_stock=20.0)
        stock3 = StockLevel(item_id=item1.id, location_id=location2.id, current_stock=15.0)
        
        db_session.add_all([stock1, stock2, stock3])
        db_session.commit()
        
        # Create transactions
        trans1 = Transaction(
            item_id=item1.id, location_id=location1.id, user_id=user.id,
            transaction_type=TransactionType.SALE, quantity=-2.0
        )
        trans2 = Transaction(
            item_id=item2.id, location_id=location1.id, user_id=user.id,
            transaction_type=TransactionType.ADJUSTMENT, quantity=4.0
        )
        
        db_session.add_all([trans1, trans2])
        db_session.commit()
        
        # Test complex queries
        
        # 1. Find all items below reorder point in main bar
        low_stock_items = db_session.query(InventoryItem).join(StockLevel).filter(
            StockLevel.location_id == location1.id,
            StockLevel.current_stock < InventoryItem.reorder_point
        ).all()
        
        assert len(low_stock_items) == 1
        assert low_stock_items[0].name == "Vodka A"
        
        # 2. Get total stock for each item across all locations
        from sqlalchemy import func
        total_stock_query = db_session.query(
            InventoryItem.name,
            func.sum(StockLevel.current_stock).label('total_stock')
        ).join(StockLevel).group_by(InventoryItem.id, InventoryItem.name).all()
        
        assert len(total_stock_query) == 2
        stock_dict = {name: total for name, total in total_stock_query}
        assert stock_dict["Vodka A"] == 23.0  # 8 + 15
        assert stock_dict["Beer B"] == 20.0
        
        # 3. Find all transactions by a specific user
        user_transactions = db_session.query(Transaction).filter(
            Transaction.user_id == user.id
        ).all()
        
        assert len(user_transactions) == 2
        
        # 4. Get items by category with their suppliers
        spirits_with_suppliers = db_session.query(InventoryItem).outerjoin(Supplier).filter(
            InventoryItem.category == ItemCategory.SPIRITS
        ).all()
        
        assert len(spirits_with_suppliers) == 1
        assert spirits_with_suppliers[0].name == "Vodka A"
    
    def test_database_constraints(self, db_session):
        """Test database constraints and validations."""
        # Test unique constraints
        user1 = User(
            username="unique_user",
            email="unique@example.com",
            full_name="User One",
            role=UserRole.BARBACK,
            hashed_password="password"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create user with same username
        user2 = User(
            username="unique_user",  # Same username
            email="different@example.com",
            full_name="User Two",
            role=UserRole.BARBACK,
            hashed_password="password"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
        
        db_session.rollback()
        
        # Test foreign key constraints
        # Try to create stock level with non-existent item
        from uuid import uuid4
        invalid_stock = StockLevel(
            item_id=uuid4(),  # Non-existent item
            location_id=uuid4(),  # Non-existent location
            current_stock=10.0
        )
        db_session.add(invalid_stock)
        
        with pytest.raises(Exception):  # Should raise foreign key error
            db_session.commit()