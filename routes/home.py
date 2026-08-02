"""
Home blueprint.

WHY THIS FILE EXISTS:
Renders the base layout plus real, live top headlines from NewsAPI.
If no API key is configured yet, or the request fails for any reason
(quota, network), falls back to curated demo articles so the page
never looks broken. All interactive requests (search, category
clicks, infinite scroll) go through the JSON endpoints in
routes/news.py instead, handled by static/js/news.js.
"""

from flask import Blueprint, render_template
from flask_login import login_required
from services import news_service

home_bp = Blueprint("home", __name__)

DEMO_ARTICLES = [
    {
        "title": "Global Markets Rally as Inflation Data Eases",
        "description": "Investors respond positively to the latest consumer price index figures, "
                        "with major indices posting gains across Asia, Europe, and the US.",
        "source": "World Business Daily",
        "author": "R. Kapoor",
        "category": "Business",
        "published": "2 hours ago",
        "reading_time": "3 min read",
        "image": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=800",
        "url": "#",
    },
    {
        "title": "Breakthrough Announced in Fusion Energy Research",
        "description": "Scientists report a significant efficiency milestone that could accelerate "
                        "the path toward commercially viable fusion power plants.",
        "source": "Global Science Report",
        "author": "M. Chen",
        "category": "Technology",
        "published": "5 hours ago",
        "reading_time": "4 min read",
        "image": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800",
        "url": "#",
    },
    {
        "title": "India Clinches Series Win in Final Over Thriller",
        "description": "A last-ball six sealed a memorable victory, capping off a tightly "
                        "contested series watched by millions.",
        "source": "SportsWire",
        "author": "A. Sharma",
        "category": "Cricket",
        "published": "1 day ago",
        "reading_time": "2 min read",
        "image": "https://images.unsplash.com/photo-1531415074968-036ba1b575da?q=80&w=800",
        "url": "#",
    },
]

TOP_CATEGORIES = [
    ("bx-world", "World"),
    ("bx-briefcase", "Business"),
    ("bx-chip", "Technology"),
    ("bx-cricket-ball", "Cricket"),
    ("bx-football", "Football"),
    ("bx-book-open", "Education"),
    ("bx-heart", "Health"),
    ("bx-leaf", "Environment"),
    ("bx-buildings", "Politics"),
    ("bx-dollar-circle", "Finance"),
    ("bx-rocket", "Startup"),
    ("bx-bot", "Artificial Intelligence"),
    ("bx-map", "Travel"),
    ("bx-coffee", "Lifestyle"),
    ("bx-restaurant", "Food"),
    ("bx-camera-movie", "Movies"),
]


@home_bp.route("/")
def index():
    result = news_service.get_top_headlines(category="general", country="us", page=1, page_size=6)

    if result["ok"] and result["articles"]:
        articles = result["articles"]
        using_demo_data = False
    else:
        articles = DEMO_ARTICLES
        using_demo_data = True

    return render_template(
        "index.html",
        articles=articles,
        categories=TOP_CATEGORIES,
        using_demo_data=using_demo_data,
        api_error=result.get("error") if using_demo_data else None,
    )

@home_bp.route("/about")
def about_page():
    return render_template("about.html")


@home_bp.route("/bookmarks")
@login_required
def bookmarks_page():
    return render_template("bookmarks.html")