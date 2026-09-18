from app.nodes.scraper.adzuna import AdzunaSource
from app.nodes.scraper.base import JobSource, NotConfiguredError
from app.nodes.scraper.remoteok import RemoteOKSource

ALL_SOURCES: list[JobSource] = [RemoteOKSource(), AdzunaSource()]


def get_enabled_sources() -> list[JobSource]:
    return [source for source in ALL_SOURCES if source.is_configured()]


__all__ = ["JobSource", "NotConfiguredError", "RemoteOKSource", "AdzunaSource", "get_enabled_sources"]
