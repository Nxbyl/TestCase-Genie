# 🧪 TestCase Genie

An AI-powered test case generator for QA engineers and students.
Paste a requirement or user story, pick a test type and the number of cases,
and get a structured test case table you can export to CSV — all in one page.

---

## Features

| Feature | Details |
|---|---|
| **Test types** | Functional · Negative · Boundary |
| **AI backend** | Google Gemini (primary) · mock demo data (fallback when no key) |
| **Prompt layers** | 4-layer prompt (System · Context · Task · Output) in `prompts.py` |
| **Number of cases** | Slider 5–15, default 8 |
| **Languages** | Responds in the same language as the requirement (English or Indonesian) |
| **Export** | One-click CSV download — UTF-8 with BOM (Excel-safe) |
| **Stack** | Python + Streamlit — no database |

---

## Project Structure

```
testcase-genie/
├── app.py                  # Streamlit UI + agent entry-point
├── llm_client.py           # Isolated LLM provider layer (Gemini)
├── prompts.py              # 4-layer prompt composer
├── requirements.txt        # Python dependencies
├── .env.example            # Template — copy to .env and fill in your key
├── .gitignore
├── .streamlit/
│   └── config.toml         # Theme (primaryColor, bg, font)
└── README.md
```

---

## Quick Start

### 1 — Clone / download

```bash
git clone <repo-url>
cd testcase-genie
```

### 2 — Create a virtual environment (recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Set your Gemini API key

Copy the example env file and fill in your key:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder values:

```
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

Get a free API key at <https://aistudio.google.com/app/apikey>.

> **Without a key** the app runs in **demo mode** with built-in sample test
> cases. A visible yellow banner clearly labels all demo output as
> **"DEMO DATA — not generated from your input"**.

### 5 — Run the app

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

---

## How It Works

1. User pastes a **requirement or user story** into the text area.
2. Selects a **test type** and **number of test cases** (5–15).
3. Clicks **Generate Test Cases**.
4. `app.py` calls `generate_test_cases()`:
   - Builds a 4-layer prompt via `prompts.py`.
   - Calls `llm_client.call_llm()` which sends the prompt to **Google Gemini**.
   - On rate-limit (HTTP 429) it waits 8 s and retries once.
   - On invalid JSON it retries once with a 2 s wait.
   - If all retries fail, shows a friendly `st.error` and falls back to mock data.
5. Results are shown in a full-width interactive table and can be **downloaded as CSV**.

---

## API Key Security

- **Never** commit your `.env` file — it is excluded by `.gitignore`.
- Use `.env.example` as the template; it contains only placeholder values.
- Keys are read with `python-dotenv`; they are never hard-coded in source files.

---

## Requirements

- Python **3.9+**
- `streamlit >= 1.35.0`
- `google-genai >= 0.8.0`
- `python-dotenv >= 1.0.0`

---

## V2 Changes

The following changes were made in **version 2** and the reason for each:

| # | Change | Reason |
|---|---|---|
| 1 | **Switched from OpenAI to Google Gemini** (`google-genai` SDK) | Use a freely available API; key read from `.env` via `python-dotenv`. |
| 2 | **LLM logic moved to `llm_client.py`** | Isolates the provider so a second provider (Anthropic, OpenAI, etc.) can be added by adding one function without touching the UI. |
| 3 | **Prompt moved to `prompts.py`, composed from 4 named layers** | Separating System / Context / Task / Output layers makes each piece independently editable and easier to understand. |
| 4 | **Mock mode now clearly labeled "DEMO DATA — not generated from your input"** | V1 silently served mock data; users had no way to know results weren't real. |
| 5 | **Rate-limit (HTTP 429) handled with friendly message + single retry** | V1 crashed on quota errors; now shows a clear explanation and retries after 8 s. |
| 6 | **Markdown code fences stripped before `json.loads()`** | Gemini (and most LLMs) sometimes wrap JSON in ` ```json ``` `; V1 crashed on this. |
| 7 | **Token limit raised to 4096** | V1 capped at 800 tokens, causing outputs to be cut off for ≥5 test cases. |
| 8 | **7-field schema**: ID, Title, Preconditions, Steps, Expected Result, Priority, Type | V1 had only 5 fields; Preconditions and Type were missing. |
| 9 | **`st.dataframe` shows all 7 columns with `column_order`** | V1 displayed whatever keys the LLM returned, leading to missing or reordered columns. |
| 10 | **"Number of test cases" slider (5–15, default 8)** | Users need different quantities; V1 always returned exactly 3. |
| 11 | **Prompt instructs the LLM to match the input language** | Requirements written in Indonesian now produce test cases in Indonesian. |
| 12 | **Input validation: warning if empty or < 20 chars** | V1 showed an error only on empty input; short inputs produced useless test cases. |
| 13 | **CSV export: UTF-8 with BOM, all 7 columns** | V1 produced UTF-8 without BOM (garbled in Excel) and only 5 columns. |
| 14 | **`.env.example` and `.gitignore` added** | Prevents accidental key commits; gives a clear template for setup. |
| 15 | **`.streamlit/config.toml` added** | Sets `primaryColor`, background, and font so theme is consistent in light and dark mode without fragile CSS overrides. |
| 16 | **Empty white bar above the Requirement field removed** | Caused by the wrapper `<div class="tc-card">` block in V1; replaced with `padding-top` on `.block-container`. |
