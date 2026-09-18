from pydantic import BaseModel, field_validator


class SourceItem(BaseModel):
    source_type: str  # "experience" | "hackathon" | "responsibility" | "project"
    source_ref: str
    excerpt: str


class TailoredBullet(BaseModel):
    text: str
    source_type: str
    source_ref: str
    source_excerpt: str
    # Terms in `text` not traceable to source_excerpt or the base skill
    # list — surfaced for human review at the approval gate, never
    # silently dropped or silently trusted.
    flagged_terms: list[str] = []


class TailoredResume(BaseModel):
    name: str
    email: str
    phone: str | None
    location: str | None
    links: dict[str, str | None]
    education_summary: list[str]
    # Category name -> selected skills in that category, same shape as
    # BaseProfile.skills but filtered down to what's relevant to this JD.
    highlighted_skills: dict[str, list[str]]
    bullets: list[TailoredBullet]

    @field_validator("highlighted_skills", mode="before")
    @classmethod
    def _accept_legacy_flat_skill_list(cls, v):
        # Applications tailored before skills were categorized have
        # highlighted_skills stored as a flat list in their persisted JSON
        # (TailoredResume.model_dump_json() from that era) — that JSON is
        # permanent, already-generated data, not something a code change can
        # retroactively rewrite, so the read path has to stay able to parse
        # it rather than 500 on every legacy resume forever.
        if isinstance(v, list):
            return {"Skills": v} if v else {}
        return v


class CoverLetter(BaseModel):
    body: str
    flagged_terms: list[str] = []
