from app.nodes.matcher.role_classifier import RoleTier, classify_role

BACKEND_JD = """Backend Developer Intern
We're looking for an intern to help build REST APIs using FastAPI and
PostgreSQL. You'll work on our backend services, write database migrations,
and design server-side endpoints for our platform."""

ML_JD = """Data Science Intern
Join our analytics team to build predictive models using pandas and
scikit-learn. You'll clean datasets, run statistical analysis, and train
classical machine learning models for churn prediction."""

AI_AGENT_JD = """AI Agent Engineer Intern
Build LLM-powered agents using LangChain and LangGraph. You'll design
prompt templates, implement retrieval-augmented generation pipelines, and
orchestrate multi-step agent workflows on top of GPT and Claude models."""

FRONTEND_JD = """Frontend Developer Intern
Build beautiful, responsive UIs using React, Tailwind CSS, and Figma
designs. You'll focus entirely on component styling, animations, and
pixel-perfect layouts."""

# Real Adzuna listing text (CODEMONK) that scored 0.582 similarity to the
# BACKEND anchor and passed hard filters before the keyword veto was added
# — the anchor's "Not a frontend or UI-focused role" disclaimer didn't
# actually suppress similarity via pure cosine distance.
REAL_FRONTEND_JD = """Software Engineering Intern - Frontend (React.js)
We are seeking a motivated Frontend Development Intern with a solid
foundation in React.js to contribute to our engineering team's mission of
building scalable, user-centric web applications. You will work on UI
components, responsive design, CSS styling, and frontend architecture
using React, Redux, and modern JavaScript tooling."""

FULL_STACK_BACKEND_FOCUSED_JD = """Full Stack Developer Intern
Build backend REST APIs using FastAPI and PostgreSQL, designing database
schemas and server-side business logic. You'll occasionally coordinate
with the React frontend team on API contracts, but the role is primarily
backend-focused."""

SALES_JD = """Sales Intern
Generate leads, cold-call prospective customers, and support the sales
team with outbound calling and CRM data entry."""

HR_JD = """HR Coordinator Intern
Support the HR team with onboarding, payroll coordination, and employee
engagement activities."""


def test_classifies_backend_role():
    tier, score = classify_role(BACKEND_JD)
    assert tier == RoleTier.BACKEND
    assert score > 0.5


def test_classifies_ml_role():
    tier, score = classify_role(ML_JD)
    assert tier == RoleTier.ML_DATA_SCIENCE


def test_classifies_ai_agent_role():
    tier, score = classify_role(AI_AGENT_JD)
    assert tier == RoleTier.AI_AGENT_LLM


def test_frontend_role_is_unmatched():
    # Frontend work should not be classified as backend, even though it's
    # still "software" enough to score higher than non-tech roles.
    tier, _ = classify_role(FRONTEND_JD)
    assert tier is None


def test_real_frontend_listing_is_unmatched():
    tier, score = classify_role(REAL_FRONTEND_JD)
    assert score > 0.5  # confirms the embedding alone would have passed this
    assert tier is None  # the keyword veto must catch it


def test_full_stack_backend_focused_role_still_matches():
    # The veto must not punish a genuinely backend role that merely
    # mentions working alongside a frontend team.
    tier, _ = classify_role(FULL_STACK_BACKEND_FOCUSED_JD)
    assert tier == RoleTier.BACKEND


def test_sales_role_is_unmatched():
    tier, _ = classify_role(SALES_JD)
    assert tier is None


def test_hr_role_is_unmatched():
    tier, _ = classify_role(HR_JD)
    assert tier is None
