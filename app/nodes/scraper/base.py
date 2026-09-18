from typing import Protocol

from app.exceptions import NotConfiguredError
from app.schemas.listing import NormalizedListing

__all__ = ["NotConfiguredError", "JobSource"]


class JobSource(Protocol):
    name: str

    def is_configured(self) -> bool:
        """Whether this source has what it needs (API keys, etc.) to run."""
        ...

    def fetch(self) -> list[NormalizedListing]:
        """Fetch and normalize listings. Raises NotConfiguredError if unconfigured."""
        ...
