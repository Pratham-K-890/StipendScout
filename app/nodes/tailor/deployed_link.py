import re

# Matches a markdown link's URL, a backtick-wrapped URL, or a bare URL.
_URL_PATTERN = re.compile(r"\[[^\]]*\]\((https?://[^\s)]+)\)|`(https?://[^\s`]+)`|(https?://[^\s`)]+)")
_LIVE_KEYWORDS = re.compile(r"\b(live|demo|deployed)\b", re.IGNORECASE)
_EXCLUDED_HOSTS = ("github.com", "shields.io", "badge.fury.io", "img.shields.io")


def extract_deployed_url(readme_text: str) -> str | None:
    """Finds a live/demo/deployed URL stated in the README (e.g. "**Live
    API:** `https://...`"), if any. A URL only counts if one of
    live/demo/deployed appears in the ~40 characters right before it —
    otherwise this would pick up any random link (badges, docs, the repo
    itself) rather than an actual deployment."""
    for match in _URL_PATTERN.finditer(readme_text):
        url = match.group(1) or match.group(2) or match.group(3)
        if not url:
            continue
        if any(host in url for host in _EXCLUDED_HOSTS):
            continue
        preceding = readme_text[max(0, match.start() - 40) : match.start()]
        if _LIVE_KEYWORDS.search(preceding):
            return url
    return None
