import html as html_lib
from collections import defaultdict
from io import BytesIO

from xhtml2pdf import pisa

from app.schemas.tailored_resume import TailoredResume

_SECTION_TITLES = {
    "project": "PROJECTS",
    "experience": "EXPERIENCE",
    "hackathon": "HACKATHONS",
    "responsibility": "RESPONSIBILITIES",
}
_SECTION_ORDER = ["project", "experience", "hackathon", "responsibility"]

_CSS = """
    @page { size: A4; margin: 1.25cm 1.5cm; }
    body { font-family: Helvetica, Arial, sans-serif; font-size: 9pt; line-height: 1.32; color: #111; }
    .name { text-align: center; font-size: 17pt; letter-spacing: 1.5px; margin-bottom: 2px; }
    .contact { text-align: center; font-size: 8.5pt; color: #333; margin-bottom: 4px; }
    .section-title { font-size: 9.5pt; font-weight: bold; border-bottom: 0.75pt solid #333;
                      margin-top: 8px; margin-bottom: 3px; letter-spacing: 0.5px; }
    .entry-heading { font-weight: bold; font-size: 9pt; margin-top: 4px; }
    ul { margin: 2px 0 4px 0; padding-left: 14px; }
    li { margin-bottom: 2px; }
    .education-line { margin: 0 0 3px 0; }
    .skill-line { margin: 0 0 1px 0; }
"""


# xhtml2pdf's base Helvetica font can't render several "smart"
# typographic characters LLMs commonly generate (non-breaking hyphen,
# em/en dash, curly quotes, ellipsis) — they come out as missing-glyph
# black boxes. Caught by actually reading a rendered PDF back, not by any
# unit test. Normalize to plain ASCII equivalents before rendering.
_UNICODE_TO_ASCII = {
    "—": " - ",  # em dash —
    "–": "-",  # en dash –
    "‐": "-",  # hyphen ‐ (U+2010)
    "‑": "-",  # non-breaking hyphen ‑ (U+2011)
    "‘": "'",  # left single quote '
    "’": "'",  # right single quote '
    "“": '"',  # left double quote "
    "”": '"',  # right double quote "
    "…": "...",  # ellipsis …
    " ": " ",  # non-breaking space
}


def _normalize(text: str) -> str:
    for unicode_char, ascii_equivalent in _UNICODE_TO_ASCII.items():
        text = text.replace(unicode_char, ascii_equivalent)
    return text


def _esc(text: str) -> str:
    return html_lib.escape(_normalize(text or ""))


def render_resume_html(resume: TailoredResume) -> str:
    contact_parts = [p for p in [resume.location, resume.email, resume.phone] if p]
    contact_line = " | ".join(_esc(p) for p in contact_parts)

    links = [v for v in [resume.links.get("linkedin"), resume.links.get("github"),
                          resume.links.get("leetcode"), resume.links.get("portfolio")] if v]
    links_line = " | ".join(_esc(link) for link in links)

    education_html = "".join(f'<p class="education-line">{_esc(line)}</p>' for line in resume.education_summary)
    skills_html = "".join(
        f'<p class="skill-line"><b>{_esc(category)}:</b> {_esc(", ".join(category_skills))}</p>'
        for category, category_skills in resume.highlighted_skills.items()
    )

    by_type: dict[str, list] = defaultdict(list)
    for bullet in resume.bullets:
        by_type[bullet.source_type].append(bullet)

    sections_html = ""
    for source_type in _SECTION_ORDER:
        bullets = by_type.get(source_type)
        if not bullets:
            continue
        sections_html += f'<div class="section-title">{_SECTION_TITLES[source_type]}</div>'
        by_ref: dict[str, list] = defaultdict(list)
        for bullet in bullets:
            by_ref[bullet.source_ref].append(bullet)
        for ref, ref_bullets in by_ref.items():
            sections_html += f'<div class="entry-heading">{_esc(ref)}</div>'
            sections_html += "<ul>" + "".join(f"<li>{_esc(b.text)}</li>" for b in ref_bullets) + "</ul>"

    return f"""<html><head><style>{_CSS}</style></head><body>
<div class="name">{_esc(resume.name)}</div>
<div class="contact">{contact_line}</div>
{f'<div class="contact">{links_line}</div>' if links_line else ""}
<div class="section-title">EDUCATION</div>
{education_html}
<div class="section-title">SKILLS</div>
{skills_html}
{sections_html}
</body></html>"""


def render_resume_pdf(resume: TailoredResume) -> bytes:
    buffer = BytesIO()
    result = pisa.CreatePDF(render_resume_html(resume), dest=buffer)
    if result.err:
        raise RuntimeError(f"PDF generation failed with {result.err} error(s)")
    return buffer.getvalue()
