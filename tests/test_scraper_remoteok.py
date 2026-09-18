from app.nodes.scraper.remoteok import normalize_remoteok_job

LEGAL_NOTICE = {"legal": "https://remoteok.com/legal"}

INTERN_JOB = {
    "id": "1234567",
    "position": "Backend Engineer Intern",
    "company": "Acme Corp",
    "tags": ["python", "intern", "backend"],
    "location": "Worldwide",
    "description": "<p>Build <b>FastAPI</b> services.</p>",
    "url": "https://remoteok.com/remote-jobs/1234567",
    "salary_min": 20000,
    "salary_max": 40000,
}

SENIOR_JOB = {
    "id": "7654321",
    "position": "Senior Staff Engineer",
    "company": "BigTech",
    "tags": ["python", "senior"],
    "location": "Worldwide",
    "description": "<p>Lead the platform team.</p>",
    "url": "https://remoteok.com/remote-jobs/7654321",
}


def test_skips_legal_notice_entry():
    assert normalize_remoteok_job(LEGAL_NOTICE) is None


def test_skips_non_internship_roles():
    assert normalize_remoteok_job(SENIOR_JOB) is None


def test_normalizes_internship_role():
    listing = normalize_remoteok_job(INTERN_JOB)
    assert listing is not None
    assert listing.source == "remoteok"
    assert listing.external_id == "1234567"
    assert listing.title == "Backend Engineer Intern"
    assert listing.company == "Acme Corp"
    assert listing.is_remote is True
    assert "FastAPI services" in listing.description
    assert "<b>" not in listing.description
    # Annual USD salary is not treated as a confirmed monthly INR stipend.
    assert listing.stipend_amount is None
    assert listing.raw_salary == {"min": 20000, "max": 40000, "currency": "USD", "period": "year"}


def test_matches_internship_via_title_when_untagged():
    job = {**SENIOR_JOB, "id": "999", "position": "Data Science Intern", "tags": ["python"]}
    listing = normalize_remoteok_job(job)
    assert listing is not None
    assert listing.title == "Data Science Intern"
