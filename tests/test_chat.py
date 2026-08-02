"""
Tests for the AI chatbot endpoint.

No GEMINI_API_KEY is set in testing config, so these verify the app's
own validation and error handling — not real Gemini responses.
"""


def test_chat_requires_message(client):
    resp = client.post("/api/chat/message", json={"session_id": "test-session"})
    assert resp.status_code == 400


def test_chat_requires_session_id(client):
    resp = client.post("/api/chat/message", json={"message": "hello"})
    assert resp.status_code == 400


def test_chat_without_api_key_fails_gracefully(client):
    resp = client.post("/api/chat/message", json={
        "message": "latest news",
        "session_id": "test-session",
    })
    assert resp.status_code == 502
    data = resp.get_json()
    assert data["ok"] is False
    assert "GEMINI_API_KEY" in data["error"]


def test_user_message_is_saved_even_when_ai_call_fails(client, app):
    """The user's message should persist in chat_history even if the
    Gemini call fails afterward — losing what someone typed is worse
    than a failed AI response."""
    from models.history import ChatHistory

    client.post("/api/chat/message", json={
        "message": "what happened today",
        "session_id": "persist-test",
    })

    with app.app_context():
        rows = ChatHistory.query.filter_by(session_id="persist-test").all()
        assert len(rows) == 1
        assert rows[0].role == "user"
        assert rows[0].message == "what happened today"


def test_chat_history_endpoint_requires_session_id(client):
    resp = client.get("/api/chat/history")
    assert resp.status_code == 400


def test_chat_history_returns_saved_messages(client):
    client.post("/api/chat/message", json={"message": "hi", "session_id": "history-test"})
    resp = client.get("/api/chat/history?session_id=history-test")
    data = resp.get_json()
    assert data["ok"] is True
    assert len(data["messages"]) >= 1
