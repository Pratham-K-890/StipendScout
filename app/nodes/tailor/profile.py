from pathlib import Path

import yaml

from app.schemas.profile import BaseProfile

DEFAULT_PROFILE_PATH = Path("resume/base_profile.yaml")


def load_base_profile(path: Path = DEFAULT_PROFILE_PATH) -> BaseProfile:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy resume/base_profile.example.yaml to "
            f"{path} and fill in your real details."
        )
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return BaseProfile.model_validate(data)


def save_base_profile(profile: BaseProfile, path: Path = DEFAULT_PROFILE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            profile.model_dump(mode="json"),
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
