# Henry's SmartStock AI - Core Data Models Implementation

This document describes the implementation of Task 2: Core data models and database schema for Henry's SmartStock AI inventory management system.

## Implementation Overview

The implementation includes:

1. **SQLAlchemy Database Models** - Core data models with proper relationships
2. **Pydantic Schemas** - Data validation and serialization models
3. **Alembic Migrations** - Database schema migrations with proper indexes
4. **Comprehensive Unit Tests** - Test coverage for all models and operations
5. **Database Configuration** - Production-ready database setup

## Database Models

### User Model (`app/models/user.py`)
- **Purpose**: Manages system users with role-based permissions
- **Roles**: barback, bartender, manager, admin
- **Key Features**:
  - UUID primary key
  - Unique username and email constraints
  - Password hashing support
  - Role-based access control
  - Audit timestamps (created_at, updated_at)

### Location Model (`app/models/location.py`)
- **Purpose**: Manages bar locations and storage areas
- **Types**: bar, storage, kitchen, rooftop
- **Key Features**:
  - Multi-location inventory support
  - Active/inactive status
  - Descriptive information

### Supplier Model (`app/models/supplier.py`)
- **Purpose**: Manages vendor information and API integrations
- **Key Features**:
  - Contact information storage
  - API credentials (encrypted JSON field)
  - Payment terms and delivery schedules
  - Preferred supplier marking
  - Integration-ready structure

### InventoryItem Model (`app/models/inventory.py`)
- **Purpose**: Core inventory item management
- **Categories**: spirits, beer, wine, mixers, garnishes, food, supplies
- **Key Features**:
  - Barcode/SKU tracking
  - Cost and pricing information
  - Par levels and reorder points
  - Supplier relationships
  - Expiration tracking for perishables
  - Multiple units of measure

### StockLevel Model (`app/models/inventory.py`)
- **Purpose**: Tracks inventory levels by location
- **Key Features**:
  - Current and reserved stock tracking
  - Last counted timestamps
  - Unique item-location constraints
  - Real-time stock updates

### Transaction Model (`app/models/transaction.py`)
- **Purpose**: Records all inventory movements
- **Types**: sale, adjustment, receive, waste, transfer, count
- **Key Features**:
  - Complete audit trail
  - POS system integration support
  - Cost tracking
  - Reference number support
  - User attribution

## Pydantic Schemas

### Validation Schemas (`app/schemas/`)
- **UserCreate/Update/Response**: User management with validation
- **LocationCreate/Update/Response**: Location management
- **SupplierCreate/Update/Response**: Supplier management (excludes sensitive API credentials)
- **InventoryItemCreate/Update/Response**: Item management with decimal precision
- **StockLevelCreate/Update/Response**: Stock level management
- **TransactionCreate/Response**: Transaction recording

### Key Validation Features
- Email validation
- Password strength requirements
- Decimal precision for monetary values
- Non-negative constraints for quantities
- Required field validation
- Enum value validation

## Database Schema

### Migration Files (`alembic/versions/`)
- **0001_initial_schema.py**: Complete initial database schema
- **Proper Indexes**: Performance-optimized indexes for common queries
- **Foreign Key Constraints**: Data integrity enforcement
- **Enum Types**: PostgreSQL enum types for categories

### Key Indexes
- `idx_inventory_category_active`: Fast category-based queries
- `idx_stock_item_location`: Unique stock level constraints
- `idx_transaction_item_date`: Time-series transaction queries
- `idx_transaction_type_date`: Transaction type filtering

## Requirements Mapping

This implementation addresses the following requirements:

### Requirement 1.1 (Barcode Scanning)
- ✅ Barcode field in InventoryItem model
- ✅ Unique barcode constraints
- ✅ Transaction recording for inventory updates

### Requirement 1.2 (Stock Alerts)
- ✅ Par level and reorder point fields
- ✅ StockLevel model for real-time tracking
- ✅ Multi-location stock management

