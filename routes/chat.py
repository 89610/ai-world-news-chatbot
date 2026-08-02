"""
Chat blueprint.

    POST /api/chat/message   — send a message, get Gemini's reply + sources
    GET  /api/chat/history   — restore a conversation by session_id
"""

from flask import Blueprint, request, jsonify
from database import db
from models.history import ChatHistory
from services import chat_service

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.route("/message", methods=["POST"])
def send_message():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    session_id = (payload.get("session_id") or "").strip()

    if not message:
        return jsonify({"ok": False, "error": "Message is required."}), 400
    if not session_id:
        return jsonify({"ok": False, "error": "session_id is required."}), 400

    db.session.add(ChatHistory(session_id=session_id, role="user", message=message))
    db.session.commit()

    reply_text, sources, error = chat_service.generate_reply(message)

    if error:
        friendly = (
            "The chatbot isn't configured yet — add a valid GEMINI_API_KEY to .env and restart the app."
            if error == "missing_key" else error
        )
        return jsonify({"ok": False, "error": friendly}), 502

    db.session.add(ChatHistory(session_id=session_id, role="assistant", message=reply_text))
    db.session.commit()

    return jsonify({
        "ok": True,
        "reply": reply_text,
        "sources": [
            {"title": s["title"], "source": s["source"], "url": s["url"]}
            for s in sources
        ],
    })


@chat_bp.route("/history")
def get_history():
    session_id = request.args.get("session_id", "").strip()
    if not session_id:
        return jsonify({"ok": False, "error": "session_id is required.", "messages": []}), 400

    rows = (
        ChatHistory.query
        .filter_by(session_id=session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    return jsonify({
        "ok": True,
        "messages": [{"role": r.role, "message": r.message} for r in rows],
    })