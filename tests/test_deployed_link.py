from app.nodes.tailor.deployed_link import extract_deployed_url

# Real pattern seen in ai-api-assistant's README this session.
REAL_README_EXCERPT = """# AI Assistant API

A production-ready AI chat backend built with FastAPI and Groq.

**Live API:** `https://ai-api-assistant-production.up.railway.app`
**Docs:** `https://ai-api-assistant-production.up.railway.app/docs`
"""


def test_extracts_backtick_wrapped_live_url():
    assert extract_deployed_url(REAL_README_EXCERPT) == "https://ai-api-assistant-production.up.railway.app"


def test_extracts_markdown_link_demo_url():
    text = "Check out the **Live Demo**: [here](https://myproject.vercel.app)"
    assert extract_deployed_url(text) == "https://myproject.vercel.app"


def test_extracts_deployed_at_bare_url():
    text = "Deployed at https://myapp.onrender.com for testing."
    assert extract_deployed_url(text) == "https://myapp.onrender.com"


def test_returns_none_when_no_live_keyword():
    text = "See the [documentation](https://example.com/docs) for setup instructions."
    assert extract_deployed_url(text) is None


def test_returns_none_for_readme_with_no_urls():
    assert extract_deployed_url("Just a plain project description, no links here.") is None


def test_excludes_github_and_badge_urls_even_near_keyword():
    text = "This is live on GitHub: https://github.com/user/repo — see the badge below."
    assert extract_deployed_url(text) is None


def test_prefers_first_matching_live_url_over_later_docs_link():
    text = "**Live API:** `https://api.example.com`\n**Docs:** `https://api.example.com/docs`"
    assert extract_deployed_url(text) == "https://api.example.com"
