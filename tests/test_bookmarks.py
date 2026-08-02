"""Tests for the bookmarks feature. Requires a logged-in user."""


def test_add_bookmark_requires_login(client):
    resp = client.post("/api/bookmarks", json={"title": "x", "url": "http://x.com"})
    assert resp.status_code == 401
    assert resp.get_json()["auth_required"] is True


def test_add_and_list_bookmark(client, registered_user):
    resp = client.post("/api/bookmarks", json={
        "title": "Test Article",
        "url": "http://example.com/article",
        "source": "Test Source",
    })
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

    resp = client.get("/api/bookmarks")
    data = resp.get_json()
    assert data["ok"] is True
    assert len(data["bookmarks"]) == 1
    assert data["bookmarks"][0]["title"] == "Test Article"


def test_bookmarking_same_url_twice_does_not_duplicate(client, registered_user):
    payload = {"title": "Dup", "url": "http://example.com/dup", "source": "X"}
    client.post("/api/bookmarks", json=payload)
    client.post("/api/bookmarks", json=payload)

    resp = client.get("/api/bookmarks")
    assert len(resp.get_json()["bookmarks"]) == 1


def test_remove_bookmark(client, registered_user):
    add_resp = client.post("/api/bookmarks", json={
        "title": "To Remove", "url": "http://example.com/remove", "source": "X",
    })
    bookmark_id = add_resp.get_json()["id"]

    del_resp = client.delete(f"/api/bookmarks/{bookmark_id}")
    assert del_resp.status_code == 200
    assert del_resp.get_json()["ok"] is True

    list_resp = client.get("/api/bookmarks")
    assert len(list_resp.get_json()["bookmarks"]) == 0


def test_add_bookmark_missing_fields(client, registered_user):
    resp = client.post("/api/bookmarks", json={"title": "No URL"})
    assert resp.status_code == 400
