from pydantic import BaseModel


class ProjectCandidate(BaseModel):
    repo_name: str
    description: str | None
    readme_excerpt: str
    topics: list[str]
    language: str | None
    url: str | None  # None for private repos — a dead link is worse than no link
    deployed_url: str | None = None  # live/demo URL, extracted from the README if stated
    is_private: bool
    is_fork: bool
    stars: int
    updated_at: str


class RankedProject(BaseModel):
    project: ProjectCandidate
    similarity: float
