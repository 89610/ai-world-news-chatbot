"""Tests for pages that don't require login."""


def test_home_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"AI World News Chatbot" in resp.data or b"talks back" in resp.data


def test_about_page_loads(client):
    resp = client.get("/about")
    assert resp.status_code == 200


def test_contact_page_loads(client):
    resp = client.get("/contact")
    assert resp.status_code == 200


def test_privacy_page_loads(client):
    resp = client.get("/privacy")
    assert resp.status_code == 200


def test_404_page(client):
    resp = client.get("/this-page-does-not-exist")
    assert resp.status_code == 404


def test_bookmarks_page_requires_login(client):
    """Anonymous visitors should be redirected to login, not shown the page."""
    resp = client.get("/bookmarks", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
