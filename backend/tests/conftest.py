import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
import uuid


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "barback",
        "hashed_password": "hashed_password_here"
    }


@pytest.fixture
def sample_location_data():
    """Sample location data for testing."""
    return {
        "name": "Main Bar",
        "type": "bar",
        "description": "Primary bar location",
        "is_active": True
    }


@pytest.fixture
def sample_supplier_data():
    """Sample supplier data for testing."""
    return {
        "name": "Test Supplier",
        "contact_name": "John Doe",
        "email": "supplier@example.com",
        "phone": "555-1234",
        "address": "123 Supplier St",
        "is_active": True,
        "is_preferred": False
    }


@pytest.fixture
def sample_inventory_item_data():
    """Sample inventory item data for testing."""
    return {
        "name": "Test Vodka",
        "category": "spirits",
        "barcode": "123456789",
        "sku": "VOD001",
        "description": "Premium vodka",
        "unit_of_measure": "bottle",
        "cost_per_unit": 25.99,
        "selling_price": 45.00,
        "par_level": 10.0,
        "reorder_point": 5.0,
        "is_active": "true"
    }