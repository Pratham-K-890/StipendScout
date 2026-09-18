"""Live-DB test for DELETE /applications/{id} — needs a real Application row
and the real checkpointer (delete_thread touches real checkpoint tables), so
it seeds and tears down a row tagged with a distinctive source, same
convention as tests/test_tracker_ingest.py."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Application, Listing
from app.db.session import SessionLocal
from app.main import app

TEST_SOURCE = "test_application_delete"


@pytest.fixture
def seeded_application():
    session = SessionLocal()
    listing = Listing(
        source=TEST_SOURCE,
        external_id="delete-endpoint-test",
        title="Test Intern",
        company="Test Co",
        location="Bengaluru",
        is_remote=False,
        url="https://example.com/delete-endpoint-test",
        description="A test listing for the delete endpoint.",
    )
    session.add(listing)
    session.flush()
    application = Application(listing_id=listing.id, jd_snapshot={"description": "test"})
    session.add(application)
    session.commit()
    application_id = str(application.id)
    session.close()

    yield application_id

    # Defensive cleanup in case the test failed before reaching the delete
    # call — Application has a non-cascading FK to Listing, so any leftover
    # Application row must go first or the Listing delete would violate it.
    cleanup_session = SessionLocal()
    test_listings = cleanup_session.execute(select(Listing).where(Listing.source == TEST_SOURCE)).scalars().all()
    listing_ids = [listing.id for listing in test_listings]
    for row in cleanup_session.execute(select(Application).where(Application.listing_id.in_(listing_ids))).scalars():
        cleanup_session.delete(row)
    for listing in test_listings:
        cleanup_session.delete(listing)
    cleanup_session.commit()
    cleanup_session.close()


def test_delete_application_removes_it(seeded_application):
    with TestClient(app) as client:
        response = client.delete(f"/applications/{seeded_application}")
        assert response.status_code == 204

        get_response = client.get(f"/applications/{seeded_application}")
        assert get_response.status_code == 404


def test_delete_nonexistent_application_returns_404():
    fake_id = str(uuid.uuid4())
    with TestClient(app) as client:
        response = client.delete(f"/applications/{fake_id}")
        assert response.status_code == 404
