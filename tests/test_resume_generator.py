from app.nodes.tailor.resume_generator import MAX_SKILLS, _flatten_skills, _select_relevant_skills


def test_flatten_skills_preserves_category_order():
    skills = {"Languages": ["Python", "Java"], "Databases": ["PostgreSQL"]}
    assert _flatten_skills(skills) == ["Python", "Java", "PostgreSQL"]


def test_select_relevant_skills_keeps_only_real_matches_grouped_by_category():
    profile_skills = {"Languages": ["Python", "Java"], "Frameworks": ["FastAPI", "React"]}
    result = _select_relevant_skills(profile_skills, ["Python", "FastAPI"])
    assert result == {"Languages": ["Python"], "Frameworks": ["FastAPI"]}


def test_select_relevant_skills_is_case_insensitive_but_preserves_profile_casing():
    profile_skills = {"Frameworks": ["FastAPI", "PostgreSQL"]}
    result = _select_relevant_skills(profile_skills, ["fastapi", "POSTGRESQL"])
    assert result == {"Frameworks": ["FastAPI", "PostgreSQL"]}


def test_select_relevant_skills_drops_invented_skills():
    profile_skills = {"Languages": ["Python", "FastAPI"]}
    result = _select_relevant_skills(profile_skills, ["Python", "Rust", "Kubernetes"])
    assert result == {"Languages": ["Python"]}


def test_select_relevant_skills_omits_categories_with_no_selected_skills():
    profile_skills = {"Languages": ["Python"], "Databases": ["PostgreSQL"]}
    result = _select_relevant_skills(profile_skills, ["Python"])
    assert result == {"Languages": ["Python"]}
    assert "Databases" not in result


def test_select_relevant_skills_falls_back_to_capped_prefix_when_selection_empty():
    profile_skills = {"Cat": [f"skill-{i}" for i in range(30)]}
    result = _select_relevant_skills(profile_skills, [])
    assert result == {"Cat": [f"skill-{i}" for i in range(MAX_SKILLS)]}


def test_select_relevant_skills_falls_back_when_llm_only_invents_skills():
    profile_skills = {"Languages": ["Python", "FastAPI"]}
    result = _select_relevant_skills(profile_skills, ["Rust", "Kubernetes"])
    assert result == {"Languages": ["Python", "FastAPI"]}


def test_select_relevant_skills_caps_at_max_even_with_valid_selection():
    profile_skills = {"Cat": [f"skill-{i}" for i in range(30)]}
    all_skills = _flatten_skills(profile_skills)
    result = _select_relevant_skills(profile_skills, all_skills)
    assert sum(len(v) for v in result.values()) == MAX_SKILLS
