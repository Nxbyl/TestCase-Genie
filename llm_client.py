"""
llm_client.py — Isolated LLM provider layer for TestCase Genie.

Primary provider : Google Gemini (google-genai SDK).
Fallback         : Mock data (clearly labeled as demo data).

To add another provider (e.g. Anthropic, OpenAI) in the future:
  1. Add its API key / model vars to .env and .env.example.
  2. Implement a call_<provider>() function following the same signature
     as call_gemini() — takes (prompt: str) → str (raw LLM text).
  3. Call it inside generate_test_cases() before the mock fallback.
"""

import os
import time
import json
import re

from dotenv import load_dotenv

load_dotenv()

# ── Read credentials from .env ────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── Try importing the google-genai SDK ───────────────────────────────────────
try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _strip_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```) before parsing."""
    text = text.strip()
    # Remove opening fence with optional language tag
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    # Remove closing fence
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _parse_json(raw: str) -> list[dict]:
    """Strip fences, then parse JSON. Raises ValueError on failure."""
    clean = _strip_fences(raw)
    data = json.loads(clean)
    if not isinstance(data, list):
        raise ValueError("LLM returned JSON but it is not a list.")
    return data


# ─────────────────────────────────────────────────────────────────────────────
# PRIMARY PROVIDER — Google Gemini
# ─────────────────────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> str:
    """
    Send a single-turn prompt to Gemini and return the raw text response.
    Raises an exception on HTTP errors (caller handles retry / fallback).
    """
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=4096,   # raised so long outputs are not cut off
        ),
    )
    return response.text


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def call_llm(prompt: str) -> tuple[list[dict], bool]:
    """
    Try the primary provider (Gemini) with one automatic retry on rate-limit
    or invalid-JSON errors.

    Returns:
        (cases, is_mock)
        cases   : list of test-case dicts
        is_mock : True when the result comes from mock / fallback data
    """
    if not GEMINI_AVAILABLE:
        return [], True   # signal caller to use mock

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return [], True   # no key configured → mock

    last_exc = None
    for attempt in range(2):           # up to 2 attempts
        try:
            raw = call_gemini(prompt)
            cases = _parse_json(raw)
            return cases, False        # success — real data

        except Exception as exc:
            last_exc = exc
            exc_str = str(exc).lower()

            # Rate-limit / quota (HTTP 429 or "quota" keyword)
            is_rate_limit = "429" in exc_str or "quota" in exc_str or "rate" in exc_str

            if attempt == 0:
                wait = 8 if is_rate_limit else 2
                time.sleep(wait)
                continue              # retry
            # second attempt also failed — fall through
            break

    # Both attempts failed — surface the error to the caller
    raise last_exc
