from typing import Literal

from pydantic import BaseModel

from app.schemas.jd_summary import JDSummary


class ApplicationSummary(BaseModel):
    id: str
    status: str
    listing_title: str
    listing_company: str
    listing_url: str
    created_at: str
    status_changed_at: str
    applied_at: str | None
    # From listing_summary (matcher-confirmed, from JD text) — not
    # Listing.stipend_amount, which is a dead column for the only
    # currently-enabled source. None means not stated, not unpaid.
    stipend_amount: int | None = None
    role_tier: str | None = None


class ApplicationDetail(ApplicationSummary):
    jd_snapshot: dict
    listing_summary: JDSummary | None
    tailored_resume: dict | None
    tailored_cover_letter: str | None
    pending_review: dict | None


class ProjectSelectionRequest(BaseModel):
    action: Literal["approve", "decline"]
    selected_repo_names: list[str] = []


class FinalApprovalRequest(BaseModel):
    action: Literal["approve", "decline"]


class StatusUpdateRequest(BaseModel):
    status: Literal["pending", "applied", "rejected", "interview", "stale"]


class ApplicationStats(BaseModel):
    total: int
    by_status: dict[str, int]
    # (interview + rejected) / (applied + interview + rejected) — share of
    # actually-submitted applications that got any response at all. None
    # when nothing's been applied to yet, not 0, since 0 would misleadingly
    # read as "you applied and got zero responses."
    response_rate: float | None
    avg_stipend: float | None
    role_tier_breakdown: dict[str, int]
