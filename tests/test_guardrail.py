from app.nodes.tailor.guardrail import flag_unsupported_terms


def test_no_flags_when_bullet_is_faithful_rewrite():
    source = "Built a FastAPI backend using Groq and LLaMA 3.3 70B for tool calling."
    generated = "Developed a FastAPI service integrating Groq's LLaMA 3.3 70B for autonomous tool calling."
    assert flag_unsupported_terms(generated, source, known_skills=[]) == []


def test_flags_invented_technology():
    source = "Built a FastAPI backend using Groq."
    generated = "Built a FastAPI backend using Groq and deployed it with Kubernetes on AWS."
    flagged = flag_unsupported_terms(generated, source, known_skills=[])
    assert "Kubernetes" in flagged
    assert "AWS" in flagged


def test_flags_invented_metric():
    source = "Built a classifier for churn prediction."
    generated = "Built a classifier achieving 99.8% accuracy for churn prediction."
    flagged = flag_unsupported_terms(generated, source, known_skills=[])
    assert any("99.8" in term for term in flagged)


def test_known_skill_list_prevents_false_flag():
    # A skill not mentioned in this specific source excerpt, but genuinely
    # on the candidate's skill list, should not be flagged as invented.
    source = "Built a backend service."
    generated = "Built a backend service using PostgreSQL."
    flagged = flag_unsupported_terms(generated, source, known_skills=["PostgreSQL"])
    assert "PostgreSQL" not in flagged


def test_plain_english_words_are_not_flagged():
    source = "Built a backend service."
    generated = "Designed and shipped a reliable backend service for production use."
    assert flag_unsupported_terms(generated, source, known_skills=[]) == []


def test_slash_compound_not_flagged_when_both_parts_known():
    source = "Backend supports SQLite or Postgres for local development."
    generated = "Built a backend with Postgres/SQLite support for flexible deployment."
    assert flag_unsupported_terms(generated, source, known_skills=[]) == []


def test_hyphen_compound_not_flagged_when_technical_part_known():
    source = "Taught backend development with FastAPI to students."
    generated = "Delivered FastAPI-based instruction to students."
    assert flag_unsupported_terms(generated, source, known_skills=[]) == []


def test_compound_still_flagged_when_a_technical_part_is_unknown():
    source = "Built a backend with Postgres support."
    generated = "Built a backend with Postgres/MongoDB support."
    flagged = flag_unsupported_terms(generated, source, known_skills=[])
    assert "Postgres/MongoDB" in flagged


def test_second_sentence_capital_not_flagged_as_new_claim():
    source = "Built a wellness planning backend. Helped organize hackathons."
    generated = "Built a wellness planning backend using FastAPI. These skills transfer directly."
    flagged = flag_unsupported_terms(generated, source, known_skills=[])
    assert "These" not in flagged
