from app.nodes.tailor.profile import load_base_profile, save_base_profile
from app.schemas.profile import BaseProfile, EducationEntry, ExperienceEntry, Links


def _profile() -> BaseProfile:
    return BaseProfile(
        name="Test User",
        email="test@example.com",
        phone="+91-0000000000",
        location="Bengaluru, India",
        links=Links(github="https://github.com/test", linkedin=None, leetcode=None, portfolio=None),
        education=[
            EducationEntry(institution="Test College", degree="B.E.", branch="CS", start_year=2024, end_year=2028)
        ],
        experience=[ExperienceEntry(title="Intern", company="Acme", start_date="2025-06", bullets=["Did a thing."])],
        skills={"Languages": ["Python"], "Frameworks": ["FastAPI"]},
    )


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "profile.yaml"
    original = _profile()
    save_base_profile(original, path=path)
    loaded = load_base_profile(path=path)
    assert loaded == original


def test_load_missing_file_raises(tmp_path):
    path = tmp_path / "does_not_exist.yaml"
    try:
        load_base_profile(path=path)
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
