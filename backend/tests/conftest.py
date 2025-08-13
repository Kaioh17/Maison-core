import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.database import get_db, get_base_db
from app.models.base import Base
from app.api.core.oauth2 import create_access_token
from app.models.tenant import Tenants
from app.models.driver import Drivers
from app.models.user import Users
from app.models.vehicle import Vehicles
from app.models.booking import Bookings
from app.utils.password_utils import hash
from .test_setting import Settings
import os

settings = Settings()
# Test database configuration
SQLALCHEMY_DATABASE_URL = settings.db_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_base_db():
    """Override base database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_base_db] = override_get_base_db

@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    """Database session fixture"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_tenant(db_session):
    """Test tenant fixture"""
    tenant = Tenants(
        id=1,
        company_name="Test Company",
        email="test@company.com",
        password=hash("testpassword123"),
        role="tenant",
        is_active=True,
        first_name="Test",
        last_name="Company",
        phone_no="+1234567890",
        slug="testcompany",
        address="123 Test St",
        city="Test City",
        drivers_count=0,
        is_verified=True
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant

@pytest.fixture
def test_driver(db_session, test_tenant):
    """Test driver fixture"""
    driver = Drivers(
        id=1,
        tenant_id=test_tenant.id,
        first_name="John",
        last_name="Doe",
        email="driver@test.com",
        phone_no="+1234567890",
        is_active=True,
        driver_type="standard",
        completed_rides="0",
        driver_token="test_driver_token",
        is_registered="registered",
        status="available"
    )
    db_session.add(driver)
    db_session.commit()
    db_session.refresh(driver)
    return driver

@pytest.fixture
def test_user(db_session, test_tenant):
    """Test user/rider fixture"""
    user = Users(
        id=1,
        tenant_id=test_tenant.id,
        first_name="Jane",
        last_name="Smith",
        email="user@test.com",
        phone_no="+0987654321",
        password="testpassword123",
        role="rider",
        tier="free"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_vehicle(db_session, test_tenant, test_driver):
    """Test vehicle fixture"""
    vehicle = Vehicles(
        id=1,
        tenant_id=test_tenant.id,
        driver_id=test_driver.id,
        make="Toyota",
        model="Camry",
        year=2020,
        license_plate="ABC123",
        status="available"
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)
    return vehicle

@pytest.fixture
def test_booking(db_session, test_tenant, test_driver, test_user):
    """Test booking fixture"""
    booking = Bookings(
        id=1,
        tenant_id=test_tenant.id,
        driver_id=test_driver.id,
        rider_id=test_user.id,
        service_type="standard",
        pickup_location="123 Main St",
        pickup_time="2024-01-01T10:00:00",
        dropoff_location="456 Oak Ave",
        dropoff_time="2024-01-01T11:00:00",
        city="Test City",
        booking_status="pending",
        estimated_price=25.00,
        notes="Test booking"
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking

@pytest.fixture
def tenant_token(test_tenant):
    """JWT token for tenant authentication"""
    return create_access_token(data={"id": str(test_tenant.id), "role": "tenant"})

@pytest.fixture
def driver_token(test_driver):
    """JWT token for driver authentication"""
    return create_access_token(data={"id": str(test_driver.id), "role": "driver",  "tenant_id": str(test_driver.tenant_id)})

@pytest.fixture
def user_token(test_user):
    """JWT token for user authentication"""
    return create_access_token(data={"id": str(test_user.id), "role": "user", "tenant_id": str(test_user.tenant_id)})

@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up database after each test"""
    yield
    # Clean up all data after each test
    try:
        # Delete data in reverse dependency order
        db = TestingSessionLocal()
        try:
            db.execute(text("DELETE FROM bookings"))
            db.execute(text("DELETE FROM vehicles"))
            db.execute(text("DELETE FROM drivers"))
            db.execute(text("DELETE FROM users"))
            db.execute(text("DELETE FROM tenants"))
            db.commit()
        finally:
            db.close()
    except Exception:
        # If cleanup fails, recreate tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine) 