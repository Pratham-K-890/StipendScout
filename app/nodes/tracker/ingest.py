from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Listing
from app.nodes.matcher.embeddings import embed_text
from app.schemas.listing import NormalizedListing
from app.schemas.tracker import IngestSummary


def ingest_listings(session: Session, source: str, listings: list[NormalizedListing]) -> IngestSummary:
    """Upsert one source's scrape results into `listings`, and mark rows
    from this source not seen in this run as disappeared.

    An empty `listings` list is deliberately NOT treated as "everything
    from this source disappeared" — that's almost always a transient
    scraper/API failure, not every posting vanishing at once. Skip the
    disappearance sweep entirely in that case.
    """
    if not listings:
        return IngestSummary(source=source, new=0, updated=0, disappeared=0, skipped_empty_run=True)

    now = datetime.now(timezone.utc)
    seen_external_ids = {listing.external_id for listing in listings}

    existing_rows = {
        row.external_id: row
        for row in session.execute(select(Listing).where(Listing.source == source)).scalars()
    }

    new_count = 0
    updated_count = 0
    for normalized in listings:
        embedding = embed_text(f"{normalized.title}\n{normalized.description}")
        existing = existing_rows.get(normalized.external_id)
        if existing:
            existing.title = normalized.title
            existing.company = normalized.company
            existing.location = normalized.location
            existing.is_remote = normalized.is_remote
            existing.stipend_amount = normalized.stipend_amount
            existing.stipend_currency = normalized.stipend_currency
            existing.url = normalized.url
            existing.description = normalized.description
            existing.description_embedding = embedding
            existing.last_seen_at = now
            existing.disappeared_at = None  # reappeared, if it had previously vanished
            updated_count += 1
        else:
            session.add(
                Listing(
                    source=source,
                    external_id=normalized.external_id,
                    title=normalized.title,
                    company=normalized.company,
                    location=normalized.location,
                    is_remote=normalized.is_remote,
                    stipend_amount=normalized.stipend_amount,
                    stipend_currency=normalized.stipend_currency,
                    url=normalized.url,
                    description=normalized.description,
                    description_embedding=embedding,
                    first_seen_at=now,
                    last_seen_at=now,
                )
            )
            new_count += 1

    disappeared_rows = [
        row
        for external_id, row in existing_rows.items()
        if external_id not in seen_external_ids and row.disappeared_at is None
    ]
    for row in disappeared_rows:
        row.disappeared_at = now

    session.commit()
    return IngestSummary(
        source=source, new=new_count, updated=updated_count, disappeared=len(disappeared_rows)
    )
