from app.nodes.matcher.role_classifier import classify_role
from app.nodes.matcher.rules import detect_ppo, extract_stipend, location_passes
from app.schemas.listing import NormalizedListing
from app.schemas.match import MatchResult


def evaluate_listing(listing: NormalizedListing) -> MatchResult:
    text = f"{listing.title}\n{listing.description}"
    reasons: list[str] = []

    if not location_passes(listing.is_remote, listing.location):
        reasons.append("location is not Bengaluru or remote")

    stipend_amount, stipend_status = extract_stipend(text)
    if stipend_status == "confirmed_below_minimum":
        reasons.append(f"stipend below ₹10,000/month (found ₹{stipend_amount})")

    ppo_detected = detect_ppo(text)
    if ppo_detected:
        reasons.append("PPO-linked internship")

    role_tier, similarity = classify_role(text)
    if role_tier is None:
        reasons.append("role doesn't match backend/ML-DS/AI-agent focus")

    return MatchResult(
        passes_hard_filters=len(reasons) == 0,
        exclusion_reasons=reasons,
        role_tier=role_tier,
        role_similarity=similarity,
        stipend_amount=stipend_amount,
        stipend_status=stipend_status,
        ppo_detected=ppo_detected,
    )
