"""
prompts.py — Prompt composition for TestCase Genie.

The final prompt is assembled at runtime from four named layers.
Each layer has a clear, single responsibility so it can be
independently tweaked or swapped without touching the others.
"""


# ── Layer 1: SYSTEM_LAYER ─────────────────────────────────────────────────────
# Purpose: establish the LLM's identity and professional mindset.
# Keeps the role definition separate from task details so it can be
# reused across different test-generation tasks in the future.
SYSTEM_LAYER = (
    "You are a meticulous Senior QA Analyst with 10+ years of experience "
    "writing test cases for enterprise software. "
    "You follow industry-standard practices (IEEE 829, ISTQB) and always "
    "produce precise, unambiguous, and actionable test cases. "
    "You never omit required fields, and you never add commentary outside "
    "the requested JSON structure."
)


# ── Layer 2: CONTEXT_LAYER template ──────────────────────────────────────────
# Purpose: inject the user's specific requirement and chosen test type.
# Kept as a template so it is formatted at call-time, not at import-time,
# allowing the same module to handle any requirement or test type.
CONTEXT_LAYER_TEMPLATE = (
    "--- REQUIREMENT ---\n"
    "{requirement}\n"
    "--- END REQUIREMENT ---\n\n"
    "Test type requested: {test_type}"
)


# ── Layer 3: TASK_LAYER ───────────────────────────────────────────────────────
# Purpose: instruct the model on the exact reasoning and generation steps.
# Separating the 'what to think' from 'what to output' improves compliance
# with the output schema in Layer 4.
TASK_LAYER_TEMPLATE = (
    "Steps to follow:\n"
    "1. Carefully read and understand the requirement above.\n"
    "2. Identify testable conditions relevant to {test_type} testing.\n"
    "3. Generate exactly {num_cases} test cases of the '{test_type}' type.\n"
    "4. For each test case, populate ALL seven required fields.\n"
    "5. IMPORTANT: Respond in the SAME LANGUAGE as the requirement text "
    "(if the requirement is in Indonesian, write all field values in Indonesian; "
    "if in English, write in English)."
)


# ── Layer 4: OUTPUT_LAYER ─────────────────────────────────────────────────────
# Purpose: enforce a strict JSON schema so the parser never fails on
# unexpected structure. Defined last so the model sees it immediately
# before it begins generating, maximising schema adherence.
OUTPUT_LAYER = (
    "Output format — return ONLY a valid JSON array, with NO markdown fences, "
    "NO code blocks, NO explanations, and NO text before or after the array.\n\n"
    "Each element in the array must have EXACTLY these seven keys:\n"
    '  "ID"             : string  — e.g. "TC-001"\n'
    '  "Title"          : string  — short descriptive title\n'
    '  "Preconditions"  : string  — what must be true before the test\n'
    '  "Steps"          : string  — numbered action steps as a single string\n'
    '  "Expected Result": string  — what the system should do\n'
    '  "Priority"       : string  — one of: Critical | High | Medium | Low\n'
    '  "Type"           : string  — one of: Functional | Negative | Boundary | '
    'Performance | Security | Usability\n\n'
    "Do not include any other keys. Do not wrap the array in an object."
)


# ─────────────────────────────────────────────────────────────────────────────
# COMPOSER
# ─────────────────────────────────────────────────────────────────────────────

def build_prompt(requirement: str, test_type: str, num_cases: int) -> str:
    """
    Assemble the four layers into a single prompt string sent to the LLM.

    Args:
        requirement : raw text from the user's input field
        test_type   : one of Functional | Negative | Boundary
        num_cases   : number of test cases to generate (from the UI slider)

    Returns:
        A single string prompt ready to be passed to any LLM provider.
    """
    context = CONTEXT_LAYER_TEMPLATE.format(
        requirement=requirement,
        test_type=test_type,
    )
    task = TASK_LAYER_TEMPLATE.format(
        test_type=test_type,
        num_cases=num_cases,
    )

    return "\n\n".join([SYSTEM_LAYER, context, task, OUTPUT_LAYER])