### Requirement 4.1 (Role-based Access)
- ✅ User model with role enumeration
- ✅ Four role levels: barback, bartender, manager, admin
- ✅ JWT-ready user authentication structure

### Requirement 6.2 (Multi-location Tracking)
- ✅ Location model with different types
- ✅ StockLevel model linking items to locations
- ✅ Transaction model with location tracking

### Requirement 8.1 (Waste Tracking)
- ✅ Transaction types including 'waste'
- ✅ Expiration tracking in InventoryItem
- ✅ FIFO support through transaction timestamps

## Testing Implementation

### Unit Tests (`tests/`)
- **test_models.py**: Comprehensive model testing
  - CRUD operations
  - Relationship testing
  - Constraint validation
  - Enum value testing

- **test_schemas.py**: Pydantic schema validation
  - Valid data acceptance
  - Invalid data rejection
  - Partial update testing
  - Security field exclusion

- **test_database_operations.py**: Database integration testing
  - Complex query operations
  - Relationship integrity
  - Constraint enforcement
  - Performance validation

### Test Coverage
- ✅ All model creation and validation
- ✅ All relationship mappings
- ✅ All constraint enforcement
- ✅ All schema validation rules
- ✅ Complex database operations

## Usage Examples

### Creating a User
```python
from app.models import User, UserRole

user = User(
    username="bartender1",
    email="bartender@henrys.com",
    full_name="John Smith",
    role=UserRole.BARTENDER,
    hashed_password="hashed_password_here"
)
```

### Creating an Inventory Item
```python
from app.models import InventoryItem, ItemCategory, UnitOfMeasure

item = InventoryItem(
    name="Grey Goose Vodka",
    category=ItemCategory.SPIRITS,
    barcode="123456789012",
    unit_of_measure=UnitOfMeasure.BOTTLE,
    cost_per_unit=Decimal("28.99"),
    par_level=6.0,
    reorder_point=3.0,
    supplier_id=supplier.id
)
```

### Recording a Transaction
```python
from app.models import Transaction, TransactionType

transaction = Transaction(
    item_id=item.id,
    location_id=location.id,
    user_id=user.id,
    transaction_type=TransactionType.SALE,
    quantity=-1.0,
    unit_cost=Decimal("28.99"),
    notes="Sold to customer"
)
```

## Running Tests

### With pytest (recommended)
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

### With custom test runner
```bash
cd backend
python run_tests.py
```

### With Docker
```bash
docker-compose up -d postgres
cd backend
python -m pytest tests/
```

## Database Setup

### Local Development
1. Install PostgreSQL
2. Create database: `henrys_smartstock`
3. Update `.env` file with database credentials
4. Run migrations: `alembic upgrade head`

### Production Deployment
1. Configure production database URL
2. Set environment variables
3. Run migrations in production environment
4. Verify all indexes are created

## Performance Considerations

### Optimized Queries
- Proper indexing for common query patterns
- Composite indexes for multi-column searches
- Foreign key indexes for join operations

### Scalability Features
- UUID primary keys for distributed systems
- Partitioning-ready timestamp fields
- Efficient relationship mappings

## Security Features

### Data Protection
- Encrypted API credentials storage
- Password hashing support
- Audit trail for all changes
- Role-based access control

### Validation
- Input sanitization through Pydantic
- SQL injection prevention
- Constraint enforcement at database level

## Next Steps

This implementation provides the foundation for:
1. **API Endpoints**: RESTful APIs using these models
2. **Authentication Service**: JWT-based auth using User model
3. **Real-time Updates**: WebSocket integration with StockLevel
4. **Reporting**: Analytics using Transaction history
5. **ML Integration**: Forecasting using historical transaction data

The models are production-ready and follow best practices for:
- Database design
- Data validation
- Security
- Performance
- Maintainability
- Testing

All requirements for Task 2 have been successfully implemented and tested.