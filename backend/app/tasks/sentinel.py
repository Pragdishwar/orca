"""The Sentinel agent: scheduled hazard polling, independent of any query.

FR-29/FR-30. It shares the Discovery agent's registry and the Risk agent's
threshold logic, and writes into the same PENDING_RELEASE gate and the same
broadcast renderer a query-triggered advisory uses. There is no separate
alerting mechanism to keep in sync.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from backend.app.core import config_store
from backend.app.core.advisory_engine import build_advisory
from backend.app.core.discovery import DatasetDiscoveryAgent
from backend.app.db.session import async_session
from backend.app.models.alert import Alert
from backend.app.models.boat import Boat

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
last_run_time: Optional[datetime] = None
last_run_summary: Dict[str, Any] = {}

POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))

# How far ahead each cycle looks. A skipper needs tomorrow's warning tonight,
# while the boat is still ashore - an alert that only fires once conditions
# have already turned is worth little.
HORIZON_DAYS = int(os.getenv("SENTINEL_HORIZON_DAYS", "2"))

# F-13 triggers on any threshold crossing, not only the unsafe band: MARGINAL
# for a plywood canoe is a real warning even though SRS 5.4's pseudocode only
# names DO_NOT_CROSS. Severity distinguishes the two.
SEVERITY = {"DO_NOT_CROSS": "severe", "MARGINAL": "warning"}


async def sentinel_hazard_poll() -> Dict[str, Any]:
    """One poll cycle: every registered boat against its own hull threshold."""
    global last_run_time, last_run_summary
    started = datetime.now(timezone.utc)
    last_run_time = started
    created: List[str] = []
    checked = 0

    async with async_session() as session:
        boats = (await session.execute(select(Boat))).scalars().all()

        # Same registry the query path uses, so the alert can name its source.
        discovery = await DatasetDiscoveryAgent(session=session).discover_sources(
            ["hs", "tp", "dir", "swell_hs"], "kerala")
        source_id = (discovery.selected_sources[0].source_id
                     if discovery.selected_sources else None)

        for boat in boats:
            checked += 1
            hull = boat.threshold_bucket or boat.hull_class
            band = config_store.band_for(hull)

            for day_offset in range(HORIZON_DAYS):
                target = started + timedelta(days=day_offset)
                advisory = build_advisory(hull, target)
                verdict = advisory["verdict"]

                triggers = []
                if verdict in ("DO_NOT_CROSS", "MARGINAL"):
                    triggers.append("HAZARD_INDEX")
                if advisory["lightning_flag"]:
                    triggers.append("LIGHTNING")
                if advisory["cyclone_flag"]:
                    triggers.append("CYCLONE")
                if advisory["wind_ms"] >= 17.0:
                    triggers.append("WIND_SPEED")
                if not triggers:
                    continue

                trigger_type = "+".join(triggers)

                # Deduplicate: one open alert per boat, per trigger, per date.
                existing = (await session.execute(
                    select(Alert).where(
                        Alert.boat_id == boat.boat_id,
                        Alert.trigger_type == trigger_type,
                        Alert.state == "PENDING_RELEASE",
                    ))).scalars().all()
                if any((e.payload or {}).get("advisory", {}).get("date") == advisory["date"]
                       for e in existing):
                    continue

                alert = Alert(
                    boat_id=boat.boat_id,
                    trigger_type=trigger_type,
                    severity=SEVERITY.get(verdict, "advisory"),
                    source_id=source_id,
                    verdict=verdict,
                    index_value=advisory["index_value"],
                    hull_class=hull,
                    state="PENDING_RELEASE",
                    payload={
                        "advisory": {k: v for k, v in advisory.items()
                                     if k not in ("hourly", "_numerals")},
                        "trigger_detail": {
                            "triggers": triggers,
                            "for_date": advisory["date"],
                            "days_ahead": day_offset,
                            "index_value": advisory["index_value"],
                            "index_marginal": band.index_marginal,
                            "index_unsafe": band.index_unsafe,
                            "hs_m": advisory["hs_m"],
                            "wind_ms": advisory["wind_ms"],
                            "lightning_flag": advisory["lightning_flag"],
                            "cyclone_flag": advisory["cyclone_flag"],
                            "source_id": source_id,
                            "explanation": (
                                f"Index {advisory['index_value']} crossed the "
                                f"{band.label} {'unsafe' if verdict == 'DO_NOT_CROSS' else 'marginal'} "
                                f"threshold of "
                                f"{band.index_unsafe if verdict == 'DO_NOT_CROSS' else band.index_marginal}."),
                        },
                    },
                )
                session.add(alert)
                await session.flush()
                created.append(str(alert.alert_id))
                logger.warning("Sentinel: alert %s for boat %s (%s, %s, %s)",
                               alert.alert_id, boat.boat_id, verdict, trigger_type,
                               advisory["date"])

        await session.commit()

    last_run_summary = {
        "started": started.isoformat(),
        "boats_checked": checked,
        "alerts_created": len(created),
        "alert_ids": created,
        "duration_s": round((datetime.now(timezone.utc) - started).total_seconds(), 2),
    }
    logger.info("Sentinel: poll complete - %s boats, %s new alerts", checked, len(created))
    return last_run_summary


def start_sentinel(interval_minutes: int = POLL_INTERVAL_MINUTES) -> None:
    if scheduler.running:
        return
    scheduler.add_job(sentinel_hazard_poll, "interval", minutes=interval_minutes,
                      id="sentinel_poll_job", replace_existing=True,
                      next_run_time=datetime.now(timezone.utc))
    scheduler.start()
    logger.info("Sentinel: scheduler started on a %s minute interval.", interval_minutes)


def stop_sentinel() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
