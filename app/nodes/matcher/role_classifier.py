import enum
import re

from app.nodes.matcher.embeddings import cosine_similarity, embed_text, embed_texts

# Below this cosine similarity to every anchor, we treat the role as not
# matching any of the three priority tiers at all (rather than forcing it
# into the closest one). Calibrated on a small hand-built sample: true
# matches scored 0.60-0.85 on their own tier, while off-topic roles
# (sales, HR, frontend) topped out at 0.45 on their highest tier — MiniLM
# has some baseline "tech job" similarity bias, so 0.35 was too loose and
# let a Sales Intern JD through as BACKEND. Revisit as more real listings
# flow through.
SIMILARITY_THRESHOLD = 0.5


class RoleTier(str, enum.Enum):
    BACKEND = "backend"
    ML_DATA_SCIENCE = "ml_data_science"
    AI_AGENT_LLM = "ai_agent_llm"


_ANCHOR_TEXTS: dict[RoleTier, str] = {
    RoleTier.BACKEND: (
        "Backend developer internship building REST APIs and server-side "
        "services using FastAPI, Django, or Flask. Working with databases, "
        "backend application logic, and server architecture. Not a "
        "frontend or UI-focused role."
    ),
    RoleTier.ML_DATA_SCIENCE: (
        "Machine learning and data science internship building predictive "
        "models, performing data analysis and statistics, using pandas, "
        "scikit-learn, and classical machine learning algorithms on "
        "structured data."
    ),
    RoleTier.AI_AGENT_LLM: (
        "AI agent and large language model engineering internship building "
        "LLM-powered applications, prompt engineering, retrieval-augmented "
        "generation, agent orchestration with LangChain or LangGraph, and "
        "generative AI systems."
    ),
}

# Cosine similarity doesn't reliably encode negation — the BACKEND anchor
# explicitly says "Not a frontend or UI-focused role", but a real pure-React
# internship still scored 0.582 against it (verified live against a real
# Adzuna listing). Layering a cheap keyword veto on top of the embedding
# catches this specific known blind spot without weakening the embedding
# classification everywhere else (ML/AI-agent tiers don't have this
# confusion in the same way, so this only applies to BACKEND).
_FRONTEND_KEYWORDS = re.compile(
    r"\b(react|redux|vue|angular|css|html|responsive design|ui/ux|"
    r"frontend|front-end|front end)\b",
    re.IGNORECASE,
)
_BACKEND_KEYWORDS = re.compile(
    r"\b(fastapi|django|flask|rest api|backend|back-end|back end|"
    r"server-side|database|\bsql\b|orm|api endpoint)\b",
    re.IGNORECASE,
)


def _is_actually_frontend_not_backend(text: str) -> bool:
    frontend_hits = len(_FRONTEND_KEYWORDS.findall(text))
    backend_hits = len(_BACKEND_KEYWORDS.findall(text))
    return frontend_hits >= 2 and backend_hits == 0


_anchor_embeddings_cache: dict[RoleTier, list[float]] | None = None


def _get_anchor_embeddings() -> dict[RoleTier, list[float]]:
    global _anchor_embeddings_cache
    if _anchor_embeddings_cache is None:
        tiers = list(_ANCHOR_TEXTS.keys())
        vectors = embed_texts([_ANCHOR_TEXTS[tier] for tier in tiers])
        _anchor_embeddings_cache = dict(zip(tiers, vectors))
    return _anchor_embeddings_cache


def classify_role(text: str) -> tuple[RoleTier | None, float]:
    """Returns (best-matching tier or None, its similarity score)."""
    embedding = embed_text(text)
    anchors = _get_anchor_embeddings()
    scored = {tier: cosine_similarity(embedding, vec) for tier, vec in anchors.items()}
    best_tier = max(scored, key=scored.get)
    best_score = scored[best_tier]
    if best_score < SIMILARITY_THRESHOLD:
        return None, best_score
    if best_tier == RoleTier.BACKEND and _is_actually_frontend_not_backend(text):
        return None, best_score
    return best_tier, best_score
