from app.schemas.jd_summary import JDSummary


def test_defaults_are_safe_fallback_shape():
    summary = JDSummary()
    assert summary.stipend_amount is None
    assert summary.stipend_status == "unknown"
    assert summary.ppo_detected is False
    assert summary.role_similarity is None
    assert summary.responsibilities == []
    assert summary.requirements == []
    assert summary.duration is None
    assert summary.benefits == []


def test_round_trips_through_dict():
    summary = JDSummary(
        stipend_amount=15000,
        stipend_status="confirmed_ok",
        location="Bangalore",
        is_remote=False,
        ppo_detected=False,
        role_tier="backend",
        role_similarity=0.73,
        responsibilities=["Build REST APIs"],
        requirements=["Python", "FastAPI"],
        duration="3 months",
        benefits=["Certificate"],
    )
    assert JDSummary.model_validate(summary.model_dump()) == summary
