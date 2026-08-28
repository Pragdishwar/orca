"""Create the schema and seed the read-only tables on startup.

The prototype has to come up on a clean machine with one command, so this runs
automatically rather than relying on a separate migration step being
remembered. It is idempotent: seeding is skipped when the tables already hold
rows, so restarting never duplicates or clobbers registered boats.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select

from backend.app.core import config_store
from backend.app.core.seed_data import BOATS, NAMED_GROUNDS, ZONES
from backend.app.db.session import Base, async_session, engine
from backend.app.models import (  # noqa: F401 - imported so metadata is populated
    Advisory, Alert, Boat, Ground, HullThreshold, Incident, OfficialAdvisory,
    Query, Session, SourceRegistry, Trace, Zone,
)

logger = logging.getLogger(__name__)


async def create_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Schema ready.")


async def _count(session, model) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def seed() -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with async_session() as session:
        if await _count(session, SourceRegistry) == 0:
            for row in config_store.registry_seed():
                session.add(SourceRegistry(
                    source_id=row["source_id"],
                    provider=row["provider"],
                    country=row["country"],
                    variables=row["variables"],
                    spatial_coverage=row["spatial_coverage"],
                    resolution_km=row["resolution_km"],
                    access_method=row["access_method"],
                    access_status=row["access_status"],
                    priority_tier=row["priority_tier"],
                    provenance=row.get("provenance", "SYNTHETIC"),
                    # Only a source that actually connected has a pull time.
                    last_pull_ts=now if row["access_status"] == "CONNECTED" else None,
                ))
            logger.info("Seeded source registry (D-14).")

        if await _count(session, HullThreshold) == 0:
            for row in config_store.hull_thresholds():
                session.add(HullThreshold(
                    hull_class=row["hull_class"],
                    hs_marginal=row["hs_marginal_m"],
                    hs_unsafe=row["hs_unsafe_m"],
                    index_marginal=row["index_marginal"],
                    index_unsafe=row["index_unsafe"],
                    source=row["source"],
                ))
            logger.info("Seeded hull thresholds (D-10).")

        if await _count(session, Boat) == 0:
            for row in BOATS:
                session.add(Boat(**row))
            logger.info("Seeded demo boats (D-09).")

        if await _count(session, Ground) == 0:
            for row in NAMED_GROUNDS:
                session.add(Ground(**row))
            logger.info("Seeded named grounds (D-07).")

        if await _count(session, Zone) == 0:
            for row in ZONES:
                session.add(Zone(**row))
            logger.info("Seeded geofence zones (D-05).")

        await session.commit()


async def bootstrap() -> None:
    await create_schema()
    await seed()
