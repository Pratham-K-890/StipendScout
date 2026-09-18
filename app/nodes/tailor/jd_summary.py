from app.nodes.tailor.llm_client import generate_json


def _summary_prompt(jd_text: str) -> str:
    return f"""Summarize this internship job description into short factual
bullet points. Extract ONLY information explicitly stated in the text —
do not invent, infer, or assume anything not present. If a category has
no stated information, return an empty list (or null for duration).

Job Description:
{jd_text}

Return ONLY valid JSON, no markdown fences, in this exact shape:
{{"responsibilities": ["...", "..."], "requirements": ["...", "..."], "duration": "..." or null, "benefits": ["...", "..."]}}"""


def generate_ai_jd_summary(jd_text: str) -> dict:
    """Returns {"responsibilities": [...], "requirements": [...],
    "duration": str|None, "benefits": [...]} — grounded strictly in the
    given text, no fabrication guardrail needed the way the resume tailor
    has one, since this is summarization of provided text, not generation
    of new claims about the candidate."""
    result = generate_json(_summary_prompt(jd_text))
    return {
        "responsibilities": result.get("responsibilities") or [],
        "requirements": result.get("requirements") or [],
        "duration": result.get("duration"),
        "benefits": result.get("benefits") or [],
    }
