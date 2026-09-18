"""Live-DB regression test: GET /applications/{id} must normalize a
legacy-shaped (flat-list) stored tailored_resume the same way
GET .../resume.pdf already does — confirmed live that json.loads() bypassed
TailoredResume's backward-compat validator and returned highlighted_skills
as a bare list for pre-migration applications."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Application, Listing
from app.db.session import SessionLocal
from app.main import app

TEST_SOURCE = "test_legacy_resume_detail"

_LEGACY_TAILORED_RESUME = {
    "name": "Test User",
    "email": "test@example.com",
    "phone": None,
    "location": None,
    "links": {"linkedin": None, "github": None, "leetcode": None, "portfolio": None},
    "education_summary": ["B.E. Testing"],
    "highlighted_skills": ["Python", "FastAPI"],  # the old flat shape
    "bullets": [],
}


@pytest.fixture
def seeded_legacy_application():
    session = SessionLocal()
    listing = Listing(
        source=TEST_SOURCE,
        external_id="legacy-resume-detail",
        title="Test Intern",
        company="Test Co",
        location="Bengaluru",
        is_remote=False,
        url="https://example.com/legacy-resume-detail",
        description="test",
    )
    session.add(listing)
    session.flush()
    application = Application(
        listing_id=listing.id,
        jd_snapshot={"description": "test"},
        tailored_resume=json.dumps(_LEGACY_TAILORED_RESUME),
    )
    session.add(application)
    session.commit()
    application_id = str(application.id)
    session.close()

    yield application_id

    cleanup_session = SessionLocal()
    for row in cleanup_session.execute(select(Listing).where(Listing.source == TEST_SOURCE)).scalars():
        for app_row in cleanup_session.execute(
            select(Application).where(Application.listing_id == row.id)
        ).scalars():
            cleanup_session.delete(app_row)
        cleanup_session.delete(row)
    cleanup_session.commit()
    cleanup_session.close()


def test_get_application_normalizes_legacy_flat_skill_list(seeded_legacy_application):
    with TestClient(app) as client:
        response = client.get(f"/applications/{seeded_legacy_application}")
        assert response.status_code == 200
        skills = response.json()["tailored_resume"]["highlighted_skills"]
        assert skills == {"Skills": ["Python", "FastAPI"]}
