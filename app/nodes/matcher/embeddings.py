import math
from functools import lru_cache

from fastembed import TextEmbedding

# Matches the 384-dim pgvector column sized for this model in app/db/models.py.
# Used for module 4's role classification — anchors are hand-written in
# JD-like phrasing, so plain STS-style similarity (what MiniLM is trained
# for) works well there.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Used for module 5's JD<->project ranking. A JD (imperative, "build X
# using Y") and a README (declarative, "this app does X") are different
# enough in style/length that MiniLM's symmetric similarity performs
# poorly there (empirically: a genuine RAG project scored below unrelated
# ones). BGE is trained for asymmetric query/passage retrieval instead —
# still 384-dim, still local/free. Deliberately NOT used for module 4,
# which is already tuned and validated against MiniLM.
RETRIEVAL_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=2)
def _get_model(model_name: str) -> TextEmbedding:
    return TextEmbedding(model_name=model_name)


def embed_texts(texts: list[str], model_name: str = MODEL_NAME) -> list[list[float]]:
    return [vector.tolist() for vector in _get_model(model_name).embed(texts)]


def embed_text(text: str, model_name: str = MODEL_NAME) -> list[float]:
    return embed_texts([text], model_name=model_name)[0]


def embed_query(text: str) -> list[float]:
    """BGE query-side embedding for asymmetric retrieval (e.g. a JD)."""
    return embed_text(_BGE_QUERY_PREFIX + text, model_name=RETRIEVAL_MODEL_NAME)


def embed_passage(text: str) -> list[float]:
    """BGE passage-side embedding for asymmetric retrieval (e.g. a project)."""
    return embed_text(text, model_name=RETRIEVAL_MODEL_NAME)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)
