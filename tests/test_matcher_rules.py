from app.nodes.matcher.rules import detect_ppo, extract_stipend, location_passes


def test_location_passes_for_remote():
    assert location_passes(is_remote=True, location="Worldwide") is True


def test_location_passes_for_bangalore_variants():
    assert location_passes(is_remote=False, location="Bangalore, Karnataka") is True
    assert location_passes(is_remote=False, location="Bengaluru, India") is True


def test_location_fails_for_other_city():
    assert location_passes(is_remote=False, location="Mumbai, Maharashtra") is False


def test_location_fails_when_unknown():
    assert location_passes(is_remote=False, location=None) is False


def test_extract_stipend_confirmed_ok():
    amount, status = extract_stipend("Stipend: ₹15,000 per month, work from office.")
    assert amount == 15000
    assert status == "confirmed_ok"


def test_extract_stipend_confirmed_below_minimum():
    amount, status = extract_stipend("You will receive Rs 5000/month as stipend.")
    assert amount == 5000
    assert status == "confirmed_below_minimum"


def test_extract_stipend_unknown_when_absent():
    amount, status = extract_stipend("Great learning opportunity, apply now.")
    assert amount is None
    assert status == "unknown"


def test_extract_stipend_ignores_annual_figures():
    # No month unit nearby -> must not be misread as a monthly stipend.
    amount, status = extract_stipend("Expected CTC: INR 400,000 per annum.")
    assert amount is None
    assert status == "unknown"


def test_detect_ppo_true():
    assert detect_ppo("This internship may lead to a PPO for top performers.") is True
    assert detect_ppo("Pre-placement offer available based on performance.") is True


def test_detect_ppo_false():
    assert detect_ppo("This is a fixed-duration paid internship.") is False


def test_detect_ppo_false_when_explicitly_negated():
    # A real bug found live: "No PPO offered" — a reassurance that should
    # let the listing pass — was matching the bare "PPO" substring.
    assert detect_ppo("This is a 6 month internship. No PPO offered.") is False
    assert detect_ppo("This internship does not offer a PPO.") is False
    assert detect_ppo("There is no pre-placement offer for this role.") is False


def test_detect_ppo_true_still_detected_alongside_negation_text():
    assert detect_ppo("Top performers may receive a PPO after the internship.") is True
