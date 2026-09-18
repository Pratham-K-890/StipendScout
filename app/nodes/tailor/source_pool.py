from app.schemas.profile import BaseProfile
from app.schemas.project import ProjectCandidate
from app.schemas.tailored_resume import SourceItem

PROJECT_README_EXCERPT_CHARS = 400


def build_source_pool(profile: BaseProfile, selected_projects: list[ProjectCandidate]) -> list[SourceItem]:
    """Every atomic, factual claim the tailor is allowed to draw from,
    each tagged with exactly where it came from. Nothing outside this
    pool should ever end up on the generated resume/cover letter."""
    items: list[SourceItem] = []

    for exp in profile.experience:
        for bullet in exp.bullets:
            items.append(
                SourceItem(source_type="experience", source_ref=f"{exp.title} at {exp.company}", excerpt=bullet)
            )

    for hackathon in profile.hackathons:
        for bullet in hackathon.bullets:
            items.append(
                SourceItem(
                    source_type="hackathon",
                    source_ref=f"{hackathon.title} ({hackathon.event})",
                    excerpt=bullet,
                )
            )

    for responsibility in profile.responsibilities:
        for bullet in responsibility.bullets:
            items.append(
                SourceItem(
                    source_type="responsibility",
                    source_ref=f"{responsibility.title}, {responsibility.organization}",
                    excerpt=bullet,
                )
            )

    for project in selected_projects:
        excerpt = project.description or ""
        if project.readme_excerpt:
            excerpt = f"{excerpt} {project.readme_excerpt[:PROJECT_README_EXCERPT_CHARS]}".strip()
        if excerpt:
            items.append(SourceItem(source_type="project", source_ref=project.repo_name, excerpt=excerpt))

    return items
