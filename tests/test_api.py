import app.api.routes.applications as applications_routes
from fastapi.testclient import TestClient

from app.exceptions import NotConfiguredError
from app.main import app
from app.schemas.scan import PendingReview


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_applications_list_returns_200():
    with TestClient(app) as client:
        response = client.get("/applications")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_applications_invalid_status_filter_returns_400():
    with TestClient(app) as client:
        response = client.get("/applications?status=bogus")
        assert response.status_code == 400


def test_get_nonexistent_application_returns_404():
    with TestClient(app) as client:
        response = client.get("/applications/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


def test_get_malformed_application_id_returns_404():
    with TestClient(app) as client:
        response = client.get("/applications/not-a-uuid")
        assert response.status_code == 404


def test_project_selection_with_no_pending_review_returns_400():
    with TestClient(app) as client:
        response = client.post(
            "/applications/00000000-0000-0000-0000-000000000000/project-selection",
            json={"action": "approve", "selected_repo_names": []},
        )
        assert response.status_code == 400


def test_final_approval_with_no_pending_review_returns_400():
    with TestClient(app) as client:
        response = client.post(
            "/applications/00000000-0000-0000-0000-000000000000/final-approval",
            json={"action": "approve"},
        )
        assert response.status_code == 400


def test_status_update_on_nonexistent_application_returns_404():
    with TestClient(app) as client:
        response = client.patch(
            "/applications/00000000-0000-0000-0000-000000000000/status",
            json={"status": "interview"},
        )
        assert response.status_code == 404


def test_status_update_rejects_invalid_status():
    with TestClient(app) as client:
        response = client.patch(
            "/applications/00000000-0000-0000-0000-000000000000/status",
            json={"status": "bogus"},
        )
        assert response.status_code == 422


def test_resume_pdf_for_nonexistent_application_returns_404():
    with TestClient(app) as client:
        response = client.get("/applications/00000000-0000-0000-0000-000000000000/resume.pdf")
        assert response.status_code == 404


def test_project_selection_without_profile_returns_helpful_422(monkeypatch):
    # Simulates approving gate 1 before resume/base_profile.yaml exists —
    # tailor_node's load_base_profile() would raise FileNotFoundError deep
    # inside the graph; the route must turn that into a clear message
    # instead of a raw 500.
    fake_id = "00000000-0000-0000-0000-000000000000"
    monkeypatch.setattr(
        applications_routes,
        "get_pending_review",
        lambda checkpointer, application_id: PendingReview(
            application_id=fake_id, review_type="project_selection", payload={"type": "project_selection"}
        ),
    )

    def raise_not_found(checkpointer, application_id, action, selected_repo_names):
        raise FileNotFoundError("resume/base_profile.yaml not found")

    monkeypatch.setattr(applications_routes, "resume_project_selection", raise_not_found)

    with TestClient(app) as client:
        response = client.post(
            f"/applications/{fake_id}/project-selection",
            json={"action": "approve", "selected_repo_names": []},
        )
        assert response.status_code == 422
        assert "/profile" in response.json()["detail"]


def test_not_configured_error_returns_503_with_its_message(monkeypatch):
    fake_id = "00000000-0000-0000-0000-000000000000"
    monkeypatch.setattr(
        applications_routes,
        "get_pending_review",
        lambda checkpointer, application_id: PendingReview(
            application_id=fake_id, review_type="project_selection", payload={"type": "project_selection"}
        ),
    )

    def raise_not_configured(checkpointer, application_id, action, selected_repo_names):
        raise NotConfiguredError("GITHUB_TOKEN is required in .env (a personal access token).")

    monkeypatch.setattr(applications_routes, "resume_project_selection", raise_not_configured)

    with TestClient(app) as client:
        response = client.post(
            f"/applications/{fake_id}/project-selection",
            json={"action": "approve", "selected_repo_names": []},
        )
        assert response.status_code == 503
        assert response.json() == {"detail": "GITHUB_TOKEN is required in .env (a personal access token)."}


def test_unhandled_exception_returns_json_500_with_cors_headers(monkeypatch):
    # Confirms the global handler intercepts inside CORSMiddleware, not
    # Starlette's outer ServerErrorMiddleware — without it this response
    # would be plain text with no CORS headers, and the frontend's shared
    # error handler would see a network error instead of a readable one.
    fake_id = "00000000-0000-0000-0000-000000000000"
    monkeypatch.setattr(
        applications_routes,
        "get_pending_review",
        lambda checkpointer, application_id: PendingReview(
            application_id=fake_id, review_type="project_selection", payload={"type": "project_selection"}
        ),
    )

    def raise_unexpected(checkpointer, application_id, action, selected_repo_names):
        raise RuntimeError("All OpenRouter models failed.")

    monkeypatch.setattr(applications_routes, "resume_project_selection", raise_unexpected)

    with TestClient(app) as client:
        response = client.post(
            f"/applications/{fake_id}/project-selection",
            json={"action": "approve", "selected_repo_names": []},
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_declining_project_selection_deletes_checkpoint_thread(monkeypatch):
    # decline_node deletes the Application row but can't safely clear its
    # own checkpoint thread mid-invocation — the route does it afterward.
    # Previously this never happened at all, leaving an orphaned thread
    # behind on every decline.
    fake_id = "00000000-0000-0000-0000-000000000000"
    monkeypatch.setattr(
        applications_routes,
        "get_pending_review",
        lambda checkpointer, application_id: PendingReview(
            application_id=fake_id, review_type="project_selection", payload={"type": "project_selection"}
        ),
    )
    monkeypatch.setattr(applications_routes, "resume_project_selection", lambda *a, **k: None)

    deleted_threads = []
    fake_checkpointer = type("FakeCheckpointer", (), {"delete_thread": lambda self, tid: deleted_threads.append(tid)})()
    app.dependency_overrides[applications_routes.get_checkpointer] = lambda: fake_checkpointer
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/applications/{fake_id}/project-selection",
                json={"action": "decline", "selected_repo_names": []},
            )
        assert response.status_code == 200
        assert deleted_threads == [fake_id]
    finally:
        app.dependency_overrides.pop(applications_routes.get_checkpointer, None)


def test_approving_project_selection_does_not_delete_checkpoint_thread(monkeypatch):
    fake_id = "00000000-0000-0000-0000-000000000000"
    monkeypatch.setattr(
        applications_routes,
        "get_pending_review",
        lambda checkpointer, application_id: PendingReview(
            application_id=fake_id, review_type="project_selection", payload={"type": "project_selection"}
        ),
    )
    monkeypatch.setattr(applications_routes, "resume_project_selection", lambda *a, **k: None)

    deleted_threads = []
    fake_checkpointer = type("FakeCheckpointer", (), {"delete_thread": lambda self, tid: deleted_threads.append(tid)})()
    app.dependency_overrides[applications_routes.get_checkpointer] = lambda: fake_checkpointer
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/applications/{fake_id}/project-selection",
                json={"action": "approve", "selected_repo_names": []},
            )
        assert response.status_code == 200
        assert deleted_threads == []
    finally:
        app.dependency_overrides.pop(applications_routes.get_checkpointer, None)
