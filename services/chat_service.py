"""
Chat service.

WHY GROUNDED IN LIVE ARTICLES:
Gemini's own training data goes stale — for a question like "what's
today's top business news," answering from training data would be
wrong or outdated. Instead, every question is first used as a search
query against NewsAPI (via news_service.py), and Gemini is instructed
to answer ONLY using those freshly-fetched articles, citing sources.

Uses Gemini's REST API directly via `requests` (already a dependency)
rather than adding the google-generativeai SDK — one less package for
a call this simple.
"""

import requests
from flask import current_app
from services import news_service

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_INSTRUCTION = """You are the AI News Assistant for "AI World News Chatbot", \
a news dashboard. You answer questions using ONLY the news articles provided \
to you in each message — never your own general knowledge of current events, \
since your training data may be outdated.

Rules:
- Base your answer strictly on the provided articles.
- Always mention which source(s) you're drawing from by name (e.g. "According to Reuters...").
- If the provided articles don't actually answer the question, say so plainly \
  and suggest the person try a more specific search instead of guessing.
- Keep answers concise: 2-4 sentences for a summary, unless the person is asking \
  for more detail.
- Never fabricate facts, quotes, or figures not present in the supplied articles.
- Be conversational and helpful, not robotic."""


def _build_context_block(articles):
    if not articles:
        return "No articles were found for this query."

    lines = []
    for i, a in enumerate(articles[:5], start=1):
        lines.append(
            f"{i}. \"{a['title']}\" — {a['source']} ({a['published']})\n"
            f"   {a['description']}\n"
            f"   URL: {a['url']}"
        )
    return "\n".join(lines)


def generate_reply(user_message: str):
    """Returns (reply_text, sources_list, error_or_None)."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return None, [], "missing_key"

    search_result = news_service.search_news(query=user_message, page_size=5)
    articles = search_result.get("articles", []) if search_result.get("ok") else []
    context_block = _build_context_block(articles)

    model = current_app.config.get("CHATBOT_MODEL", "gemini-flash-latest")
    url = f"{GEMINI_BASE_URL}/{model}:generateContent"

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{
            "role": "user",
            "parts": [{
                "text": (
                    f"User question: {user_message}\n\n"
                    f"Available articles:\n{context_block}"
                ),
            }],
        }],
        "generationConfig": {
            # Newer Gemini models "think" before answering, and those
            # thinking tokens share the same budget as the final reply
            # — without capping thinking, a modest maxOutputTokens can
            # be entirely consumed by thinking, leaving an empty reply.
            "thinkingConfig": {"thinkingLevel": "low"},
            "maxOutputTokens": 1024,
        },
    }

    try:
        resp = requests.post(url, params={"key": api_key}, json=payload, timeout=15)
        data = resp.json()

        if resp.status_code != 200:
            error_message = (data.get("error") or {}).get("message", f"Gemini returned status {resp.status_code}")
            return None, [], f"Chatbot error: {error_message}"

        candidates = data.get("candidates", [])
        if not candidates:
            return None, [], "Chatbot error: no response generated."

        parts = candidates[0].get("content", {}).get("parts", [])
        reply_text = "".join(p.get("text", "") for p in parts).strip()
        finish_reason = candidates[0].get("finishReason", "")

        if not reply_text:
            if finish_reason == "MAX_TOKENS":
                return None, [], "Chatbot error: response got cut off (ran out of token budget)."
            return None, [], "Chatbot error: empty response."

        return reply_text, articles[:5], None

    except requests.exceptions.RequestException as exc:
        return None, [], f"Chatbot error: {exc}"