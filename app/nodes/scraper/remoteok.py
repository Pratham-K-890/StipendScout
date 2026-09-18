import re

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.schemas.listing import NormalizedListing

REMOTEOK_API_URL = "https://remoteok.com/api"

# RemoteOK blocks requests without a browser-like User-Agent.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

_INTERN_PATTERN = re.compile(r"\bintern(ship)?\b", re.IGNORECASE)


def _looks_like_internship(raw_job: dict) -> bool:
    # RemoteOK's "tags" field is a loosely-applied category taxonomy, not
    # listing-specific keywords — jobs get tagged "internship" even when
    # they plainly aren't one (observed: an HR Coordinator role). Title is
    # the only reliable signal.
    position = raw_job.get("position") or ""
    return bool(_INTERN_PATTERN.search(position))


def _strip_html(html: str) -> str:
    text = BeautifulSoup(html or "", "html.parser").get_text(separator=" ")
    return re.sub(r"[ \t]+", " ", text).strip()


def normalize_remoteok_job(raw_job: dict) -> NormalizedListing | None:
    """Pure transform: raw RemoteOK job dict -> NormalizedListing, or None to skip.

    Returns None for the API's leading legal-notice object (no "id" field)
    and for jobs that don't look like internships.
    """
    job_id = raw_job.get("id")
    if not job_id:
        return None
    if not _looks_like_internship(raw_job):
        return None

    salary_min = raw_job.get("salary_min")
    salary_max = raw_job.get("salary_max")
    raw_salary = None
    if salary_min or salary_max:
        # RemoteOK salaries are annual USD figures, not monthly INR — kept
        # as raw reference only, not normalized into stipend_amount.
        raw_salary = {"min": salary_min, "max": salary_max, "currency": "USD", "period": "year"}

    return NormalizedListing(
        source="remoteok",
        external_id=str(job_id),
        title=raw_job.get("position", "").strip(),
        company=raw_job.get("company", "").strip(),
        location=raw_job.get("location") or None,
        is_remote=True,
        url=raw_job.get("url") or f"https://remoteok.com/remote-jobs/{job_id}",
        description=_strip_html(raw_job.get("description", "")),
        stipend_amount=None,
        raw_salary=raw_salary,
    )


@retry(
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def _fetch_raw_jobs() -> list[dict]:
    response = httpx.get(REMOTEOK_API_URL, headers=_HEADERS, timeout=15)
    response.raise_for_status()
    return response.json()


class RemoteOKSource:
    name = "remoteok"

    def is_configured(self) -> bool:
        return True  # public API, no key required

    def fetch(self) -> list[NormalizedListing]:
        raw_jobs = _fetch_raw_jobs()
        listings = [normalize_remoteok_job(job) for job in raw_jobs]
        return [listing for listing in listings if listing is not None]
