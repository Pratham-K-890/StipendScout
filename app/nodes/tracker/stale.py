from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Application, ApplicationStatus, Listing
from app.schemas.tracker import StaleSweepResult

DEFAULT_STALE_AFTER_DAYS = 14


def run_stale_sweep(session: Session, days_threshold: int = DEFAULT_STALE_AFTER_DAYS) -> StaleSweepResult:
    """Marks PENDING applications STALE on two independent signals: the
    application has sat PENDING past the age threshold, or its listing
    has disappeared from the source entirely (a much stronger signal,
    independent of how long it's been — a vanished listing is stale
    regardless of age)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_threshold)

    stale_by_age = list(
        session.execute(
            select(Application).where(
                Application.status == ApplicationStatus.PENDING,
                Application.status_changed_at < cutoff,
            )
        ).scalars()
    )

    stale_by_disappearance = list(
        session.execute(
            select(Application)
            .join(Listing, Application.listing_id == Listing.id)
            .where(
                Application.status == ApplicationStatus.PENDING,
                Listing.disappeared_at.is_not(None),
            )
        ).scalars()
    )

    all_stale = {app.id: app for app in [*stale_by_age, *stale_by_disappearance]}
    for app in all_stale.values():
        app.status = ApplicationStatus.STALE

    session.commit()
    return StaleSweepResult(
        stale_by_age=len(stale_by_age),
        stale_by_disappearance=len(stale_by_disappearance),
        total_marked=len(all_stale),
    )
