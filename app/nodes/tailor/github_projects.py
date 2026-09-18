import base64

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.exceptions import NotConfiguredError
from app.nodes.tailor.deployed_link import extract_deployed_url
from app.schemas.project import ProjectCandidate

GITHUB_API = "https://api.github.com"
README_MAX_CHARS = 1500


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


@retry(
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def _get(url: str, params: dict | None = None) -> httpx.Response:
    response = httpx.get(url, headers=_headers(), params=params, timeout=15)
    response.raise_for_status()
    return response


def _list_owned_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        batch = _get(
            f"{GITHUB_API}/user/repos",
            params={"per_page": 100, "page": page, "affiliation": "owner"},
        ).json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def _fetch_readme(full_name: str) -> str:
    try:
        response = httpx.get(f"{GITHUB_API}/repos/{full_name}/readme", headers=_headers(), timeout=15)
    except httpx.TransportError:
        return ""
    if response.status_code == 404:
        return ""
    response.raise_for_status()
    content_b64 = response.json().get("content", "")
    try:
        return base64.b64decode(content_b64).decode("utf-8", errors="ignore")
    except (ValueError, UnicodeDecodeError):
        return ""


def fetch_project_candidates(include_forks: bool = False) -> list[ProjectCandidate]:
    if not settings.github_token:
        raise NotConfiguredError("GITHUB_TOKEN is required in .env (a personal access token).")

    candidates: list[ProjectCandidate] = []
    for repo in _list_owned_repos():
        if repo.get("fork") and not include_forks:
            continue

        # GitHub's special "profile README" repo is named exactly like the
        # owner's username and renders as a bio on the profile page — it's
        # not a project and shouldn't be ranked as one.
        owner_login = (repo.get("owner") or {}).get("login", "")
        if repo["name"].lower() == owner_login.lower():
            continue

        description = repo.get("description")
        readme = _fetch_readme(repo["full_name"])
        if not description and not readme:
            continue  # nothing to describe, skip

        is_private = bool(repo.get("private", False))
        candidates.append(
            ProjectCandidate(
                repo_name=repo["name"],
                description=description,
                readme_excerpt=readme[:README_MAX_CHARS],
                topics=repo.get("topics", []) or [],
                language=repo.get("language"),
                url=None if is_private else repo.get("html_url"),
                deployed_url=extract_deployed_url(readme),  # full readme, before truncation
                is_private=is_private,
                is_fork=bool(repo.get("fork", False)),
                stars=repo.get("stargazers_count", 0),
                updated_at=repo.get("updated_at", ""),
            )
        )
    return candidates
