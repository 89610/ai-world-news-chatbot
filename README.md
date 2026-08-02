# AI World News Chatbot

Real-time world news dashboard + AI chatbot. This delivery is
the project foundation — a clean, runnable Flask
foundation with the full folder structure, base design system, and
navbar/footer, ready for every later phase to build on.

## Quick start

```bash
cd project
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Visit **http://localhost:5000**. No MySQL server needed yet — leaving
`MYSQL_PASSWORD` blank in `.env` falls back to a local SQLite file
(`dev.db`) so the app runs immediately.

## Why each file exists

| File | Purpose |
|---|---|
| `app.py` | Application factory — creates the Flask app, loads config, registers blueprints and error handlers. Factory pattern (not a bare `app = Flask(...)`) so the same code can run under dev/test/prod configs and is testable with pytest. |
| `config.py` | Reads all secrets (DB credentials, API keys) from environment variables via `.env` — nothing sensitive is ever hardcoded. |
| `database.py` | Defines the shared `db` (SQLAlchemy) and `migrate` (Flask-Migrate) objects separately from `app.py`, so `models/` can import `db` without a circular import. |
| `requirements.txt` | Full dependency list for the whole project's planned phases, installed once up front. |
| `.env.example` | Template for local secrets — copy to `.env`, which is git-ignored. |
| `.gitignore` | Keeps `.env`, virtual envs, `__pycache__`, and local DB files out of version control. |
| `routes/home.py` | The current only route — renders the base layout. |
| `templates/base.html` | Shared layout (navbar, footer, fonts, Bootstrap) every page extends. |
| `templates/index.html` | Home page — currently a placeholder hero, since live news (Phase 4) and the chatbot (Phase 5) don't exist yet. |
| `templates/404.html` / `500.html` | Error pages matching the site's design instead of Flask's default plain-text errors. |
| `static/css/style.css` | The design system — CSS variables for the color palette, buttons, navbar, glassmorphism cards. |
| `static/css/responsive.css` | Mobile/tablet breakpoint overrides, kept separate from the main stylesheet. |
| `static/js/app.js` | Dark/light mode toggle — the only interactive behavior needed so far. |
| `models/`, `services/`, `utils/` | Empty for now — populated starting Phase 2 (models), Phase 4 (services for news/chat API calls), and as needed (utils for shared helpers). |
| `migrations/` | Empty — Flask-Migrate will populate this once `flask db init` runs in Phase 2. |

## Roadmap

| Phase | Scope |
|---|---|
| 2 | Database design — users, bookmarks, chat_history, search_history, news_cache tables |
| 3 | Authentication — register/login/logout, password hashing, protected routes |
| 4 | News module — live NewsAPI/GNews/Guardian integration, search, categories |
| 5 | AI Chatbot — Gemini-powered, grounded in live articles |
| 6 | User features — bookmarks, dark mode (already built), newsletter |
| 7 | UI polish — animations, toasts, skeletons, back-to-top |
| 8 | Testing, optimization, deployment |

## Verifying it works

```bash
python app.py
```
Visit `/` — you should see the navbar, a placeholder hero section
with a "Stay informed with news that talks back" heading, a disabled
chatbot preview card, and a footer. Try the dark mode toggle (moon
icon, top right) — it should switch themes and persist on reload.
Visit a nonexistent URL (e.g. `/xyz`) — you should see a styled 404
page, not Flask's default error page.
