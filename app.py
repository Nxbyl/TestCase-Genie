"""
TestCase Genie v2 — AI-powered test case generator for QA engineers and students.
Stack: Python + Streamlit.  Primary LLM: Google Gemini.  Fallback: mock demo data.
"""

import io
import csv
import os

import streamlit as st
from dotenv import load_dotenv

from prompts import build_prompt
from llm_client import call_llm, GEMINI_AVAILABLE, GEMINI_API_KEY

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TestCase Genie",
    page_icon="🧪",
    layout="centered",
)

# ── Minimal CSS — theme-aware (works in both light and dark mode) ─────────────
st.markdown(
    """
    <style>
        /* ── Layout: remove the empty top gap that Streamlit adds ── */
        .block-container { padding-top: 1.5rem !important; }

        /* ── Header card ── */
        .tc-header {
            background: var(--primary-color, #2563EB);
            color: #fff;
            padding: 1.2rem 1.6rem;
            border-radius: 10px;
            margin-bottom: 1.2rem;
        }
        .tc-header h1 { margin: 0; font-size: 1.9rem; }
        .tc-header p  { margin: .3rem 0 0; opacity: .88; font-size: .93rem; }

        /* ── Demo-mode warning — prominent yellow banner ── */
        .demo-warning {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            border-radius: 8px;
            padding: .75rem 1rem;
            color: #92400e;
            font-weight: 600;
            margin-bottom: 1rem;
        }

        /* ── Generate button ── */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: #2563EB !important;
            color: #fff !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: #1D4ED8 !important;
        }

        /* ── Hide Streamlit default footer ── */
        footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA — fallback when no Gemini key is configured
# ─────────────────────────────────────────────────────────────────────────────
_MOCK_CASES = {
    "Functional": [
        {
            "ID": "TC-001",
            "Title": "Valid login with correct credentials",
            "Preconditions": "User account exists and is active.",
            "Steps": "1. Navigate to /login\n2. Enter valid username and password\n3. Click 'Login'",
            "Expected Result": "User is redirected to the dashboard and a welcome message is shown.",
            "Priority": "High",
            "Type": "Functional",
        },
        {
            "ID": "TC-002",
            "Title": "Logout clears the session",
            "Preconditions": "User is logged in.",
            "Steps": "1. Log in successfully\n2. Click 'Logout'\n3. Attempt to access /dashboard directly",
            "Expected Result": "User is redirected to the login page; session cookie is cleared.",
            "Priority": "High",
            "Type": "Functional",
        },
        {
            "ID": "TC-003",
            "Title": "Password is masked in the login form",
            "Preconditions": "None.",
            "Steps": "1. Navigate to /login\n2. Type in the password field",
            "Expected Result": "Characters are displayed as bullets (●).",
            "Priority": "Medium",
            "Type": "Functional",
        },
    ],
    "Negative": [
        {
            "ID": "TC-001",
            "Title": "Login fails with wrong password",
            "Preconditions": "User account exists.",
            "Steps": "1. Navigate to /login\n2. Enter valid username, incorrect password\n3. Click 'Login'",
            "Expected Result": "Error message 'Invalid credentials' is shown; user stays on login page.",
            "Priority": "High",
            "Type": "Negative",
        },
        {
            "ID": "TC-002",
            "Title": "Login fails with empty fields",
            "Preconditions": "None.",
            "Steps": "1. Navigate to /login\n2. Leave username and password blank\n3. Click 'Login'",
            "Expected Result": "Validation errors are shown for both fields.",
            "Priority": "High",
            "Type": "Negative",
        },
        {
            "ID": "TC-003",
            "Title": "SQL injection attempt is rejected",
            "Preconditions": "None.",
            "Steps": "1. Navigate to /login\n2. Enter `' OR '1'='1` as username\n3. Click 'Login'",
            "Expected Result": "Login fails; no unauthorized access is granted.",
            "Priority": "Critical",
            "Type": "Security",
        },
    ],
    "Boundary": [
        {
            "ID": "TC-001",
            "Title": "Username at minimum length boundary",
            "Preconditions": "Registration page is accessible.",
            "Steps": "1. Navigate to /register\n2. Enter username with exactly 3 characters\n3. Submit",
            "Expected Result": "Registration succeeds; minimum boundary is accepted.",
            "Priority": "Medium",
            "Type": "Boundary",
        },
        {
            "ID": "TC-002",
            "Title": "Username one character below minimum",
            "Preconditions": "Registration page is accessible.",
            "Steps": "1. Navigate to /register\n2. Enter username with 2 characters\n3. Submit",
            "Expected Result": "Validation error: 'Username must be at least 3 characters'.",
            "Priority": "Medium",
            "Type": "Boundary",
        },
        {
            "ID": "TC-003",
            "Title": "Username at maximum length boundary",
            "Preconditions": "Registration page is accessible.",
            "Steps": "1. Navigate to /register\n2. Enter username with exactly 50 characters\n3. Submit",
            "Expected Result": "Registration succeeds; maximum boundary is accepted.",
            "Priority": "Medium",
            "Type": "Boundary",
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# AGENT ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def generate_test_cases(
    requirement: str, test_type: str, num_cases: int
) -> tuple[list[dict], bool]:
    """
    Generate test cases via the LLM or fall back to mock demo data.

    Returns:
        (cases, is_mock)  — is_mock=True when returning demo data.
    """
    prompt = build_prompt(requirement, test_type, num_cases)

    # ── Try real LLM first ────────────────────────────────────────────────────
    try:
        cases, is_mock = call_llm(prompt)
        if is_mock:
            # call_llm signals mock when SDK/key unavailable (no exception raised)
            mock_pool = _MOCK_CASES.get(test_type, _MOCK_CASES["Functional"])
            return mock_pool[:num_cases], True
        return cases, False

    except Exception as exc:
        exc_str = str(exc).lower()
        if "429" in exc_str or "quota" in exc_str or "rate" in exc_str:
            st.error(
                "⚠️ **Rate limit / quota exceeded.** "
                "The Gemini API returned HTTP 429. "
                "Please wait a minute and try again, or check your quota at "
                "[Google AI Studio](https://aistudio.google.com/)."
            )
        else:
            st.error(
                f"⚠️ **LLM error:** {exc}\n\n"
                "Falling back to demo data. Check your `GEMINI_API_KEY` and network connection."
            )
        mock_pool = _MOCK_CASES.get(test_type, _MOCK_CASES["Functional"])
        return mock_pool[:num_cases], True


# ─────────────────────────────────────────────────────────────────────────────
# CSV EXPORT
# ─────────────────────────────────────────────────────────────────────────────

COLUMNS = ["ID", "Title", "Preconditions", "Steps", "Expected Result", "Priority", "Type"]


def to_csv(cases: list[dict]) -> bytes:
    """
    Serialize test cases to CSV bytes with UTF-8 BOM so Excel opens it correctly.
    All seven columns are always included; missing keys become empty strings.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=COLUMNS,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for case in cases:
        # Fill any missing keys with empty string so DictWriter never raises
        row = {col: case.get(col, "") for col in COLUMNS}
        writer.writerow(row)
    # UTF-8 BOM so Excel auto-detects encoding
    return "\ufeff".encode("utf-8") + buf.getvalue().encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# UI LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="tc-header">
        <h1>🧪 TestCase Genie</h1>
        <p>Paste a requirement or user story, choose a test type, and let AI generate
           ready-to-use test cases in seconds.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Demo-mode banner (shown only when no valid key is configured) ─────────────
_key_missing = (
    not GEMINI_AVAILABLE
    or not GEMINI_API_KEY
    or GEMINI_API_KEY == "your_gemini_api_key_here"
)
if _key_missing:
    st.markdown(
        '<div class="demo-warning">'
        "⚠️ <strong>DEMO DATA — not generated from your input.</strong> "
        "Set <code>GEMINI_API_KEY</code> in a <code>.env</code> file to enable "
        "real AI-generated test cases."
        "</div>",
        unsafe_allow_html=True,
    )

# ── Input controls ────────────────────────────────────────────────────────────
requirement = st.text_area(
    "📋 Requirement / User Story",
    placeholder=(
        "Example: As a registered user, I want to log in with my email and password "
        "so that I can access my account dashboard.\n\n"
        "Contoh (Indonesia): Sebagai pengguna terdaftar, saya ingin masuk menggunakan "
        "email dan kata sandi agar dapat mengakses dashboard saya."
    ),
    height=160,
)

col1, col2 = st.columns([2, 1])
with col1:
    test_type = st.selectbox(
        "🔬 Test Type",
        options=["Functional", "Negative", "Boundary"],
        help=(
            "Functional — verify the feature works as expected.\n"
            "Negative — verify the system handles invalid inputs gracefully.\n"
            "Boundary — verify behaviour at the edges of valid input ranges."
        ),
    )
with col2:
    num_cases = st.slider(
        "Number of test cases",
        min_value=5,
        max_value=15,
        value=8,
        help="How many test cases the AI should generate.",
    )

generate_btn = st.button("⚡ Generate Test Cases", type="primary", use_container_width=True)

# ── Input validation ──────────────────────────────────────────────────────────
if generate_btn:
    req_stripped = requirement.strip()
    if not req_stripped:
        st.warning("⚠️ Please enter a requirement or user story before generating.")
    elif len(req_stripped) < 20:
        st.warning(
            f"⚠️ Your requirement is very short ({len(req_stripped)} characters). "
            "Please provide at least 20 characters for meaningful test cases."
        )
    else:
        with st.spinner("Analysing requirement and generating test cases…"):
            cases, is_mock = generate_test_cases(req_stripped, test_type, num_cases)
        st.session_state["cases"] = cases
        st.session_state["is_mock"] = is_mock
        st.session_state["last_type"] = test_type

# ── Results ───────────────────────────────────────────────────────────────────
if "cases" in st.session_state:
    cases: list[dict] = st.session_state["cases"]
    is_mock: bool = st.session_state.get("is_mock", False)
    last_type: str = st.session_state.get("last_type", test_type)

    # Prominent demo warning above the table
    if is_mock:
        st.warning(
            "⚠️ **DEMO DATA — not generated from your input.** "
            "Configure your Gemini API key to generate real test cases.",
            icon="⚠️",
        )
    else:
        st.success(f"✅ {len(cases)} **{last_type}** test cases generated by Gemini.")

    st.markdown("### 📊 Test Cases")

    # Build column config for all 7 columns with wrapped text
    col_cfg = {
        "ID":              st.column_config.TextColumn("ID",              width="small"),
        "Title":           st.column_config.TextColumn("Title",           width="medium"),
        "Preconditions":   st.column_config.TextColumn("Preconditions",   width="medium"),
        "Steps":           st.column_config.TextColumn("Steps",           width="large"),
        "Expected Result": st.column_config.TextColumn("Expected Result", width="large"),
        "Priority":        st.column_config.TextColumn("Priority",        width="small"),
        "Type":            st.column_config.TextColumn("Type",            width="small"),
    }

    st.dataframe(
        cases,
        hide_index=True,
        use_container_width=True,
        column_config=col_cfg,
        column_order=COLUMNS,
    )

    # ── Download ──────────────────────────────────────────────────────────────
    st.download_button(
        label="⬇️  Download as CSV",
        data=to_csv(cases),
        file_name="test_cases.csv",
        mime="text/csv; charset=utf-8",
        use_container_width=True,
    )
