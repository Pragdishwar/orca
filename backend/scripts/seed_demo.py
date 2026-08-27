import asyncio
import wave
import struct
import math
import os
import csv
import json
import logging
from sqlalchemy import select, text
from backend.app.db.session import async_session, engine
from backend.app.models.boat import Boat
from backend.app.models.hull_threshold import HullThreshold
from backend.app.models.source_registry import SourceRegistry
from backend.app.models.zone import Zone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_data():
    async with async_session() as session:
        # Seed Source Registry (D-14)
        sources = [
            SourceRegistry(provider="MOSDAC", spatial_coverage="Kerala", variables={"available": ["hs", "tp", "dir"]}, priority_tier=1, access_status="ONLINE"),
            SourceRegistry(provider="Bhuvan", spatial_coverage="Kerala", variables={"available": ["sst", "chl"]}, priority_tier=1, access_status="ONLINE"),
            SourceRegistry(provider="INCOIS", spatial_coverage="Kerala", variables={"available": ["advisory"]}, priority_tier=1, access_status="ONLINE"),
            SourceRegistry(provider="Copernicus", spatial_coverage="Kerala", variables={"available": ["hs", "tp", "dir"]}, priority_tier=2, access_status="ONLINE"),
            SourceRegistry(provider="NASA", spatial_coverage="Kerala", variables={"available": ["sst", "chl"]}, priority_tier=2, access_status="ONLINE"),
        ]
        session.add_all(sources)

        # Seed Hull Thresholds
        thresholds = [
            HullThreshold(hull_class="Small FRP", max_wave_height_m=1.8, max_current_kts=2.5, index_marginal=0.4, index_unsafe=0.7),
            HullThreshold(hull_class="Motorized Canoe", max_wave_height_m=1.2, max_current_kts=1.5, index_marginal=0.3, index_unsafe=0.6),
            HullThreshold(hull_class="Deep-Sea Trawler", max_wave_height_m=4.0, max_current_kts=5.0, index_marginal=0.6, index_unsafe=0.85),
        ]
        session.add_all(thresholds)

        # Seed Demo Boats
        boats = [
            Boat(boat_id="B-FRP-01", hull_class="Small FRP", length_m=8.5, engine_hp=9.9, home_harbour="Muthalapozhi", threshold_bucket="Small FRP"),
            Boat(boat_id="B-FRP-02", hull_class="Small FRP", length_m=9.0, engine_hp=15.0, home_harbour="Muthalapozhi", threshold_bucket="Small FRP"),
            Boat(boat_id="B-CAN-01", hull_class="Motorized Canoe", length_m=6.0, engine_hp=5.0, home_harbour="Muthalapozhi", threshold_bucket="Motorized Canoe"),
            Boat(boat_id="B-CAN-02", hull_class="Motorized Canoe", length_m=5.5, engine_hp=5.0, home_harbour="Muthalapozhi", threshold_bucket="Motorized Canoe"),
            Boat(boat_id="B-TRW-01", hull_class="Deep-Sea Trawler", length_m=20.0, engine_hp=120.0, home_harbour="Muthalapozhi", threshold_bucket="Deep-Sea Trawler"),
            Boat(boat_id="B-TRW-02", hull_class="Deep-Sea Trawler", length_m=24.0, engine_hp=200.0, home_harbour="Muthalapozhi", threshold_bucket="Deep-Sea Trawler"),
        ]
        session.add_all(boats)
        
        # In a real PostGIS environment, we would seed proper ST_GeomFromText polygons.
        # This script runs basic structural seeding for demo purposes.
        
        await session.commit()
        logger.info("Database entities seeded successfully.")

def generate_mock_audio():
    """Pre-generates mock audio .wav files in backend/static/audio/ for VHF phrases."""
    os.makedirs('backend/static/audio', exist_ok=True)
    sample_rate = 44100
    duration = 2.0 # seconds
    freq = 440.0 # Hz
    
    files = ["vhf_alert_en.wav", "vhf_alert_ml.wav", "vhf_alert_ta.wav"]
    for f in files:
        path = os.path.join('backend/static/audio', f)
        with wave.open(path, 'w') as wavef:
            wavef.setnchannels(1)
            wavef.setsampwidth(2)
            wavef.setframerate(sample_rate)
            
            for i in range(int(sample_rate * duration)):
                value = int(32767.0 * math.cos(2.0 * math.pi * freq * i / sample_rate))
                data = struct.pack('<h', value)
                wavef.writeframesraw(data)
        logger.info(f"Generated mock VHF audio: {path}")

def generate_mock_datasets():
    """Seeds dated incident CSV and Golden Test Cases JSON."""
    os.makedirs('backend/static/data', exist_ok=True)
    
    # 10-year wave/wind hourly hindcast + Harmonic Tide (Simulated via CSV)
    hindcast_path = 'backend/static/data/hindcast_D01.csv'
    with open(hindcast_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'hs', 'tp', 'dir', 'wind_spd', 'tide_stage'])
        writer.writerow(['2026-08-27T08:00:00Z', '1.5', '8.0', '210', '15', 'flood'])
        writer.writerow(['2026-08-27T09:00:00Z', '2.5', '10.0', '215', '20', 'ebb'])
    
    # Incident CSV (D-03)
    incident_path = 'backend/static/data/incidents_D03.csv'
    with open(incident_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'vessel_type', 'outcome', 'hs_at_time'])
        writer.writerow(['2023-07-10', 'FRP Skiff', 'Capsize', '3.8'])
        writer.writerow(['2022-09-15', 'Motorized Canoe', 'Engine Failure', '2.1'])
        
    # Golden Test Cases (M-02, M-03)
    golden_path = 'backend/static/data/golden_M02_M03.json'
    with open(golden_path, 'w') as f:
        json.dump({
            "M-02": [{"query": "Is it safe?", "expected": "SAFE"}],
            "M-03": [{"verdict_token": "SAFE", "computed": "DO_NOT_CROSS", "expected_guard": "FAIL"}]
        }, f)
    logger.info("Mock datasets D-01, D-02, D-03, M-02, M-03 created.")

async def main():
    logger.info("Starting Data Seeding Pipeline...")
    try:
        await seed_data()
    except Exception as e:
        logger.error(f"DB Seeding skipped or failed (PostGIS might not be up yet): {e}")
    generate_mock_audio()
    generate_mock_datasets()
    logger.info("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(main())
