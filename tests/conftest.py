"""
Shared pytest fixtures.

Every test runs against the "testing" config (in-memory SQLite, see
config.py's TestingConfig), so tests never touch your real MySQL
database — safe to run anytime without affecting real data.
"""

import pytest
from app import create_app
from database import db


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def registered_user(client):
    """Registers a test user and returns their credentials. The client
    fixture keeps its session cookie, so the caller is already logged
    in after using this fixture."""
    import re

    resp = client.get("/auth/register")
    token = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode()).group(1)

    client.post("/auth/register", data={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "password123",
        "csrf_token": token,
    })

    return {"username": "testuser", "email": "testuser@example.com", "password": "password123"}
