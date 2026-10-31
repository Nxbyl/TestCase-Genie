# 🧪 TestCase Genie

An AI-powered test case generator for QA engineers and students.
Paste a requirement or user story, pick a test type, and get a structured
test case table you can export to CSV — all in one page.

---

## Features

| Feature | Details |
|---|---|
| **Test types** | Functional · Negative · Boundary |
| **AI backend** | OpenAI `gpt-4o-mini` (falls back to demo data if no key) |
| **Export** | One-click CSV download |
| **Stack** | Python + Streamlit — single file, no database |

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

### 4 — (Optional) Set your OpenAI API key

Without a key the app runs in **demo mode** with built-in sample test cases.

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# macOS / Linux
export OPENAI_API_KEY="sk-..."
```

### 5 — Run the app

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

---

## Project Structure

```
testcase-genie/
├── app.py            # Single-file Streamlit application
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## How It Works

1. The user pastes a **requirement or user story** into the text area.
2. Selects a **test type** (Functional / Negative / Boundary).
3. Clicks **Generate Test Cases**.
4. The app calls `generate_test_cases()`:
   - If `OPENAI_API_KEY` is set → sends a structured prompt to `gpt-4o-mini` and parses the JSON response.
   - Otherwise → returns pre-built mock test cases so the UI is always fully usable.
5. Results are displayed in an interactive table and can be **downloaded as CSV**.

---

## Requirements

- Python **3.9+**
- `streamlit >= 1.35.0`
- `openai >= 1.30.0` *(only needed for real AI generation)*
