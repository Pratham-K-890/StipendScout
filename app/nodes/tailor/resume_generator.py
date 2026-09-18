from app.nodes.tailor.guardrail import flag_unsupported_terms
from app.nodes.tailor.llm_client import generate_json
from app.nodes.tailor.source_pool import build_source_pool
from app.schemas.profile import BaseProfile
from app.schemas.project import ProjectCandidate
from app.schemas.tailored_resume import CoverLetter, SourceItem, TailoredBullet, TailoredResume

MAX_BULLETS = 8


def _format_education(profile: BaseProfile) -> list[str]:
    lines = []
    for e in profile.education:
        span = f"{e.start_year}-{e.end_year}" if e.start_year else ""
        cgpa = f", CGPA {e.cgpa}" if e.cgpa else ""
        branch = f" in {e.branch}" if e.branch else ""
        lines.append(f"{e.degree}{branch}, {e.institution} ({span}){cgpa}".strip())
    return lines


MAX_SKILLS = 20


def _flatten_skills(skills: dict[str, list[str]]) -> list[str]:
    return [s for category_skills in skills.values() for s in category_skills]


def _bullets_prompt(jd_text: str, source_items: list[SourceItem], skills: dict[str, list[str]]) -> str:
    sources_block = "\n".join(
        f"[{i}] ({item.source_type} - {item.source_ref}): {item.excerpt}" for i, item in enumerate(source_items)
    )
    skills_block = "\n".join(
        f"{category}: " + ", ".join(category_skills) for category, category_skills in skills.items()
    )
    return f"""You are tailoring a resume for a specific internship posting. You are
given a job description, a numbered list of SOURCE FACTS about the
candidate, and the candidate's full skill list (grouped into categories —
the categories are fixed, you are only picking which individual skills to
keep, not inventing or renaming categories).

Do two things:
1. Select the {MAX_BULLETS} source facts most relevant to this JD and
   rewrite each as one punchy resume bullet emphasizing that relevance.
2. Select up to {MAX_SKILLS} skills total (across all categories combined)
   from the candidate's skill list that are most relevant to this JD —
   dumping the entire skill list on every resume is not useful to the
   candidate; pick fewer if the role is narrow.

STRICT RULES:
- Do NOT invent any tool, technology, outcome, or fact not present in the
  source fact you are rewriting.
- You may reorder, rephrase, and emphasize wording — never add new claims.
- Each output bullet must cite the source index it was derived from.
- Every skill you return must be copied EXACTLY (same spelling/casing) from
  the candidate's skill list below — do not invent or reword skills.

Job Description:
{jd_text}

Source Facts:
{sources_block}

Candidate's Skill List:
{skills_block}

Return ONLY valid JSON, no markdown fences, in this exact shape:
{{"bullets": [{{"source_index": 0, "text": "..."}}], "relevant_skills": ["..."]}}"""


def _cover_letter_prompt(profile: BaseProfile, jd_text: str, company: str, bullets: list[TailoredBullet]) -> str:
    bullets_block = "\n".join(f"- {b.text}" for b in bullets)
    return f"""Write a concise, specific cover letter (150-220 words) for {profile.name}
applying to an internship at {company}. Use ONLY the achievements listed
below as factual material — do not invent new facts, tools, or experience
beyond what is listed. No generic filler about "passion" or "hard worker."

Job Description:
{jd_text}

Achievements to draw from:
{bullets_block}

Return ONLY valid JSON, no markdown fences, in this exact shape:
{{"body": "..."}}"""


def _select_relevant_skills(
    profile_skills: dict[str, list[str]], llm_selection: list[str]
) -> dict[str, list[str]]:
    # LLM selects from the real list — never trust its spelling/casing, only
    # use it to pick which of the candidate's actual skills to keep. Anything
    # not an exact match is dropped rather than kept, since a near-match
    # could be a subtly invented skill. Categories themselves are never
    # LLM-controlled — only which skills within them survive.
    valid = {s.lower(): (category, s) for category, skills in profile_skills.items() for s in skills}
    selected = [valid[s.lower()] for s in llm_selection if s.lower() in valid]
    # dedupe while preserving first-seen order
    seen: set[str] = set()
    deduped = [pair for pair in selected if not (pair[1] in seen or seen.add(pair[1]))]

    if not deduped:
        # Selection failed/empty — fall back to a capped prefix (in profile
        # category order) rather than either an empty skills section or the
        # full (overkill) list.
        deduped = [(category, s) for category, skills in profile_skills.items() for s in skills][:MAX_SKILLS]
    else:
        deduped = deduped[:MAX_SKILLS]

    regrouped: dict[str, list[str]] = {}
    kept = {s for _, s in deduped}
    for category, skills in profile_skills.items():
        category_kept = [s for s in skills if s in kept]
        if category_kept:
            regrouped[category] = category_kept
    return regrouped


def generate_tailored_resume(
    profile: BaseProfile, jd_text: str, selected_projects: list[ProjectCandidate]
) -> TailoredResume:
    source_items = build_source_pool(profile, selected_projects)
    result = generate_json(_bullets_prompt(jd_text, source_items, profile.skills))
    relevant_skills = _select_relevant_skills(profile.skills, result.get("relevant_skills", []))
    flat_skills = _flatten_skills(profile.skills)

    bullets: list[TailoredBullet] = []
    for entry in result.get("bullets", []):
        source = source_items[entry["source_index"]]
        text = entry["text"]
        # source_ref (e.g. a club/company/repo name) is legitimate context,
        # not something the bullet must independently "prove" — only the
        # excerpt is the actual factual claim being rewritten.
        known_context = f"{source.excerpt} {source.source_ref}"
        bullets.append(
            TailoredBullet(
                text=text,
                source_type=source.source_type,
                source_ref=source.source_ref,
                source_excerpt=source.excerpt,
                flagged_terms=flag_unsupported_terms(text, known_context, flat_skills),
            )
        )

    return TailoredResume(
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        location=profile.location,
        links=profile.links.model_dump(),
        education_summary=_format_education(profile),
        highlighted_skills=relevant_skills,
        bullets=bullets,
    )


def generate_cover_letter(
    profile: BaseProfile, jd_text: str, company: str, bullets: list[TailoredBullet]
) -> CoverLetter:
    result = generate_json(_cover_letter_prompt(profile, jd_text, company, bullets))
    body = result["body"]
    # A cover letter legitimately references the JD, the company, and the
    # candidate's own name — none of that is a fabrication risk, only new
    # *skill/experience* claims beyond the sourced bullets are.
    known_context = " ".join(f"{b.source_excerpt} {b.source_ref}" for b in bullets)
    known_context += f" {jd_text} {company} {profile.name}"
    return CoverLetter(body=body, flagged_terms=flag_unsupported_terms(body, known_context, _flatten_skills(profile.skills)))
