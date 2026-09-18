from app.nodes.scraper.search_settings import DEFAULT_SEARCH_QUERIES, load_search_settings, save_search_settings
from app.schemas.search_settings import SearchSettings


def test_load_returns_defaults_when_missing(tmp_path):
    path = tmp_path / "does_not_exist.yaml"
    settings = load_search_settings(path=path)
    assert settings.search_queries == DEFAULT_SEARCH_QUERIES
    assert settings.exclude_keywords == []


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "search_settings.yaml"
    original = SearchSettings(search_queries=["backend intern", "ml intern"], exclude_keywords=["sales"])
    save_search_settings(original, path=path)
    loaded = load_search_settings(path=path)
    assert loaded == original
