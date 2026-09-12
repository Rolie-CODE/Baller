import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from main import app, get_db
import models

# Use in-memory SQLite database for isolated automated testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello Rolie" in response.json()["message"]


def test_register_user_success(client):
    payload = {
        "username": "kobebryant",
        "email": "kobe@lakers.com",
        "password": "mambamentality"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "kobebryant"
    assert data["email"] == "kobe@lakers.com"
    assert data["role"] == "PLAYER"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    # Ensure sensitive fields are NEVER leaked
    assert "password" not in data
    assert "password_hash" not in data


def test_register_coach_success(client):
    payload = {
        "username": "coachpop",
        "email": "pop@spurs.com",
        "password": "championships5",
        "role": "COACH"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "COACH"
    assert data["username"] == "coachpop"


def test_register_admin_rejected(client):
    payload = {
        "username": "fakeadmin",
        "email": "fakeadmin@platform.com",
        "password": "hackerpassword",
        "role": "ADMIN"
    }
    response = client.post("/auth/register", json=payload)
    # Rejects unauthorized role selection at API boundary
    assert response.status_code == 422


def test_register_duplicate_email(client):
    payload1 = {
        "username": "player1",
        "email": "same@example.com",
        "password": "password123"
    }
    client.post("/auth/register", json=payload1)

    payload2 = {
        "username": "player2",
        "email": "same@example.com",
        "password": "password456"
    }
    response = client.post("/auth/register", json=payload2)
    assert response.status_code == 409
    assert "Email is already registered" in response.json()["detail"]


def test_register_duplicate_username(client):
    payload1 = {
        "username": "samename",
        "email": "first@example.com",
        "password": "password123"
    }
    client.post("/auth/register", json=payload1)

    payload2 = {
        "username": "samename",
        "email": "second@example.com",
        "password": "password456"
    }
    response = client.post("/auth/register", json=payload2)
    assert response.status_code == 409
    assert "Username is already taken" in response.json()["detail"]


def test_register_invalid_email(client):
    payload = {
        "username": "validuser",
        "email": "not-an-email",
        "password": "password123"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_register_short_password(client):
    payload = {
        "username": "validuser",
        "email": "user@example.com",
        "password": "123"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_login_with_username_and_email(client):
    reg_payload = {
        "username": "stephcurry",
        "email": "steph@warriors.com",
        "password": "splashbrother"
    }
    client.post("/auth/register", json=reg_payload)

    # 1. Login with username
    login_user_res = client.post("/auth/login", json={
        "username": "stephcurry",
        "password": "splashbrother"
    })
    assert login_user_res.status_code == 200
    assert "access_token" in login_user_res.json()
    assert login_user_res.json()["token_type"] == "bearer"

    # 2. Login with email
    login_email_res = client.post("/auth/login", json={
        "email": "steph@warriors.com",
        "password": "splashbrother"
    })
    assert login_email_res.status_code == 200
    assert "access_token" in login_email_res.json()

    # 3. Login using username_or_email field
    login_field_res = client.post("/auth/login", json={
        "username_or_email": "stephcurry",
        "password": "splashbrother"
    })
    assert login_field_res.status_code == 200
    assert "access_token" in login_field_res.json()


def test_login_invalid_password(client):
    reg_payload = {
        "username": "lebronjames",
        "email": "lebron@lakers.com",
        "password": "kingjames23"
    }
    client.post("/auth/register", json=reg_payload)

    response = client.post("/auth/login", json={
        "username": "lebronjames",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Invalid email/username or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={
        "username": "nobody",
        "password": "password123"
    })
    assert response.status_code == 401


def test_get_me_authenticated_and_unauthenticated(client):
    reg_payload = {
        "username": "giannis",
        "email": "greekfreak@bucks.com",
        "password": "freaktime34"
    }
    client.post("/auth/register", json=reg_payload)

    # Login to get token
    login_res = client.post("/auth/login", json={
        "username": "giannis",
        "password": "freaktime34"
    })
    token = login_res.json()["access_token"]

    # 1. Access /auth/me with valid Bearer token
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["username"] == "giannis"
    assert data["email"] == "greekfreak@bucks.com"
    assert data["role"] == "PLAYER"

    # 2. Access /auth/me without token -> 401
    unauth_res = client.get("/auth/me")
    assert unauth_res.status_code == 401

    # 3. Access /auth/me with invalid token -> 401
    bad_token_res = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert bad_token_res.status_code == 401

