from app.nodes.tailor.project_matcher import rank_projects_for_jd
from app.schemas.project import ProjectCandidate

JD_TEXT = """Machine Learning Intern
Build predictive models using pandas and scikit-learn, analyze structured
datasets, and train classical ML models for churn prediction."""


def _candidate(name: str, description: str, topics: list[str], readme: str = "") -> ProjectCandidate:
    return ProjectCandidate(
        repo_name=name,
        description=description,
        readme_excerpt=readme,
        topics=topics,
        language="Python",
        url=f"https://github.com/user/{name}",
        is_private=False,
        is_fork=False,
        stars=0,
        updated_at="2026-01-01T00:00:00Z",
    )


def test_ranks_relevant_project_above_unrelated_one():
    ml_project = _candidate(
        "churn-predictor",
        "A scikit-learn pipeline that predicts customer churn from tabular data using pandas and classical ML models.",
        ["machine-learning", "pandas", "scikit-learn"],
    )
    unrelated_project = _candidate(
        "portfolio-website",
        "A personal portfolio site built with React and Tailwind CSS.",
        ["react", "frontend", "css"],
    )

    ranked = rank_projects_for_jd(JD_TEXT, [ml_project, unrelated_project], top_n=2)

    assert ranked[0].project.repo_name == "churn-predictor"
    assert ranked[0].similarity > ranked[1].similarity


def test_top_n_limits_results():
    candidates = [_candidate(f"repo-{i}", "Some project.", []) for i in range(5)]
    ranked = rank_projects_for_jd(JD_TEXT, candidates, top_n=2)
    assert len(ranked) == 2
