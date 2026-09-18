from pydantic import BaseModel


class EducationEntry(BaseModel):
    institution: str
    degree: str
    branch: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    cgpa: str | None = None


class ExperienceEntry(BaseModel):
    title: str
    company: str
    start_date: str
    end_date: str | None = None  # None = ongoing
    bullets: list[str]


class Links(BaseModel):
    linkedin: str | None = None
    github: str | None = None
    leetcode: str | None = None
    portfolio: str | None = None


class HackathonEntry(BaseModel):
    title: str
    event: str
    team_project: bool = False
    bullets: list[str]


class ResponsibilityEntry(BaseModel):
    title: str
    organization: str
    bullets: list[str]


class BaseProfile(BaseModel):
    name: str
    email: str
    phone: str | None = None
    location: str | None = None
    links: Links
    education: list[EducationEntry]
    experience: list[ExperienceEntry] = []
    hackathons: list[HackathonEntry] = []
    responsibilities: list[ResponsibilityEntry] = []
    # Category name -> skills in that category, e.g. {"Languages": ["Python", ...]}.
    # Order is meaningful (both category order and within-category order) —
    # it's what the resume renders, so it's preserved end to end, never
    # alphabetized or otherwise reordered.
    skills: dict[str, list[str]]
