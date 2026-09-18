import pytest

from app.nodes.scraper.adzuna import AdzunaSource, is_excluded, normalize_adzuna_job
from app.nodes.scraper.base import NotConfiguredError
from app.schemas.search_settings import SearchSettings

RAW_JOB = {
    "id": 111222333,
    "title": "Backend Developer Intern",
    "company": {"display_name": "Acme India"},
    "location": {"display_name": "Bangalore, Karnataka"},
    "description": "FastAPI backend internship.",
    "redirect_url": "https://www.adzuna.in/details/111222333",
    "salary_min": 180000,
    "salary_max": 240000,
    "salary_is_predicted": "1",
}


def test_normalizes_adzuna_job():
    listing = normalize_adzuna_job(RAW_JOB)
    assert listing.source == "adzuna"
    assert listing.external_id == "111222333"
    assert listing.title == "Backend Developer Intern"
    assert listing.company == "Acme India"
    assert listing.location == "Bangalore, Karnataka"
    assert listing.is_remote is False
    assert listing.stipend_amount is None
    assert listing.raw_salary == {
        "min": 180000,
        "max": 240000,
        "currency": "INR",
        "period": "year",
        "is_predicted": "1",
    }


def test_fetch_raises_when_not_configured(monkeypatch):
    monkeypatch.setattr("app.nodes.scraper.adzuna.settings.adzuna_app_id", "")
    monkeypatch.setattr("app.nodes.scraper.adzuna.settings.adzuna_app_key", "")
    source = AdzunaSource()
    assert source.is_configured() is False
    with pytest.raises(NotConfiguredError):
        source.fetch()


def test_is_excluded_matches_title():
    listing = normalize_adzuna_job(RAW_JOB)
    assert is_excluded(listing, ["backend"]) is True


def test_is_excluded_matches_description():
    listing = normalize_adzuna_job(RAW_JOB)
    assert is_excluded(listing, ["fastapi"]) is True


def test_is_excluded_false_when_no_match():
    listing = normalize_adzuna_job(RAW_JOB)
    assert is_excluded(listing, ["sales", "marketing"]) is False


def test_is_excluded_false_for_empty_list():
    listing = normalize_adzuna_job(RAW_JOB)
    assert is_excluded(listing, []) is False


def test_fetch_queries_each_search_term_and_dedupes(monkeypatch):
    monkeypatch.setattr("app.nodes.scraper.adzuna.settings.adzuna_app_id", "id")
    monkeypatch.setattr("app.nodes.scraper.adzuna.settings.adzuna_app_key", "key")
    monkeypatch.setattr(
        "app.nodes.scraper.adzuna.load_search_settings",
        lambda: SearchSettings(search_queries=["backend intern", "ml intern"], exclude_keywords=["sales"]),
    )

    calls = []

    def fake_fetch(app_id, app_key, what, where):
        calls.append(what)
        if what == "backend intern":
            return [
                {**RAW_JOB, "id": 1, "title": "Backend Intern"},
                {**RAW_JOB, "id": 2, "title": "Sales Intern"},
            ]
        return [
            {**RAW_JOB, "id": 1, "title": "Backend Intern"},  # duplicate across queries
            {**RAW_JOB, "id": 3, "title": "ML Intern"},
        ]

    monkeypatch.setattr("app.nodes.scraper.adzuna._fetch_raw_jobs", fake_fetch)

    source = AdzunaSource()
    results = source.fetch()

    assert calls == ["backend intern", "ml intern"]
    assert {r.external_id for r in results} == {"1", "3"}  # id 2 excluded (sales), id 1 deduped
