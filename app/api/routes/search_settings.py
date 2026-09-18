from fastapi import APIRouter

from app.nodes.scraper.search_settings import load_search_settings, save_search_settings
from app.schemas.search_settings import SearchSettings

router = APIRouter(prefix="/search-settings", tags=["search-settings"])


@router.get("", response_model=SearchSettings)
def get_search_settings():
    return load_search_settings()


@router.put("", response_model=SearchSettings)
def update_search_settings(settings: SearchSettings):
    save_search_settings(settings)
    return settings
