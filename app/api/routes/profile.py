from fastapi import APIRouter, HTTPException

from app.nodes.tailor.profile import load_base_profile, save_base_profile
from app.schemas.profile import BaseProfile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=BaseProfile)
def get_profile():
    try:
        return load_base_profile()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No profile set up yet") from None


@router.put("", response_model=BaseProfile)
def update_profile(profile: BaseProfile):
    save_base_profile(profile)
    return profile
