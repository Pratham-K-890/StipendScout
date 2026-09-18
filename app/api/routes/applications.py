import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_checkpointer
from app.db.models import Application, ApplicationStatus, Listing
from app.db.session import get_db
from app.graph import get_pending_review, resume_final_approval, resume_project_selection
from app.nodes.tailor.resume_render import render_resume_pdf
from app.schemas.api import (
    ApplicationDetail,
    ApplicationStats,
    ApplicationSummary,
    FinalApprovalRequest,
    ProjectSelectionRequest,
    StatusUpdateRequest,
)
from app.schemas.jd_summary import JDSummary
from app.schemas.tailored_resume import TailoredResume

router = APIRouter(prefix="/applications", tags=["applications"])


def _parse_uuid(application_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Application not found") from None


def _to_summary(app_row: Application, listing: Listing) -> ApplicationSummary:
    listing_summary = app_row.listing_summary or {}
    return ApplicationSummary(
        id=str(app_row.id),
        status=app_row.status.value,
        listing_title=listing.title,
        listing_company=listing.company,
        listing_url=listing.url,
        created_at=app_row.created_at.isoformat(),
        status_changed_at=app_row.status_changed_at.isoformat(),
        applied_at=app_row.applied_at.isoformat() if app_row.applied_at else None,
        stipend_amount=listing_summary.get("stipend_amount"),
        role_tier=listing_summary.get("role_tier"),
    )


@router.get("", response_model=list[ApplicationSummary])
def list_applications(status: str | None = None, db: Session = Depends(get_db)):
    query = select(Application, Listing).join(Listing, Application.listing_id == Listing.id)
    if status:
        try:
            status_enum = ApplicationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}") from None
        query = query.where(Application.status == status_enum)
    rows = db.execute(query.order_by(Application.created_at.desc())).all()
    return [_to_summary(app_row, listing) for app_row, listing in rows]


# Must come before GET /{application_id} — otherwise "stats" is captured by
# the {application_id} path param and 404s as a malformed UUID.
@router.get("/stats", response_model=ApplicationStats)
def get_stats(db: Session = Depends(get_db)):
    rows = db.execute(select(Application, Listing).join(Listing, Application.listing_id == Listing.id)).all()

    by_status = {s.value: 0 for s in ApplicationStatus}
    stipends: list[int] = []
    role_tiers: dict[str, int] = {}
    submitted = 0
    responded = 0
    submitted_statuses = (ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED)
    responded_statuses = (ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED)

    for app_row, listing in rows:
        by_status[app_row.status.value] += 1
        # Listing.stipend_amount is a structurally dead column for the only
        # currently-enabled source — Adzuna's normalizer hardcodes it to
        # None and keeps the raw predicted salary separately unconfirmed.
        # The real, matcher-confirmed figure (regex-extracted from the JD
        # text) lives on the Application instead, same source JDSummaryCard
        # already uses — confirmed live: 0/93 real Listings ever had this
        # column set. Fall back to the raw Listing field only in case a
        # future source ever does populate it directly.
        stipend = (app_row.listing_summary or {}).get("stipend_amount")
        if stipend is None:
            stipend = listing.stipend_amount
        if stipend is not None:
            stipends.append(stipend)
        if app_row.status in submitted_statuses:
            submitted += 1
            if app_row.status in responded_statuses:
                responded += 1
        tier = (app_row.listing_summary or {}).get("role_tier") or "unknown"
        role_tiers[tier] = role_tiers.get(tier, 0) + 1

    return ApplicationStats(
        total=len(rows),
        by_status=by_status,
        response_rate=(responded / submitted) if submitted else None,
        avg_stipend=(sum(stipends) / len(stipends)) if stipends else None,
        role_tier_breakdown=role_tiers,
    )


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(application_id: str, db: Session = Depends(get_db), checkpointer=Depends(get_checkpointer)):
    app_uuid = _parse_uuid(application_id)
    app_row = db.get(Application, app_uuid)
    if app_row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    listing = db.get(Listing, app_row.listing_id)
    pending = get_pending_review(checkpointer, application_id)

    summary = _to_summary(app_row, listing)
    return ApplicationDetail(
        **summary.model_dump(),
        jd_snapshot=app_row.jd_snapshot,
        listing_summary=JDSummary.model_validate(app_row.listing_summary) if app_row.listing_summary else None,
        # Goes through TailoredResume (not a raw json.loads) so the
        # legacy-flat-skill-list backward-compat validator normalizes old
        # persisted resumes the same way GET .../resume.pdf already does —
        # confirmed live: without this, this endpoint returned
        # highlighted_skills as a bare list for pre-migration applications,
        # breaking the Record<string, string[]> contract every caller relies on.
        tailored_resume=TailoredResume.model_validate_json(app_row.tailored_resume).model_dump()
        if app_row.tailored_resume
        else None,
        tailored_cover_letter=app_row.tailored_cover_letter,
        pending_review=pending.payload if pending else None,
    )


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: str, db: Session = Depends(get_db), checkpointer=Depends(get_checkpointer)):
    # A general delete for any application regardless of state — decline
    # (during a pending review) already deletes the row as a side effect,
    # but a resolved application (applied/interview/rejected/stale) had no
    # way to be removed at all. Also clears the LangGraph checkpoint thread,
    # not just the DB row, so no orphaned graph state lingers behind it.
    app_uuid = _parse_uuid(application_id)
    app_row = db.get(Application, app_uuid)
    if app_row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app_row)
    db.commit()
    checkpointer.delete_thread(application_id)


