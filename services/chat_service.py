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

WHY RETRY + FALLBACK:
Gemini sometimes returns 503 ("model is experiencing high demand") or 429
(rate limit). These are temporary, so we retry once on the preferred model,
then fall back to other current Gemini models before showing an error.
Every failed attempt is logged to the terminal with its real status code.
"""

import time

import requests
from flask import current_app
from services import news_service

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Tried in order after the preferred model (CHATBOT_MODEL) fails.
# Gemini 2.0 is shut down and 2.5 is restricted, so use the 3.x family.
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]

# HTTP statuses that mean "temporary problem — trying again can work".
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

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


def _generation_config(use_thinking: bool) -> dict:
    """
    Thinking tokens share the output budget, so keep thinking low to avoid an
    empty reply. If a model rejects the thinking setting, _call_gemini retries
    that model once with use_thinking=False.
    """
    config = {"maxOutputTokens": 1024}
    if use_thinking:
        config["thinkingConfig"] = {"thinkingLevel": "low"}
    return config


def _call_gemini(payload_base: dict, api_key: str, preferred_model: str):
    """
    Calls Gemini with retry + model fallback.
    Returns (response_json, None) on success, or (None, error_message) on failure.
    """
    logger = current_app.logger
    models = [preferred_model] + [m for m in FALLBACK_MODELS if m != preferred_model]
    seen_statuses = set()

    for index, model in enumerate(models):
        url = f"{GEMINI_BASE_URL}/{model}:generateContent"
        max_attempts = 1  # fallback models already cover retries; keep waits short
        use_thinking = True
        attempt = 0

        while attempt < max_attempts:
            payload = dict(payload_base)
            payload["generationConfig"] = _generation_config(use_thinking)

            try:
                resp = requests.post(url, params={"key": api_key}, json=payload, timeout=12)
            except requests.exceptions.RequestException as exc:
                logger.warning("Gemini [%s] network error: %s", model, exc)
                seen_statuses.add(0)
                attempt += 1
                time.sleep(1)
                continue

            if resp.status_code == 200:
                try:
                    return resp.json(), None
                except ValueError:
                    logger.warning("Gemini [%s] returned invalid JSON", model)
                    seen_statuses.add(200)
                    break

            try:
                error_text = (resp.json().get("error") or {}).get("message", "")
            except ValueError:
                error_text = resp.text[:200]
            logger.warning("Gemini [%s] -> HTTP %s: %s", model, resp.status_code, error_text)
            seen_statuses.add(resp.status_code)

            # Model rejected the thinking setting: retry same model without it.
            if resp.status_code == 400 and use_thinking and "think" in error_text.lower():
                use_thinking = False
                continue

            if resp.status_code not in RETRYABLE_STATUS:
                break  # e.g. 404 model gone, 403 bad key: move to the next model

            attempt += 1
            if attempt < max_attempts:
                time.sleep(1.5)

    if seen_statuses & {401, 403}:
        return None, "Chatbot error: the Gemini API key was rejected. Check GEMINI_API_KEY in your .env file."
    if 429 in seen_statuses:
        return None, "Chatbot error: the free AI limit was reached. Please try again in a few minutes."
    if seen_statuses == {404}:
        return None, "Chatbot error: the AI model is unavailable. Check CHATBOT_MODEL in your settings."
    return None, "Chatbot error: the AI is very busy right now. Please try again in a minute."


def generate_reply(user_message: str):
    """Returns (reply_text, sources_list, error_or_None)."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return None, [], "missing_key"

    search_result = news_service.search_news(query=user_message, page_size=5)
    articles = search_result.get("articles", []) if search_result.get("ok") else []
    context_block = _build_context_block(articles)

    model = current_app.config.get("CHATBOT_MODEL", "gemini-flash-latest")

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
    }

    data, error = _call_gemini(payload, api_key, model)
    if error:
        return None, [], error

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