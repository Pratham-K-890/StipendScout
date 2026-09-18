from pathlib import Path

import yaml

from app.schemas.search_settings import SearchSettings

DEFAULT_SEARCH_SETTINGS_PATH = Path("config/search_settings.yaml")

# Matches the original role priority order (backend > classical ML/DS >
# AI-agent) — deliberately targeted queries instead of a single generic
# "intern" search, which pulls in mostly sales/HR/marketing noise (we've
# seen live batches where 0 of 50 generic results passed the matcher).
DEFAULT_SEARCH_QUERIES = [
    "backend developer intern",
    "python developer intern",
    "machine learning intern",
    "data science intern",
    "AI agent intern",
]


def load_search_settings(path: Path = DEFAULT_SEARCH_SETTINGS_PATH) -> SearchSettings:
    if not path.exists():
        return SearchSettings(search_queries=list(DEFAULT_SEARCH_QUERIES), exclude_keywords=[])
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return SearchSettings.model_validate(data)


def save_search_settings(settings: SearchSettings, path: Path = DEFAULT_SEARCH_SETTINGS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            settings.model_dump(mode="json"),
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
