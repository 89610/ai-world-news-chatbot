"""Tests for the newsletter subscribe endpoint."""


def test_subscribe_with_valid_email(client):
    resp = client.post("/api/newsletter/subscribe", json={"email": "reader@example.com"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    # No MAIL_USERNAME configured in testing — email sending should
    # fail gracefully while the subscription itself still succeeds.
    assert data["email_sent"] is False


def test_subscribe_rejects_invalid_email(client):
    resp = client.post("/api/newsletter/subscribe", json={"email": "not-an-email"})
    assert resp.status_code == 400


def test_subscribe_twice_reports_already_subscribed(client):
    client.post("/api/newsletter/subscribe", json={"email": "dup@example.com"})
    resp = client.post("/api/newsletter/subscribe", json={"email": "dup@example.com"})
    assert resp.get_json()["already_subscribed"] is True


def test_subscriber_is_actually_stored(client, app):
    from models.newsletter import NewsletterSubscriber

    client.post("/api/newsletter/subscribe", json={"email": "stored@example.com"})

    with app.app_context():
        subscriber = NewsletterSubscriber.query.filter_by(email="stored@example.com").first()
        assert subscriber is not None
