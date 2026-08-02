"""Tests for the auth flow: register, login, logout."""

import re


def get_csrf_token(client, path):
    resp = client.get(path)
    return re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode()).group(1)


def test_register_creates_account(client):
    token = get_csrf_token(client, "/auth/register")
    resp = client.post("/auth/register", data={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123",
        "csrf_token": token,
    }, follow_redirects=True)
    assert resp.status_code == 200
    # After registering, Flask-Login logs the user in automatically —
    # the navbar should now show their username instead of "Sign In".
    assert b"newuser" in resp.data


def test_register_rejects_short_password(client):
    token = get_csrf_token(client, "/auth/register")
    resp = client.post("/auth/register", data={
        "username": "shortpw",
        "email": "shortpw@example.com",
        "password": "abc",
        "csrf_token": token,
    })
    assert b"at least 6 characters" in resp.data


def test_register_rejects_duplicate_username(client, registered_user):
    # registered_user fixture leaves the client logged in, and the
    # register page redirects logged-in visitors away — log out first
    # so we can actually reach the registration form again.
    client.post("/auth/logout", data={"csrf_token": get_csrf_token(client, "/")})

    token = get_csrf_token(client, "/auth/register")
    resp = client.post("/auth/register", data={
        "username": registered_user["username"],
        "email": "different@example.com",
        "password": "password123",
        "csrf_token": token,
    })
    assert b"already taken" in resp.data


def test_login_with_correct_credentials(client, registered_user):
    # Log out first (registered_user fixture leaves us logged in)
    client.post("/auth/logout", data={"csrf_token": get_csrf_token(client, "/")})

    token = get_csrf_token(client, "/auth/login")
    resp = client.post("/auth/login", data={
        "identifier": registered_user["username"],
        "password": registered_user["password"],
        "csrf_token": token,
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert registered_user["username"].encode() in resp.data


def test_login_rejects_wrong_password(client, registered_user):
    client.post("/auth/logout", data={"csrf_token": get_csrf_token(client, "/")})

    token = get_csrf_token(client, "/auth/login")
    resp = client.post("/auth/login", data={
        "identifier": registered_user["username"],
        "password": "wrongpassword",
        "csrf_token": token,
    })
    assert b"Invalid username/email or password" in resp.data


def test_logout_redirects_to_home(client, registered_user):
    token = get_csrf_token(client, "/")
    resp = client.post("/auth/logout", data={"csrf_token": token}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Sign In" in resp.data
