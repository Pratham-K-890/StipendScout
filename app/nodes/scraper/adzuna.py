import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.nodes.scraper.base import NotConfiguredError
from app.nodes.scraper.search_settings import load_search_settings
from app.schemas.listing import NormalizedListing

ADZUNA_SEARCH_URL = "https://api.adzuna.com/v1/api/jobs/in/search/1"
SEARCH_LOCATION = "Bangalore"


def normalize_adzuna_job(raw_job: dict) -> NormalizedListing:
    """Pure transform: raw Adzuna job dict -> NormalizedListing."""
    location = ((raw_job.get("location") or {}).get("display_name")) or None
    company = ((raw_job.get("company") or {}).get("display_name")) or ""

    salary_min = raw_job.get("salary_min")
    salary_max = raw_job.get("salary_max")
    raw_salary = None
    if salary_min or salary_max:
        # Adzuna salary figures are annual INR estimates, often predicted
        # rather than stated — kept as raw reference, not treated as a
        # confirmed monthly stipend.
        raw_salary = {
            "min": salary_min,
            "max": salary_max,
            "currency": "INR",
            "period": "year",
            "is_predicted": raw_job.get("salary_is_predicted"),
        }

    return NormalizedListing(
        source="adzuna",
        external_id=str(raw_job.get("id")),
        title=raw_job.get("title", "").strip(),
        company=company.strip(),
        location=location,
        is_remote=False,
        url=raw_job.get("redirect_url", ""),
        description=(raw_job.get("description") or "").strip(),
        stipend_amount=None,
        raw_salary=raw_salary,
    )


@retry(
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def _fetch_raw_jobs(app_id: str, app_key: str, what: str, where: str) -> list[dict]:
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": what,
        "where": where,
        "results_per_page": 50,
        "max_days_old": 45,
        "content-type": "application/json",
    }
    response = httpx.get(ADZUNA_SEARCH_URL, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("results", [])


def is_excluded(listing: NormalizedListing, exclude_keywords: list[str]) -> bool:
    keywords = [kw.strip().lower() for kw in exclude_keywords if kw.strip()]
    if not keywords:
        return False
    haystack = f"{listing.title} {listing.description}".lower()
    return any(keyword in haystack for keyword in keywords)


class AdzunaSource:
    name = "adzuna"

    def is_configured(self) -> bool:
        return bool(settings.adzuna_app_id and settings.adzuna_app_key)

    def fetch(self) -> list[NormalizedListing]:
        if not self.is_configured():
            raise NotConfiguredError(
                "Adzuna requires ADZUNA_APP_ID and ADZUNA_APP_KEY in .env "
                "(free signup at developer.adzuna.com)."
            )
        search_settings = load_search_settings()

        seen_ids: set[str] = set()
        listings: list[NormalizedListing] = []
        for query in search_settings.search_queries:
            raw_jobs = _fetch_raw_jobs(settings.adzuna_app_id, settings.adzuna_app_key, what=query, where=SEARCH_LOCATION)
            for raw_job in raw_jobs:
                job_id = str(raw_job.get("id"))
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                listing = normalize_adzuna_job(raw_job)
                if is_excluded(listing, search_settings.exclude_keywords):
                    continue
                listings.append(listing)
        return listings
