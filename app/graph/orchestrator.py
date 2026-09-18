import uuid

from langgraph.types import Command
from sqlalchemy import select

from app.db.models import Application, Listing
from app.db.session import SessionLocal
from app.graph.graph import build_graph
from app.nodes.matcher import evaluate_listing
from app.nodes.scraper import get_enabled_sources
from app.nodes.tailor import fetch_project_candidates
from app.nodes.tailor.jd_summary import generate_ai_jd_summary
from app.nodes.tracker import ingest_listings, run_stale_sweep
from app.schemas.jd_summary import JDSummary
from app.schemas.listing import NormalizedListing
from app.schemas.project import ProjectCandidate
from app.schemas.scan import PendingReview, ScanSummary


def _listing_to_normalized(listing: Listing) -> NormalizedListing:
    return NormalizedListing(
        source=listing.source,
        external_id=listing.external_id,
        title=listing.title,
        company=listing.company,
        location=listing.location,
        is_remote=listing.is_remote,
        url=listing.url,
        description=listing.description,
        stipend_amount=listing.stipend_amount,
        stipend_currency=listing.stipend_currency,
    )


def _interrupt_to_pending_review(application_id: str, result: dict) -> PendingReview | None:
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None
    payload = interrupts[0].value
    return PendingReview(application_id=application_id, review_type=payload["type"], payload=payload)


def get_pending_review(checkpointer, application_id: str) -> PendingReview | None:
    """Read-only lookup of whatever this application's graph thread is
    currently paused at, without invoking/advancing it — used so a client
    can re-fetch the review payload later rather than only getting it
    transiently from the call that produced it."""
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": application_id}}
    snapshot = graph.get_state(config)
    for task in snapshot.tasks:
        if task.interrupts:
            payload = task.interrupts[0].value
            return PendingReview(application_id=application_id, review_type=payload["type"], payload=payload)
    return None


def start_application_for_listing(
    checkpointer, listing: Listing, project_candidates: list[ProjectCandidate]
) -> PendingReview | None:
    """Runs the matcher on a Listing; if it passes, creates a PENDING
    Application row and drives the graph to its first interrupt. Returns
    the pending review payload, or None if the listing didn't pass
    matching (no Application row created — nothing to review)."""
    normalized = _listing_to_normalized(listing)
    jd_text = f"{listing.title}\n{listing.description}"
    match_result = evaluate_listing(normalized)
    if not match_result.passes_hard_filters:
        return None

    try:
        ai_summary = generate_ai_jd_summary(jd_text)
    except Exception:  # noqa: BLE001 - enrichment only; a failed LLM call shouldn't block the listing entirely
        ai_summary = {"responsibilities": [], "requirements": [], "duration": None, "benefits": []}

    listing_summary = JDSummary(
        stipend_amount=match_result.stipend_amount,
        stipend_status=match_result.stipend_status,
        location=listing.location,
        is_remote=listing.is_remote,
        ppo_detected=match_result.ppo_detected,
        role_tier=match_result.role_tier.value if match_result.role_tier else None,
        role_similarity=match_result.role_similarity,
        **ai_summary,
    )

    application_id = uuid.uuid4()
    session = SessionLocal()
    try:
        session.add(
            Application(
                id=application_id,
                listing_id=listing.id,
                jd_snapshot={
                    "title": listing.title,
                    "company": listing.company,
                    "description": listing.description,
                    "url": listing.url,
                },
                listing_summary=listing_summary.model_dump(),
            )
        )
        session.commit()
    finally:
        session.close()

    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": str(application_id)}}
    result = graph.invoke(
        {
            "application_id": str(application_id),
            "listing_id": str(listing.id),
            "jd_text": jd_text,
            "company": listing.company,
            "project_candidates": [c.model_dump() for c in project_candidates],
        },
        config=config,
    )
    return _interrupt_to_pending_review(str(application_id), result)


def resume_project_selection(
    checkpointer, application_id: str, action: str, selected_repo_names: list[str]
) -> PendingReview | None:
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": application_id}}
    result = graph.invoke(
        Command(resume={"action": action, "selected_repo_names": selected_repo_names}), config=config
    )
    return _interrupt_to_pending_review(application_id, result)


def resume_final_approval(checkpointer, application_id: str, action: str) -> PendingReview | None:
    graph = build_graph(checkpointer)
    config = {"configurable": {"thread_id": application_id}}
    result = graph.invoke(Command(resume={"action": action}), config=config)
    return _interrupt_to_pending_review(application_id, result)


def run_scan(checkpointer) -> ScanSummary:
    session = SessionLocal()
    try:
        sources_scraped = []
        for source in get_enabled_sources():
            listings = source.fetch()
            ingest_listings(session, source.name, listings)
            sources_scraped.append(source.name)

        run_stale_sweep(session)

        listing_ids_with_application = set(session.execute(select(Application.listing_id)).scalars())
        candidate_listings = (
            session.execute(select(Listing).where(Listing.disappeared_at.is_(None))).scalars().all()
        )
        to_process = [listing for listing in candidate_listings if listing.id not in listing_ids_with_application]
    finally:
        session.close()

    pending_reviews: list[PendingReview] = []
    if to_process:
        project_candidates = fetch_project_candidates()  # fetched once for the whole batch
        for listing in to_process:
            review = start_application_for_listing(checkpointer, listing, project_candidates)
            if review:
                pending_reviews.append(review)

    return ScanSummary(
        sources_scraped=sources_scraped,
        new_applications_started=len(pending_reviews),
        pending_reviews=pending_reviews,
    )