@router.get("/{application_id}/resume.pdf")
def get_resume_pdf(application_id: str, db: Session = Depends(get_db)):
    app_uuid = _parse_uuid(application_id)
    app_row = db.get(Application, app_uuid)
    if app_row is None or not app_row.tailored_resume:
        raise HTTPException(status_code=404, detail="No tailored resume available for this application")
    resume = TailoredResume.model_validate_json(app_row.tailored_resume)
    pdf_bytes = render_resume_pdf(resume)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="resume_{application_id}.pdf"'},
    )


@router.patch("/{application_id}/status", response_model=ApplicationSummary)
def update_status(application_id: str, body: StatusUpdateRequest, db: Session = Depends(get_db)):
    # Manual escape hatch for states the automated flow doesn't produce on
    # its own — an interview call or an employer rejection happen outside
    # this system, after you've actually applied.
    app_uuid = _parse_uuid(application_id)
    app_row = db.get(Application, app_uuid)
    if app_row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    app_row.status = ApplicationStatus(body.status)
    db.commit()
    listing = db.get(Listing, app_row.listing_id)
    return _to_summary(app_row, listing)


@router.post("/{application_id}/project-selection")
def submit_project_selection(
    application_id: str, body: ProjectSelectionRequest, checkpointer=Depends(get_checkpointer)
):
    _parse_uuid(application_id)
    pending = get_pending_review(checkpointer, application_id)
    if pending is None or pending.review_type != "project_selection":
        raise HTTPException(status_code=400, detail="No pending project-selection review for this application")
    try:
        next_review = resume_project_selection(checkpointer, application_id, body.action, body.selected_repo_names)
    except FileNotFoundError:
        # Approving here triggers resume generation, which needs the base
        # profile — a clear message instead of a raw 500 from deep inside
        # the tailoring step.
        raise HTTPException(
            status_code=422, detail="Set up your profile at /profile before approving applications."
        ) from None
    if body.action == "decline":
        # decline_node deletes the Application row but has no safe way to
        # also clear its own checkpoint thread mid-invocation — do it here,
        # after graph.invoke() has fully returned, so every decline is a
        # full clean removal instead of leaving an orphaned thread behind
        # (the asymmetry the new DELETE endpoint below doesn't have).
        checkpointer.delete_thread(application_id)
    return {"application_id": application_id, "next_review": next_review}


@router.post("/{application_id}/final-approval")
def submit_final_approval(application_id: str, body: FinalApprovalRequest, checkpointer=Depends(get_checkpointer)):
    _parse_uuid(application_id)
    pending = get_pending_review(checkpointer, application_id)
    if pending is None or pending.review_type != "final_approval":
        raise HTTPException(status_code=400, detail="No pending final-approval review for this application")
    next_review = resume_final_approval(checkpointer, application_id, body.action)
    if body.action == "decline":
        checkpointer.delete_thread(application_id)
    return {"application_id": application_id, "next_review": next_review}
