import re

# Resume bullets are terse and verb-first ("Built...", "Developed..."), so
# outside the first word, a capitalized token is almost always a proper
# noun or technology name in this domain — a much stronger signal here
# than in general prose. Combined with acronyms/internal-caps/digits and
# bare numeric claims (percentages, metrics), this reliably catches the
# case that matters most: a generated bullet naming a tool, tech, or
# number the source excerpt never mentioned. It won't catch a false claim
# phrased entirely in lowercase words, or a short acronym that happens to
# collide with a common substring elsewhere in the source text (this uses
# plain substring matching, not word-boundary matching) — over-flagging
# is the intended safe failure mode here, not silent trust.
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9+.#/-]*")
_NUMERIC_CLAIM = re.compile(r"\b\d+(?:\.\d+)?%?\b")
_SENTENCE_END = re.compile(r"[.!?][\"')]*$")

# Formal-letter/generic words that get capitalized by sentence position or
# convention, not because they're a claim — flagging these is pure noise
# that trains a reviewer to stop reading the flags at all.
_STOPWORDS = {
    "dear", "sincerely", "regards", "hiring", "team", "manager",
    "additionally", "beyond", "hello", "intern", "internship", "role",
}


def _extract_candidate_terms(text: str) -> list[str]:
    terms = []
    at_sentence_start = True
    for raw_word in text.split():
        match = _WORD.match(raw_word)
        is_sentence_start = at_sentence_start
        at_sentence_start = bool(_SENTENCE_END.search(raw_word))

        if not match:
            continue
        token = match.group(0).rstrip(".,;:!?")
        if len(token) < 2:
            continue
        if token.lower() in _STOPWORDS:
            continue

        has_internal_upper = any(c.isupper() for c in token[1:])
        is_all_caps = token.isupper()
        has_digit = any(c.isdigit() for c in token)
        is_capitalized_new_sentence = token[0].isupper() and not is_sentence_start
        if has_internal_upper or is_all_caps or has_digit or is_capitalized_new_sentence:
            terms.append(token)
    terms.extend(match.group(0) for match in _NUMERIC_CLAIM.finditer(text))
    return terms


def _is_technical_part(part: str) -> bool:
    # A plain all-lowercase word ("based", "driven", "compatible") is a
    # grammatical modifier, not a claim, and doesn't need to be traceable
    # to the source on its own.
    return not part.islower()


def _is_supported(term: str, haystack: str) -> bool:
    if term.lower() in haystack:
        return True
    # A slash- or hyphen-joined compound built entirely from already-known
    # parts isn't a new claim — e.g. "Postgres/SQLite" from a source that
    # says "SQLite or Postgres", or "FastAPI-based" from "FastAPI". Only
    # the technical-looking parts need independent verification; a plain
    # lowercase suffix like "-based"/"-driven" doesn't.
    parts = [p for p in re.split(r"[/-]", term) if len(p) >= 2]
    if len(parts) <= 1:
        return False
    technical_parts = [p for p in parts if _is_technical_part(p)]
    if not technical_parts:
        return False
    return all(p.lower() in haystack for p in technical_parts)


def flag_unsupported_terms(generated_text: str, source_excerpt: str, known_skills: list[str]) -> list[str]:
    """Terms in generated_text that appear in neither the source excerpt
    it was supposedly derived from, nor the candidate's known skill list.
    Returned for human review — never used to silently reject or edit."""
    haystack = f"{source_excerpt} {' '.join(known_skills)}".lower()
    return [term for term in _extract_candidate_terms(generated_text) if not _is_supported(term, haystack)]
