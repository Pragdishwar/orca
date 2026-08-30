import math
import random
import urllib.request
import asyncio
import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict, List

SEED = 26176

INLET = {
    "inlet_id": "muthalapozhi",
    "name": "Muthalapozhi",
    "lat": 8.6360,
    "lon": 76.7860,
    "channel_bearing_deg": 250.0,
    "mouth_width_m": 110.0,
}

RECORD_START = datetime(2022, 1, 1, tzinfo=timezone.utc)
RECORD_YEARS = 3



async def build_record(lat: float = None, lon: float = None) -> List[Dict[str, Any]]:
    import httpx
    if lat is None or lon is None:
        lat, lon = INLET["lat"], INLET["lon"]

    now = datetime.now(timezone.utc)
    yesterday_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    start_date = "2022-01-01"

    m_url = f'https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&hourly=wave_height,wave_period,wave_direction,wind_wave_height,swell_wave_height,sea_level_height_msl'
    w_url_archive = f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={yesterday_date}&hourly=wind_speed_10m,wind_direction_10m'
    w_url_forecast = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&past_days=1&forecast_days=7&hourly=wind_speed_10m,wind_direction_10m'

    try:
        async with httpx.AsyncClient() as client:
            m_res, wa_res, wf_res = await asyncio.gather(
                client.get(m_url, headers={'User-Agent': 'Mozilla/5.0'}),
                client.get(w_url_archive, headers={'User-Agent': 'Mozilla/5.0'}),
                client.get(w_url_forecast, headers={'User-Agent': 'Mozilla/5.0'}),
            )
            m_data = m_res.json()
            w_archive = wa_res.json()
            w_forecast = wf_res.json()
    except Exception as e:
        print(f"Error fetching from Open-Meteo: {e}")
        return []

    m_hourly = m_data.get("hourly", {})
    
    w_times = w_archive.get("hourly", {}).get("time", []) + w_forecast.get("hourly", {}).get("time", [])
    w_speeds = w_archive.get("hourly", {}).get("wind_speed_10m", []) + w_forecast.get("hourly", {}).get("wind_speed_10m", [])
    w_dirs = w_archive.get("hourly", {}).get("wind_direction_10m", []) + w_forecast.get("hourly", {}).get("wind_direction_10m", [])
    
    wind_dict = {}
    for i, t in enumerate(w_times):
        wind_dict[t] = (w_speeds[i], w_dirs[i])

    times = m_hourly.get("time", [])
    if not times:
        return []

    rows = []
    
    # Live arrays fed directly into agents; remove synthetic generators like chop or hardcoded lightning logic if possible.
    # We will compute basic flags to prevent agent breakage, but using real values where possible.
    for i in range(len(times)):
        ts_str = times[i]
        ts = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
        
        hs = m_hourly.get("wave_height", [])[i]
        tp = m_hourly.get("wave_period", [])[i]
        dir_deg = m_hourly.get("wave_direction", [])[i]
        windsea_hs = m_hourly.get("wind_wave_height", [])[i]
        swell_hs = m_hourly.get("swell_wave_height", [])[i]
        sea_level = m_hourly.get("sea_level_height_msl", [])[i]
        
        wind_tuple = wind_dict.get(ts_str)
        wind_ms, wind_dir = wind_tuple if wind_tuple else (0.0, 0.0)

        # NaNs gracefully handled
        hs = hs if hs is not None else 0.5
        tp = tp if tp is not None else 5.0
        dir_deg = dir_deg if dir_deg is not None else 250.0
        windsea_hs = windsea_hs if windsea_hs is not None else 0.0
        swell_hs = swell_hs if swell_hs is not None else hs
        wind_ms = (wind_ms * 1000 / 3600) if wind_ms is not None else 0.0 
        wind_dir = wind_dir if wind_dir is not None else 0.0
        sea_level = sea_level if sea_level is not None else 0.0
        height = sea_level + 0.55
        
        if i > 0 and i < len(times) - 1:
            prev_level = m_hourly.get("sea_level_height_msl", [])[i-1] or 0.0
            next_level = m_hourly.get("sea_level_height_msl", [])[i+1] or 0.0
            rate = next_level - prev_level
        else:
            rate = 0.0
            
        if rate < -0.02: stage = "ebb"
        elif rate > 0.02: stage = "flood"
        else: stage = "slack"

        # Keep basic logic for flags so frontend icons work, but derived strictly from real seasons
        conv_season = 1.0 if ts.month in (4, 5, 10, 11) else 0.25
        diurnal = 1.0 if 13 <= ts.hour <= 21 else 0.2
        # Real-world proxy for cyclone: wind_ms > 17 (34 knots)
        cyclone_flag = 1 if wind_ms > 17 else 0
        # Lightning proxy: high winds + convergence season
        lightning_flag = 1 if (wind_ms > 10 and conv_season == 1.0 and diurnal == 1.0) else 0
        strike_density = 2.0 if lightning_flag else 0.0

        rows.append({
            "ts": ts,
            "hs_m": round(hs, 3),
            "tp_s": round(tp, 2),
            "dir_deg": round(dir_deg, 1),
            "wind_ms": round(wind_ms, 2),
            "wind_dir_deg": round(wind_dir, 1),
            "swell_hs_m": round(swell_hs, 3),
            "windsea_hs_m": round(windsea_hs, 3),
            "tide_height_m": round(height, 3),
            "tide_stage": stage,
            "tide_rate_m_per_hr": round(rate, 4),
            "lightning_flag": lightning_flag,
            "strike_density": strike_density,
            "cyclone_flag": cyclone_flag,
        })

    return rows

def wave_data(row: Dict[str, Any]) -> Dict[str, float]:
    return {
        "hs": row["hs_m"],
        "tp": row["tp_s"],
        "dir": row["dir_deg"],
        "swell_hs": row["swell_hs_m"],
        "wind_ms": row["wind_ms"],
    }

def tide_data(row: Dict[str, Any]) -> Dict[str, Any]:
    return {"stage": row["tide_stage"], "rate": row["tide_rate_m_per_hr"]}

async def get_historical_waves(
    hours: int = 12, lat: float = None, lon: float = None
) -> List[Dict[str, Any]]:
    record = await build_record(lat, lon)
    now = datetime.now(timezone.utc)
    return [r for r in record if now - timedelta(hours=hours) <= r["ts"] <= now]

async def get_forecast_waves(
    hours: int = 48, lat: float = None, lon: float = None
) -> List[Dict[str, Any]]:
    record = await build_record(lat, lon)
    now = datetime.now(timezone.utc)
    return [r for r in record if now <= r["ts"] <= now + timedelta(hours=hours)]

async def row_at(ts: datetime, lat: float = INLET["lat"], lon: float = INLET["lon"]) -> Dict[str, Any]:
    record = await build_record(lat, lon)
    if not record: return {}
    idx = int((ts - RECORD_START).total_seconds() // 3600)
    return record[min(max(idx, 0), len(record) - 1)]

async def window(start: datetime, end: datetime, lat: float = INLET["lat"], lon: float = INLET["lon"]) -> List[Dict[str, Any]]:
    record = await build_record(lat, lon)
    if not record: return []
    lo = max(0, int((start - RECORD_START).total_seconds() // 3600))
    hi = min(len(record), int((end - RECORD_START).total_seconds() // 3600) + 1)
    return record[lo:hi]
