from pydantic import BaseModel


class JDSummary(BaseModel):
    # Facts the matcher already computes — surfaced here so a human doesn't
    # have to re-derive them by reading the raw JD text themselves.
    stipend_amount: int | None = None
    stipend_status: str = "unknown"  # "confirmed_ok" | "confirmed_below_minimum" | "unknown"
    location: str | None = None
    is_remote: bool = False
    ppo_detected: bool = False
    role_tier: str | None = None
    # Cosine similarity of the JD text to role_tier's anchor text — the
    # actual number behind the role match, not just the pass/fail tier, so
    # the matcher's reasoning is inspectable rather than a black box.
    role_similarity: float | None = None

    # AI-extracted — grounded strictly in the (often truncated) JD text,
    # empty lists/None when the text doesn't state something rather than
    # guessed.
    responsibilities: list[str] = []
    requirements: list[str] = []
    duration: str | None = None
    benefits: list[str] = []
