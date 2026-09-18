from pydantic import BaseModel

from app.nodes.matcher.role_classifier import RoleTier


class MatchResult(BaseModel):
    passes_hard_filters: bool
    exclusion_reasons: list[str]
    role_tier: RoleTier | None
    role_similarity: float | None
    stipend_amount: int | None
    stipend_status: str  # "confirmed_ok" | "confirmed_below_minimum" | "unknown"
    ppo_detected: bool
