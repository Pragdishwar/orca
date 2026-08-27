import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import async_session
from backend.app.models.boat import Boat
from backend.app.models.alert import Alert
from backend.app.core.discovery import DatasetDiscoveryAgent
from backend.app.core.hazard_engine import calculate_hazard_index, evaluate_verdict

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
last_run_time = None

class MockHullThreshold:
    """Mock threshold boundary config representing hull classes."""
    def __init__(self, bucket: str = "A"):
        # Assume static bounds for now
        self.index_marginal = 0.4
        self.index_unsafe = 0.7

def trigger_broadcast_renderer(alert_id: str):
    """
    Mock function to automatically invoke the Broadcast Renderer 
    to prepare SMS, VHF, Slip, and Board previews for this alert.
    """
    logger.info(f"Broadcast Renderer invoked for alert: {alert_id}")

async def sentinel_hazard_poll():
    """
    Core Sentinel task running on configurable intervals.
    Discovers data, calculates hazards, deduplicates, and fires automated alerts.
    """
    global last_run_time
    logger.info("Sentinel: Initiating hazard poll.")
    last_run_time = datetime.now(timezone.utc)
    
    async with async_session() as session:
        # 1. Iterate through all registered boats
        stmt = select(Boat)
        result = await session.execute(stmt)
        boats = result.scalars().all()
        
        discovery_agent = DatasetDiscoveryAgent(session=session)
        
        for boat in boats:
            # 2. Discover latest conditions for home_harbour
            # In actual implementation, we'd pull coordinates from Harbour registry based on boat.home_harbour
            discovery_res = await discovery_agent.discover_sources(["hs", "tp", "dir", "stage", "rate"], boat.home_harbour)
            
            # Simulate fetched payload from the Discovery Agent's top source
            mock_wave_data = {"hs": 4.5, "tp": 8.0, "dir": 90, "swell_hs": 1.0}
            mock_tide_data = {"stage": "ebb", "rate": 2.0}
            lightning_flag = 0
            cyclone_flag = 0
            
            # 3. Compute deterministic hazard_index
            index = calculate_hazard_index(
                wave_data=mock_wave_data,
                tide_data=mock_tide_data,
                inlet_geometry={"channel_bearing": 90},
                lightning_flag=lightning_flag,
                cyclone_flag=cyclone_flag
            )
            
            hull_threshold = MockHullThreshold(boat.threshold_bucket)
            verdict = evaluate_verdict(index, hull_threshold)
            
            # 4. Check if DO_NOT_CROSS, MARGINAL, or severe hazard threshold breached
            if verdict in ("DO_NOT_CROSS", "MARGINAL"):
                trigger_type = f"HAZARD_{verdict}"
                
                # Check deduplication: active alert exists for this boat/trigger?
                alert_stmt = select(Alert).where(
                    Alert.boat_id == boat.boat_id,
                    Alert.trigger_type == trigger_type,
                    Alert.state == "PENDING_RELEASE"
                )
                existing_res = await session.execute(alert_stmt)
                existing_alert = existing_res.scalars().first()
                
                if not existing_alert:
                    # 5. Create Alert entity
                    new_alert = Alert(
                        boat_id=boat.boat_id,
                        trigger_type=trigger_type,
                        severity="HIGH" if verdict == "DO_NOT_CROSS" else "MEDIUM",
                        source_id="SYS_SENTINEL",
                        state="PENDING_RELEASE"
                    )
                    session.add(new_alert)
                    await session.flush() # Secure an alert_id
                    
                    logger.warning(f"Sentinel: Alert {new_alert.alert_id} generated for Boat {boat.boat_id} (Verdict: {verdict})")
                    
                    # 6. Automate broadcast rendering
                    trigger_broadcast_renderer(str(new_alert.alert_id))
                    
        await session.commit()
    logger.info("Sentinel: Hazard poll complete.")

def start_sentinel(interval_minutes: int = 15):
    """Start the APScheduler for the Sentinel agent."""
    if not scheduler.running:
        scheduler.add_job(
            sentinel_hazard_poll, 
            'interval', 
            minutes=interval_minutes, 
            id="sentinel_poll_job", 
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Sentinel: Started background scheduler with {interval_minutes}m interval.")
