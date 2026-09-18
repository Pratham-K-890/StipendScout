from pydantic import BaseModel


class IngestSummary(BaseModel):
    source: str
    new: int
    updated: int
    disappeared: int
    skipped_empty_run: bool = False


class StaleSweepResult(BaseModel):
    stale_by_age: int
    stale_by_disappearance: int
    total_marked: int
