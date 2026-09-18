import uuid
from datetime import datetime, timezone

from langgraph.types import interrupt

from app.db.models import Application, ApplicationStatus
from app.db.session import SessionLocal
from app.graph.state import TailorGraphState
from app.nodes.tailor.profile import load_base_profile
from app.nodes.tailor.project_matcher import rank_projects_for_jd
from app.nodes.tailor.resume_generator import generate_cover_letter, generate_tailored_resume
from app.schemas.project import ProjectCandidate

PROJECT_REVIEW_TOP_N = 5


def rank_projects_node(state: TailorGraphState) -> dict:
    candidates = [ProjectCandidate.model_validate(c) for c in state["project_candidates"]]
    ranked = rank_projects_for_jd(state["jd_text"], candidates, top_n=PROJECT_REVIEW_TOP_N)
    return {"ranked_projects": [r.model_dump() for r in ranked]}


def await_project_selection_node(state: TailorGraphState) -> dict:
    # No side effects before interrupt() — this node re-runs from the top
    # on resume, so anything here would double-fire.
    decision = interrupt(
        {
            "type": "project_selection",
            "application_id": state["application_id"],
            "ranked_projects": state["ranked_projects"],
        }
    )
    return {"project_decision": decision}


def route_after_project_selection(state: TailorGraphState) -> str:
    if state["project_decision"].get("action") == "decline":
        return "decline"
    return "tailor"


def tailor_node(state: TailorGraphState) -> dict:
    profile = load_base_profile()
    selected_names = set(state["project_decision"].get("selected_repo_names", []))
    all_candidates = [ProjectCandidate.model_validate(c) for c in state["project_candidates"]]
    ranked_repo_names = {r["project"]["repo_name"] for r in state["ranked_projects"]}
    selected_projects = [
        c for c in all_candidates if c.repo_name in selected_names and c.repo_name in ranked_repo_names
    ]

    resume = generate_tailored_resume(profile, state["jd_text"], selected_projects)
    cover_letter = generate_cover_letter(profile, state["jd_text"], state["company"], resume.bullets)

    session = SessionLocal()
    try:
        app_row = session.get(Application, uuid.UUID(state["application_id"]))
        if app_row is None:
            # Reachable now that applications can be deleted mid-flow (the
            # DELETE endpoint, or a decline racing a second in-flight
            # approval) — fail loudly rather than AttributeError on a None,
            # since silently dropping freshly-generated tailored content
            # would be real data loss, unlike decline's "already gone is
            # fine, that was the goal anyway".
            raise LookupError(f"Application {state['application_id']} was deleted before tailoring could be saved.")
        app_row.tailored_resume = resume.model_dump_json()
        app_row.tailored_cover_letter = cover_letter.body
        session.commit()
    finally:
        session.close()

    return {"tailored_resume": resume.model_dump(), "cover_letter": cover_letter.model_dump()}


def await_final_approval_node(state: TailorGraphState) -> dict:
    decision = interrupt(
        {
            "type": "final_approval",
            "application_id": state["application_id"],
            "tailored_resume": state["tailored_resume"],
            "cover_letter": state["cover_letter"],
        }
    )
    return {"final_decision": decision}


def route_after_final_approval(state: TailorGraphState) -> str:
    if state["final_decision"].get("action") == "decline":
        return "decline"
    return "mark_applied"


def mark_applied_node(state: TailorGraphState) -> dict:
    session = SessionLocal()
    try:
        app_row = session.get(Application, uuid.UUID(state["application_id"]))
        if app_row is None:
            raise LookupError(f"Application {state['application_id']} was deleted before it could be marked applied.")
        app_row.status = ApplicationStatus.APPLIED
        app_row.applied_at = datetime.now(timezone.utc)
        session.commit()
    finally:
        session.close()
    return {}


def decline_node(state: TailorGraphState) -> dict:
    session = SessionLocal()
    try:
        app_row = session.get(Application, uuid.UUID(state["application_id"]))
        if app_row is not None:
            session.delete(app_row)
            session.commit()
    finally:
        session.close()
    return {}
