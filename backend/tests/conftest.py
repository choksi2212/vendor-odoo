"""
Shared pytest fixtures for the VendorBridge test suite.

Uses an in-memory SQLite database for fast, isolated tests.
Each test gets a fresh database to prevent test pollution.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User, UserRole  # This import triggers all model loading via models/__init__.py

# In-memory SQLite for testing (fast, no external dependencies)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable foreign key enforcement for SQLite (disabled by default)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter storage before each test to avoid 429 errors."""
    from app.core.security import limiter
    limiter.reset()
    # Disable rate limiting entirely during tests
    limiter.enabled = False
    yield
    limiter.enabled = True


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


def _create_user(db_session, email, username, password, role, is_verified=True):
    """Helper to create a user for testing."""
    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        role=role,
        is_verified=is_verified,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user(db_session):
    """Create a verified procurement officer user."""
    return _create_user(
        db_session,
        email="officer@vendorbridge.com",
        username="officer",
        password="OfficerPass123!",
        role=UserRole.PROCUREMENT_OFFICER,
    )


@pytest.fixture
def test_vendor_user(db_session):
    """Create a verified vendor user."""
    return _create_user(
        db_session,
        email="vendor@vendorbridge.com",
        username="vendoruser",
        password="VendorPass123!",
        role=UserRole.VENDOR,
    )


@pytest.fixture
def test_manager_user(db_session):
    """Create a verified manager user."""
    return _create_user(
        db_session,
        email="manager@vendorbridge.com",
        username="manager",
        password="ManagerPass123!",
        role=UserRole.MANAGER,
    )


@pytest.fixture
def test_admin_user(db_session):
    """Create a verified admin user."""
    return _create_user(
        db_session,
        email="admin@vendorbridge.com",
        username="admin",
        password="AdminPass123!",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def unverified_user(db_session):
    """Create an unverified user."""
    return _create_user(
        db_session,
        email="unverified@vendorbridge.com",
        username="unverified",
        password="Unverified123!",
        role=UserRole.PROCUREMENT_OFFICER,
        is_verified=False,
    )


@pytest.fixture
def auth_headers(test_user):
    """Generate auth headers for procurement officer."""
    access_token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def vendor_auth_headers(test_vendor_user):
    """Generate auth headers for vendor user."""
    access_token = create_access_token(str(test_vendor_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def manager_auth_headers(test_manager_user):
    """Generate auth headers for manager user."""
    access_token = create_access_token(str(test_manager_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user):
    """Generate auth headers for admin user."""
    access_token = create_access_token(str(test_admin_user.id))
    return {"Authorization": f"Bearer {access_token}"}
