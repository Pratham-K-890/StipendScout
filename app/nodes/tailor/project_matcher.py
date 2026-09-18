import re

from app.nodes.matcher.embeddings import cosine_similarity, embed_passage, embed_query
from app.schemas.project import ProjectCandidate, RankedProject

# all-MiniLM-L6-v2 truncates silently at 256 tokens (~1000 chars). Put the
# header (name/description/topics) first within its own budget so a long
# README can't push it out of the window and leave us ranking on
# boilerplate alone.
HEADER_BUDGET_CHARS = 250
README_BODY_BUDGET_CHARS = 550
TECH_SECTION_BUDGET_CHARS = 200

_MD_IMAGE_LINK = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_MD_INLINE_CODE = re.compile(r"`([^`]*)`")
_MD_HEADER_MARKER = re.compile(r"^#{1,6}\s*", re.MULTILINE)
_MD_HR = re.compile(r"^-{3,}\s*$", re.MULTILINE)
_MD_BLOCKQUOTE = re.compile(r"^>\s?", re.MULTILINE)
_MD_BOLD_ITALIC = re.compile(r"[*_]{1,3}")
_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+", flags=re.UNICODE
)

_HEADER_LINE = re.compile(r"^(#{1,6})\s*(.+?)\s*$", re.MULTILINE)
_TECH_SECTION_KEYWORDS = re.compile(r"tech\s*stack|built\s*with|technologies used|^stack$", re.IGNORECASE)


def _clean_markdown(text: str) -> str:
    text = _MD_IMAGE_LINK.sub("", text)
    text = _MD_CODE_FENCE.sub(" ", text)
    text = _MD_LINK.sub(r"\1", text)
    text = _MD_INLINE_CODE.sub(r"\1", text)
    text = _MD_HEADER_MARKER.sub("", text)
    text = _MD_HR.sub("", text)
    text = _MD_BLOCKQUOTE.sub("", text)
    text = _MD_BOLD_ITALIC.sub("", text)
    text = _EMOJI.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _extract_tech_section(readme: str) -> str:
    """Pull out a "Tech Stack"/"Built With" section by name, since it's the
    single most JD-relevant part of a README and a blind character cap can
    sever it before we ever reach it."""
    headers = list(_HEADER_LINE.finditer(readme))
    for i, match in enumerate(headers):
        if _TECH_SECTION_KEYWORDS.search(match.group(2)):
            start = match.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(readme)
            return readme[start:end].strip()
    return ""


def _project_text(candidate: ProjectCandidate) -> str:
    parts = [candidate.repo_name]
    if candidate.description:
        parts.append(candidate.description)
    if candidate.topics:
        parts.append("Topics: " + ", ".join(candidate.topics))
    header = ". ".join(parts)[:HEADER_BUDGET_CHARS]

    body = _clean_markdown(candidate.readme_excerpt)[:README_BODY_BUDGET_CHARS]
    tech_section = _clean_markdown(_extract_tech_section(candidate.readme_excerpt))[:TECH_SECTION_BUDGET_CHARS]

    text = f"{header}. {body}"
    # Skip appending if the tech section is short enough that it's likely
    # already inside the body window — otherwise it gets double-counted,
    # over-weighting stack vocabulary for repos whose Stack header sits early.
    if tech_section and tech_section[:40] not in body:
        text += f" Built with: {tech_section}"
    return text


def rank_projects_for_jd(
    jd_text: str, candidates: list[ProjectCandidate], top_n: int = 3
) -> list[RankedProject]:
    jd_embedding = embed_query(jd_text)
    ranked = [
        RankedProject(project=candidate, similarity=cosine_similarity(jd_embedding, embed_passage(_project_text(candidate))))
        for candidate in candidates
    ]
    ranked.sort(key=lambda rp: rp.similarity, reverse=True)
    return ranked[:top_n]
