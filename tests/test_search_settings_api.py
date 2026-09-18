"""These tests monkeypatch the route's load/save functions to a
pytest tmp_path so they never touch config/search_settings.yaml."""

import app.api.routes.search_settings as search_settings_routes
from app.nodes.scraper.search_settings import load_search_settings as real_load
from app.nodes.scraper.search_settings import save_search_settings as real_save
from fastapi.testclient import TestClient

from app.main import app


def _patch_to_temp_path(monkeypatch, tmp_path):
    temp_path = tmp_path / "search_settings.yaml"
    monkeypatch.setattr(search_settings_routes, "load_search_settings", lambda: real_load(path=temp_path))
    monkeypatch.setattr(search_settings_routes, "save_search_settings", lambda s: real_save(s, path=temp_path))


def test_get_returns_defaults_when_not_set_up(tmp_path, monkeypatch):
    _patch_to_temp_path(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/search-settings")
        assert response.status_code == 200
        assert len(response.json()["search_queries"]) > 0


def test_put_then_get_round_trip(tmp_path, monkeypatch):
    _patch_to_temp_path(monkeypatch, tmp_path)
    with TestClient(app) as client:
        payload = {"search_queries": ["backend intern"], "exclude_keywords": ["sales"]}
        put_response = client.put("/search-settings", json=payload)
        assert put_response.status_code == 200

        get_response = client.get("/search-settings")
        assert get_response.status_code == 200
        assert get_response.json() == payload
