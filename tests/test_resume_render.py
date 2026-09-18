from app.nodes.tailor.resume_render import render_resume_html, render_resume_pdf
from app.schemas.tailored_resume import TailoredBullet, TailoredResume


def _resume() -> TailoredResume:
    return TailoredResume(
        name="Test User",
        email="test@example.com",
        phone="+91-0000000000",
        location="Bengaluru, India",
        links={"linkedin": "https://linkedin.com/in/test", "github": "", "leetcode": "", "portfolio": ""},
        education_summary=["B.E. in Testing, Test College (2024-2028), CGPA 9.0"],
        highlighted_skills={"Languages": ["Python"], "Frameworks": ["FastAPI"]},
        bullets=[
            TailoredBullet(
                text="Built a <script>alert('x')</script> resume renderer.",
                source_type="project",
                source_ref="stipendscout",
                source_excerpt="...",
            ),
            TailoredBullet(
                text="Taught backend development.",
                source_type="experience",
                source_ref="Instructor at Test Org",
                source_excerpt="...",
            ),
            TailoredBullet(
                text="Built a production‑ready API—end‐to‐end.",
                source_type="hackathon",
                source_ref="Test Hackathon",
                source_excerpt="...",
            ),
        ],
    )


def test_render_html_escapes_bullet_content():
    html = render_resume_html(_resume())
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_html_includes_sections_in_order():
    html = render_resume_html(_resume())
    assert html.index("PROJECTS") < html.index("EXPERIENCE")
    assert "stipendscout" in html
    assert "Instructor at Test Org" in html


def test_render_html_normalizes_unicode_punctuation():
    # xhtml2pdf's base font can't render these — caught by reading a real
    # rendered PDF back and seeing missing-glyph boxes, not by a unit test.
    html = render_resume_html(_resume())
    assert "production‑ready" not in html
    assert "—" not in html
    assert "‐" not in html
    assert "production-ready" in html
    assert "end-to-end" in html


def test_render_pdf_produces_valid_pdf_bytes():
    pdf_bytes = render_resume_pdf(_resume())
    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 500


def test_skills_render_grouped_by_category_one_line_each():
    html = render_resume_html(_resume())
    assert html.count('class="skill-line"') == 2  # one line per category, not one big blob
    assert "<b>Languages:</b> Python" in html
    assert "<b>Frameworks:</b> FastAPI" in html


def test_legacy_flat_skill_list_still_parses():
    # Every application tailored before skills were categorized has
    # highlighted_skills persisted as a flat list (TailoredResume.model_dump_json()
    # from that era) — that JSON is permanent and must stay parseable, since
    # a code change can't retroactively rewrite already-generated resumes.
    legacy_json = _resume().model_dump_json()
    import json

    data = json.loads(legacy_json)
    data["highlighted_skills"] = ["Python", "FastAPI"]  # the old flat shape
    resume = TailoredResume.model_validate(data)
    assert resume.highlighted_skills == {"Skills": ["Python", "FastAPI"]}
    pdf_bytes = render_resume_pdf(resume)
    assert pdf_bytes[:4] == b"%PDF"


def test_legacy_empty_flat_skill_list_becomes_empty_dict():
    resume = TailoredResume.model_validate({**_resume().model_dump(), "highlighted_skills": []})
    assert resume.highlighted_skills == {}
