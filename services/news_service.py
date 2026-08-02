"""
News service.

WHY DATABASE-BACKED CACHING (not in-memory):
The news_cache table built in the database phase is used here for
real caching — unlike an in-memory dict, this survives app restarts
and works correctly even if the app runs as multiple worker processes
(e.g. under gunicorn in production), where each process would
otherwise keep its own separate in-memory cache.

NewsAPI's official top-headlines `category` values are only:
    business, entertainment, general, health, science, sports, technology
Categories outside that list (cricket, football, startups, AI, etc.)
fall through to keyword search against /v2/everything instead.
"""

import json
from datetime import datetime, timedelta

import requests
from flask import current_app

from database import db
from models.news_cache import NewsCache

NEWSAPI_BASE_URL = "https://newsapi.org/v2"

NATIVE_CATEGORIES = {
    "business", "entertainment", "general", "health", "science", "sports", "technology"
}

KEYWORD_CATEGORY_MAP = {
    "world": "world news",
    "cricket": "cricket",
    "football": "football",
    "education": "education",
    "politics": "politics",
    "finance": "finance",
    "economy": "economy",
    "startup": "startup",
    "artificial intelligence": "artificial intelligence",
    "environment": "climate environment",
    "travel": "travel",
    "lifestyle": "lifestyle",
    "food": "food",
    "movies": "movies",
}


def _cache_get(cache_key):
    entry = NewsCache.query.filter_by(cache_key=cache_key).first()
    if not entry:
        return None
    if entry.expires_at < datetime.utcnow():
        db.session.delete(entry)
        db.session.commit()
        return None
    return json.loads(entry.response_json)


def _cache_set(cache_key, payload):
    ttl_seconds = current_app.config.get("NEWS_CACHE_TTL_SECONDS", 300)
    existing = NewsCache.query.filter_by(cache_key=cache_key).first()
    if existing:
        existing.response_json = json.dumps(payload)
        existing.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    else:
        db.session.add(NewsCache(
            cache_key=cache_key,
            response_json=json.dumps(payload),
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds),
        ))
    db.session.commit()


def _normalize_articles(raw_articles):
    normalized = []
    for a in raw_articles:
        if not a.get("title") or a.get("title") == "[Removed]":
            continue
        normalized.append({
            "title": a.get("title"),
            "description": a.get("description") or "",
            "source": (a.get("source") or {}).get("name", "Unknown Source"),
            "author": a.get("author") or "Unknown",
            "category": None,
            "published": a.get("publishedAt", ""),
            "reading_time": _estimate_reading_time(a.get("content") or a.get("description") or ""),
            "image": a.get("urlToImage") or "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=800",
            "url": a.get("url", "#"),
        })
    return normalized


def _estimate_reading_time(text):
    words = max(len(text.split()), 1)
    minutes = max(round(words / 200), 1)
    return f"{minutes} min read"


def _request(endpoint, params):
    api_key = current_app.config.get("NEWSAPI_KEY")
    if not api_key:
        return {"ok": False, "error": "missing_key", "articles": []}

    cache_key = f"{endpoint}:{sorted(params.items())}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            f"{NEWSAPI_BASE_URL}/{endpoint}",
            params={**params, "apiKey": api_key},
            timeout=8,
        )
        data = resp.json()

        if resp.status_code != 200 or data.get("status") != "ok":
            return {
                "ok": False,
                "error": data.get("message", f"NewsAPI returned status {resp.status_code}"),
                "articles": [],
            }

        result = {
            "ok": True,
            "error": None,
            "articles": _normalize_articles(data.get("articles", [])),
            "total_results": data.get("totalResults", 0),
        }
        _cache_set(cache_key, result)
        return result

    except requests.exceptions.RequestException as exc:
        return {"ok": False, "error": f"Network error: {exc}", "articles": []}


def get_top_headlines(category=None, country="us", page=1, page_size=12):
    category = (category or "general").lower()

    if category in NATIVE_CATEGORIES:
        return _request("top-headlines", {
            "category": category, "country": country, "page": page, "pageSize": page_size,
        })

    keyword = KEYWORD_CATEGORY_MAP.get(category, category)
    return search_news(query=keyword, page=page, page_size=page_size)


def search_news(query, category=None, country=None, page=1, page_size=12):
    q = query or "world news"
    if category and category.lower() not in NATIVE_CATEGORIES:
        q = f"{q} {KEYWORD_CATEGORY_MAP.get(category.lower(), category)}"

    return _request("everything", {
        "q": q, "language": "en", "sortBy": "publishedAt", "page": page, "pageSize": page_size,
    })