import re

MIN_MONTHLY_STIPEND_INR = 10000

# Requires a currency marker AND an explicit month unit nearby, so we don't
# misread an annual salary figure as a monthly stipend. Low recall by
# design: Adzuna's free tier truncates JDs to 500 chars, so most listings
# simply won't have this text available at all — silence means "unknown",
# not "no stipend."
_STIPEND_PATTERN = re.compile(
    r"(?:₹|rs\.?|inr)\s?([\d][\d,]{2,6})"
    r"(?:\s*-\s*(?:₹|rs\.?|inr)?\s?[\d][\d,]{2,6})?"
    r"\s*(?:/|per\s+)?\s*(?:month|mo\b|pm\b)",
    re.IGNORECASE,
)

_PPO_PATTERN = re.compile(r"\bppo\b|pre[- ]?placement\s+offer", re.IGNORECASE)
# A short backward window catching "No PPO", "without a PPO", "does not
# offer a PPO" etc. — companies commonly state this explicitly as a
# reassurance to students, and a bare substring match on "PPO" would
# flag exactly the listings this filter exists to let through.
_PPO_NEGATION = re.compile(r"\b(no|not|without|non-?|zero|isn't|is not|doesn't|does not)\b\s*(?:\w+\s+){0,3}$", re.IGNORECASE)


def location_passes(is_remote: bool, location: str | None) -> bool:
    if is_remote:
        return True
    loc = (location or "").lower()
    return "bangalore" in loc or "bengaluru" in loc


def extract_stipend(text: str) -> tuple[int | None, str]:
    """Returns (amount, status) where status is one of:
    "confirmed_ok", "confirmed_below_minimum", "unknown".
    """
    match = _STIPEND_PATTERN.search(text)
    if not match:
        return None, "unknown"
    amount = int(match.group(1).replace(",", ""))
    status = "confirmed_ok" if amount >= MIN_MONTHLY_STIPEND_INR else "confirmed_below_minimum"
    return amount, status


def detect_ppo(text: str) -> bool:
    for match in _PPO_PATTERN.finditer(text):
        preceding = text[max(0, match.start() - 40) : match.start()]
        if _PPO_NEGATION.search(preceding):
            continue  # negated mention, e.g. "No PPO offered"
        return True
    return False
