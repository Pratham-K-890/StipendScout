import pytest
from sqlalchemy import select

from app.db.models import Listing
from app.db.session import SessionLocal
from app.nodes.tracker.ingest import ingest_listings
from app.schemas.listing import NormalizedListing

TEST_SOURCE = "test_tracker_ingest"


@pytest.fixture
def session():
    s = SessionLocal()
    yield s
    for row in s.execute(select(Listing).where(Listing.source == TEST_SOURCE)).scalars():
        s.delete(row)
    s.commit()
    s.close()


def _listing(external_id: str, title: str = "Test Intern") -> NormalizedListing:
    return NormalizedListing(
        source=TEST_SOURCE,
        external_id=external_id,
        title=title,
        company="Test Co",
        location="Bengaluru",
        is_remote=False,
        url=f"https://example.com/{external_id}",
        description="A test listing description.",
    )


def test_ingest_creates_new_listings(session):
    summary = ingest_listings(session, TEST_SOURCE, [_listing("a1"), _listing("a2")])
    assert summary.new == 2
    assert summary.updated == 0
    assert summary.disappeared == 0

    rows = session.execute(select(Listing).where(Listing.source == TEST_SOURCE)).scalars().all()
    assert len(rows) == 2
    assert all(row.description_embedding is not None for row in rows)


def test_ingest_updates_existing_and_marks_disappeared(session):
    ingest_listings(session, TEST_SOURCE, [_listing("a1"), _listing("a2")])

    summary = ingest_listings(session, TEST_SOURCE, [_listing("a1", title="Updated Title"), _listing("a3")])
    assert summary.new == 1
    assert summary.updated == 1
    assert summary.disappeared == 1

    a1 = session.execute(
        select(Listing).where(Listing.source == TEST_SOURCE, Listing.external_id == "a1")
    ).scalar_one()
    assert a1.title == "Updated Title"
    assert a1.disappeared_at is None

    a2 = session.execute(
        select(Listing).where(Listing.source == TEST_SOURCE, Listing.external_id == "a2")
    ).scalar_one()
    assert a2.disappeared_at is not None


def test_empty_scrape_run_does_not_mark_everything_disappeared(session):
    ingest_listings(session, TEST_SOURCE, [_listing("a1")])
    summary = ingest_listings(session, TEST_SOURCE, [])
    assert summary.skipped_empty_run is True

    a1 = session.execute(
        select(Listing).where(Listing.source == TEST_SOURCE, Listing.external_id == "a1")
    ).scalar_one()
    assert a1.disappeared_at is None


def test_reappearing_listing_clears_disappeared_at(session):
    ingest_listings(session, TEST_SOURCE, [_listing("a1"), _listing("a2")])
    ingest_listings(session, TEST_SOURCE, [_listing("a1")])  # a2 disappears

    a2 = session.execute(
        select(Listing).where(Listing.source == TEST_SOURCE, Listing.external_id == "a2")
    ).scalar_one()
    assert a2.disappeared_at is not None

    ingest_listings(session, TEST_SOURCE, [_listing("a1"), _listing("a2")])  # a2 reappears
    session.refresh(a2)
    assert a2.disappeared_at is None
