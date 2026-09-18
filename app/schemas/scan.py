from pydantic import BaseModel


class PendingReview(BaseModel):
    application_id: str
    review_type: str  # "project_selection" | "final_approval"
    payload: dict


class ScanSummary(BaseModel):
    sources_scraped: list[str]
    new_applications_started: int
    pending_reviews: list[PendingReview]
