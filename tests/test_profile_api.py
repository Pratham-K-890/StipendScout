"""IMPORTANT: these tests monkeypatch the profile route's load/save
functions to a pytest tmp_path so they never touch the real
resume/base_profile.yaml — do not remove that patching."""

import app.api.routes.profile as profile_routes
from app.nodes.tailor.profile import load_base_profile as real_load
from app.nodes.tailor.profile import save_base_profile as real_save
from fastapi.testclient import TestClient

from app.main import app

PAYLOAD = {
    "name": "Test User",
    "email": "test@example.com",
    "phone": None,
    "location": None,
    "links": {"linkedin": None, "github": None, "leetcode": None, "portfolio": None},
    "education": [
        {
            "institution": "Test College",
            "degree": "B.E.",
            "branch": None,
            "start_year": None,
            "end_year": None,
            "cgpa": None,
        }
    ],
    "experience": [],
    "hackathons": [],
    "responsibilities": [],
    "skills": {"Languages": ["Python"]},
}


def _patch_to_temp_path(monkeypatch, tmp_path):
    temp_path = tmp_path / "profile.yaml"
    monkeypatch.setattr(profile_routes, "load_base_profile", lambda: real_load(path=temp_path))
    monkeypatch.setattr(profile_routes, "save_base_profile", lambda p: real_save(p, path=temp_path))


def test_get_profile_404_when_not_set_up(tmp_path, monkeypatch):
    _patch_to_temp_path(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/profile")
        assert response.status_code == 404


def test_put_then_get_round_trip(tmp_path, monkeypatch):
    _patch_to_temp_path(monkeypatch, tmp_path)
    with TestClient(app) as client:
        put_response = client.put("/profile", json=PAYLOAD)
        assert put_response.status_code == 200
        assert put_response.json()["name"] == "Test User"

        get_response = client.get("/profile")
        assert get_response.status_code == 200
        assert get_response.json()["skills"] == {"Languages": ["Python"]}
