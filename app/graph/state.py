from typing import TypedDict


class TailorGraphState(TypedDict, total=False):
    application_id: str
    listing_id: str
    jd_text: str
    company: str
    project_candidates: list[dict]  # ProjectCandidate.model_dump(), fetched once per scan batch
    ranked_projects: list[dict]  # RankedProject.model_dump()
    project_decision: dict  # {"action": "approve"|"decline", "selected_repo_names": [...]}
    tailored_resume: dict  # TailoredResume.model_dump()
    cover_letter: dict  # CoverLetter.model_dump()
    final_decision: dict  # {"action": "approve"|"decline"}
