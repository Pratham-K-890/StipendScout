from pydantic import BaseModel


class NormalizedListing(BaseModel):
    """Common shape every scraper source normalizes its raw listings into."""

    source: str
    external_id: str
    title: str
    company: str
    location: str | None
    is_remote: bool
    url: str
    description: str

    # Only set when we can confidently express the pay as a monthly INR
    # figure. Left None rather than guessed when the source gives an
    # ambiguous currency/period (e.g. an annual USD salary range) —
    # downstream filtering (module 4) decides what to do with unknowns.
    stipend_amount: int | None = None
    stipend_currency: str = "INR"

    # Original, unconverted pay info from the source, kept for reference
    # and for a human reviewer to resolve ambiguous cases manually.
    raw_salary: dict | None = None
