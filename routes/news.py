"""
News blueprint.

    GET /api/news/top-headlines?category=&country=&page=
    GET /api/news/search?q=&category=&country=&page=

Kept as a JSON API (not server-rendered pages) so the frontend can
drive search, category switching, and infinite scroll without a full
page reload.
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user

from database import db
from models.history import SearchHistory
from services import news_service

news_bp = Blueprint("news", __name__, url_prefix="/api/news")


def _log_search(query=None, category=None, country=None):
    """Best-effort logging — a failed log write should never break search."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        db.session.add(SearchHistory(user_id=user_id, search_query=query or "", category=category, country=country))
        db.session.commit()
    except Exception:
        db.session.rollback()


@news_bp.route("/top-headlines")
def top_headlines():
    category = request.args.get("category", "general")
    country = request.args.get("country", "us")
    page = request.args.get("page", 1, type=int)

    result = news_service.get_top_headlines(category=category, country=country, page=page)
    _log_search(category=category, country=country)
    return jsonify(result), (200 if result["ok"] else 502)


@news_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category")
    country = request.args.get("country")
    page = request.args.get("page", 1, type=int)

    if not query:
        return jsonify({"ok": False, "error": "Search query is required.", "articles": []}), 400

    result = news_service.search_news(query=query, category=category, country=country, page=page)
    _log_search(query=query, category=category, country=country)
    return jsonify(result), (200 if result["ok"] else 502)