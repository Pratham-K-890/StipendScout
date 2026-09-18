from app.nodes.tailor.source_pool import build_source_pool
from app.schemas.profile import BaseProfile, EducationEntry, ExperienceEntry, HackathonEntry, Links, ResponsibilityEntry
from app.schemas.project import ProjectCandidate


def _profile() -> BaseProfile:
    return BaseProfile(
        name="Test User",
        email="test@example.com",
        links=Links(),
        education=[EducationEntry(institution="Test College", degree="B.E.")],
        experience=[
            ExperienceEntry(
                title="Intern",
                company="Acme",
                start_date="2025-06",
                bullets=["Did a real thing.", "Did another real thing."],
            )
        ],
        hackathons=[
            HackathonEntry(title="Hack Fest", event="Hack Fest 2026", bullets=["Won 2nd place."])
        ],
        responsibilities=[
            ResponsibilityEntry(title="Volunteer", organization="Club", bullets=["Helped organize events."])
        ],
        skills={"Languages": ["Python"]},
    )


def _project() -> ProjectCandidate:
    return ProjectCandidate(
        repo_name="my-project",
        description="A tool that does X.",
        readme_excerpt="More detail about how it does X using Y.",
        topics=[],
        language="Python",
        url="https://github.com/user/my-project",
        is_private=False,
        is_fork=False,
        stars=0,
        updated_at="2026-01-01T00:00:00Z",
    )


def test_builds_one_item_per_bullet():
    pool = build_source_pool(_profile(), [])
    assert len(pool) == 4  # 2 experience + 1 hackathon + 1 responsibility
    assert {item.source_type for item in pool} == {"experience", "hackathon", "responsibility"}


def test_includes_selected_projects():
    pool = build_source_pool(_profile(), [_project()])
    project_items = [item for item in pool if item.source_type == "project"]
    assert len(project_items) == 1
    assert project_items[0].source_ref == "my-project"
    assert "does X" in project_items[0].excerpt


def test_excludes_projects_with_no_content():
    empty_project = ProjectCandidate(
        repo_name="empty",
        description=None,
        readme_excerpt="",
        topics=[],
        language=None,
        url=None,
        is_private=False,
        is_fork=False,
        stars=0,
        updated_at="2026-01-01T00:00:00Z",
    )
    pool = build_source_pool(_profile(), [empty_project])
    assert not any(item.source_ref == "empty" for item in pool)
