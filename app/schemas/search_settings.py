from pydantic import BaseModel


class SearchSettings(BaseModel):
    search_queries: list[str]
    exclude_keywords: list[str] = []
