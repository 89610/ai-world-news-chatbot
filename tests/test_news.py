"""
Tests for the news search/category endpoints.

These don't hit the real NewsAPI (no key is configured in the testing
config), so they verify the app's own logic: input validation and
graceful degradation when the external API can't be reached — not
NewsAPI's actual search results.
"""


def test_search_requires_query(client):
    resp = client.get("/api/news/search")
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_search_without_api_key_fails_gracefully(client):
    """No NEWSAPI_KEY is set in testing config — the app should return
    a clean JSON error, never a 500 crash."""
    resp = client.get("/api/news/search?q=technology")
    assert resp.status_code == 502
    data = resp.get_json()
    assert data["ok"] is False
    assert data["articles"] == []


def test_top_headlines_without_api_key_fails_gracefully(client):
    resp = client.get("/api/news/top-headlines?category=business")
    assert resp.status_code == 502
    data = resp.get_json()
    assert data["ok"] is False


def test_search_logs_to_history_even_when_api_call_fails(client, app):
    """Search history logging shouldn't depend on the external API
    succeeding — it should record the attempted query either way."""
    from models.history import SearchHistory

    client.get("/api/news/search?q=cricket")

    with app.app_context():
        rows = SearchHistory.query.filter_by(search_query="cricket").all()
        assert len(rows) == 1
