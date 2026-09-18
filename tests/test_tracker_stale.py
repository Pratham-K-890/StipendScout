from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.db.models import Application, ApplicationStatus, Listing
from app.db.session import SessionLocal
from app.nodes.tracker.stale import run_stale_sweep

TEST_SOURCE = "test_tracker_stale"


@pytest.fixture
def session():
    s = SessionLocal()
    yield s
    for app in s.execute(select(Application).join(Listing).where(Listing.source == TEST_SOURCE)).scalars():
        s.delete(app)
    for listing in s.execute(select(Listing).where(Listing.source == TEST_SOURCE)).scalars():
        s.delete(listing)
    s.commit()
    s.close()


def _make_listing(session, external_id: str, disappeared: bool = False) -> Listing:
    listing = Listing(
        source=TEST_SOURCE,
        external_id=external_id,
        title="Test Intern",
        company="Test Co",
        url="https://example.com",
        description="desc",
    )
    if disappeared:
        listing.disappeared_at = datetime.now(timezone.utc)
    session.add(listing)
    session.flush()
    return listing


def _make_application(
    session, listing: Listing, status: ApplicationStatus = ApplicationStatus.PENDING, status_changed_at=None
) -> Application:
    app = Application(listing_id=listing.id, status=status, jd_snapshot={"title": "Test"})
    if status_changed_at:
        app.status_changed_at = status_changed_at
    session.add(app)
    session.flush()
    return app


def test_flags_stale_by_age(session):
    listing = _make_listing(session, "s1")
    old_time = datetime.now(timezone.utc) - timedelta(days=30)
    app = _make_application(session, listing, status_changed_at=old_time)
    session.commit()

    result = run_stale_sweep(session, days_threshold=14)
    assert result.stale_by_age == 1
    session.refresh(app)
    assert app.status == ApplicationStatus.STALE


def test_does_not_flag_recent_pending(session):
    listing = _make_listing(session, "s2")
    app = _make_application(session, listing)
    session.commit()

    result = run_stale_sweep(session, days_threshold=14)
    assert result.total_marked == 0
    session.refresh(app)
    assert app.status == ApplicationStatus.PENDING


def test_flags_stale_by_listing_disappearance_regardless_of_age(session):
    listing = _make_listing(session, "s3", disappeared=True)
    app = _make_application(session, listing)
    session.commit()

    result = run_stale_sweep(session, days_threshold=14)
    assert result.stale_by_disappearance == 1
    session.refresh(app)
    assert app.status == ApplicationStatus.STALE


def test_does_not_flag_non_pending_applications(session):
    listing = _make_listing(session, "s4", disappeared=True)
    app = _make_application(session, listing, status=ApplicationStatus.APPLIED)
    session.commit()

    result = run_stale_sweep(session, days_threshold=14)
    assert result.total_marked == 0
    session.refresh(app)
    assert app.status == ApplicationStatus.APPLIED
