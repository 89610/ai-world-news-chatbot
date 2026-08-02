"""
Bookmark blueprint.

    GET    /api/bookmarks         — list the logged-in user's saved articles
    POST   /api/bookmarks         — save an article
    DELETE /api/bookmarks/<id>    — remove a saved article
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from database import db
from models.bookmark import Bookmark

bookmark_bp = Blueprint("bookmark", __name__, url_prefix="/api/bookmarks")


@bookmark_bp.route("", methods=["GET"])
@login_required
def list_bookmarks():
    rows = (
        Bookmark.query
        .filter_by(user_id=current_user.id)
        .order_by(Bookmark.saved_at.desc())
        .all()
    )
    return jsonify({
        "ok": True,
        "bookmarks": [
            {
                "id": b.id,
                "title": b.article_title,
                "url": b.article_url,
                "image": b.article_image,
                "source": b.source_name,
                "saved_at": b.saved_at.isoformat(),
            }
            for b in rows
        ],
    })


@bookmark_bp.route("", methods=["POST"])
@login_required
def add_bookmark():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    url = (payload.get("url") or "").strip()

    if not title or not url:
        return jsonify({"ok": False, "error": "title and url are required."}), 400

    existing = Bookmark.query.filter_by(user_id=current_user.id, article_url=url).first()
    if existing:
        return jsonify({"ok": True, "already_saved": True, "id": existing.id})

    bookmark = Bookmark(
        user_id=current_user.id,
        article_title=title,
        article_url=url,
        article_image=payload.get("image"),
        source_name=payload.get("source"),
    )
    db.session.add(bookmark)
    db.session.commit()

    return jsonify({"ok": True, "id": bookmark.id})


@bookmark_bp.route("/<int:bookmark_id>", methods=["DELETE"])
@login_required
def remove_bookmark(bookmark_id):
    bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=current_user.id).first()
    if not bookmark:
        return jsonify({"ok": False, "error": "Bookmark not found."}), 404

    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({"ok": True})