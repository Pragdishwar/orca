"""Deterministic generation of the Muthalapozhi analysis record.

PROVENANCE: SYNTHETIC_STRUCTURED (SRS 4.4).

Every series here is generated from a fixed seed, not downloaded. The schema,
units and seasonal behaviour match the real products named in D-01/D-02/D-15
(Copernicus Marine wave hindcast, harmonic tide prediction, MOSDAC lightning),
so the ETL in SRS 9.1 can replace this module wholesale without any consumer
changing. Nothing that reads this data may present it without its badge.
"""
import math
import random
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict, List

SEED = 26176

# D-04 inlet geometry, measured from imagery.
INLET = {
    "inlet_id": "muthalapozhi",
    "name": "Muthalapozhi",
    "lat": 8.6360,
    "lon": 76.7860,
    # Channel axis, degrees true. The mouth opens to the west-south-west, so
    # swell arriving from ~250 deg runs straight up the channel.
    "channel_bearing_deg": 250.0,
    "mouth_width_m": 110.0,
}

RECORD_START = datetime(2022, 1, 1, tzinfo=timezone.utc)
RECORD_YEARS = 3


def _seasonal_hs(day_of_year: int) -> float:
    """Climatological mean significant wave height for the Kerala coast.

    Driven by the south-west monsoon: a broad maximum through Jun-Aug, a
    secondary bump in the post-monsoon, and a calm Dec-Feb.
    """
    phase = 2 * math.pi * (day_of_year - 172) / 365.0  # peak near 21 June
    monsoon = 0.95 * max(0.0, math.cos(phase))
    secondary = 0.20 * max(0.0, math.cos(2 * math.pi * (day_of_year - 290) / 365.0))
    return 0.75 + monsoon * 1.75 + secondary


def _tide_height(ts: datetime) -> float:
    """Two-constituent harmonic tide (M2 + S2), metres above datum."""
    hours = (ts - RECORD_START).total_seconds() / 3600.0
    m2 = 0.42 * math.sin(2 * math.pi * hours / 12.4206)
    s2 = 0.14 * math.sin(2 * math.pi * hours / 12.0)
    return 0.55 + m2 + s2


@lru_cache(maxsize=1)
def build_record() -> List[Dict[str, Any]]:
    """Hourly analysis frame: wave + wind + tide + hazard events, joined on ts.

    Returns one row per hour for RECORD_YEARS. Deterministic for a given SEED.
    """
    rng = random.Random(SEED)
    total_hours = RECORD_YEARS * 365 * 24
    rows: List[Dict[str, Any]] = []

    # Synoptic storm state: a slow random walk so rough spells last days, not
    # hours, the way real weather does.
    synoptic = 0.0
    # Latent "local chop" - short-period wind sea funnelled inside the channel.
    # It is NOT an input to the hazard index. It exists so the validation run
    # produces genuine misses instead of a perfect score.
    chop = 0.0
    cyclone_hours_left = 0

    for h in range(total_hours):
        ts = RECORD_START + timedelta(hours=h)
        doy = ts.timetuple().tm_yday

        synoptic = 0.985 * synoptic + rng.gauss(0, 0.18)
        chop = 0.92 * chop + rng.gauss(0, 0.30)

        base = _seasonal_hs(doy)
        hs = max(0.15, base + synoptic * 0.85 + rng.gauss(0, 0.10))

        # Peak period tracks wave height but saturates; monsoon swell is long.
        tp = 6.0 + 3.4 * math.sqrt(hs) + rng.gauss(0, 0.6)
        tp = min(max(tp, 3.5), 20.0)

        # Direction: tight around the monsoon WSW sector when energetic,
        # broader and more variable when calm.
        spread = 34.0 if hs < 1.2 else 13.0
        dir_deg = (250.0 + rng.gauss(0, spread)) % 360.0

        swell_fraction = 0.55 + 0.25 * min(1.0, hs / 3.0) + rng.gauss(0, 0.05)
        swell_fraction = min(max(swell_fraction, 0.25), 0.95)
        swell_hs = hs * swell_fraction
        windsea_hs = max(0.05, math.sqrt(max(hs**2 - swell_hs**2, 0.0025)))

        wind_ms = max(0.5, 3.0 + 4.2 * hs + rng.gauss(0, 1.4))
        wind_dir = (dir_deg + rng.gauss(0, 18)) % 360.0

        height = _tide_height(ts)
        rate = (_tide_height(ts + timedelta(minutes=30))
                - _tide_height(ts - timedelta(minutes=30)))
        if rate < -0.02:
            stage = "ebb"
        elif rate > 0.02:
            stage = "flood"
        else:
            stage = "slack"

        # Lightning: convective, concentrated in the pre- and post-monsoon
        # transition months and in the afternoon/evening.
        conv_season = 1.0 if ts.month in (4, 5, 10, 11) else 0.25
        diurnal = 1.0 if 13 <= ts.hour <= 21 else 0.2
        lightning_flag = int(rng.random() < 0.0075 * conv_season * diurnal)
        strike_density = round(rng.uniform(0.4, 8.0), 2) if lightning_flag else 0.0

        # Cyclone warnings: rare, and they persist for a couple of days.
        if cyclone_hours_left > 0:
            cyclone_hours_left -= 1
        elif ts.month in (5, 6, 10, 11, 12) and rng.random() < 0.0005:
            cyclone_hours_left = rng.randint(30, 70)
        cyclone_flag = int(cyclone_hours_left > 0)

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
            # Latent, not exposed to the index.
            "_chop": round(max(0.0, chop), 3),
        })

    return rows


def wave_data(row: Dict[str, Any]) -> Dict[str, float]:
    """Project an analysis row into the shape the hazard engine expects."""
    return {
        "hs": row["hs_m"],
        "tp": row["tp_s"],
        "dir": row["dir_deg"],
        "swell_hs": row["swell_hs_m"],
        "wind_ms": row["wind_ms"],
    }


def tide_data(row: Dict[str, Any]) -> Dict[str, Any]:
    return {"stage": row["tide_stage"], "rate": row["tide_rate_m_per_hr"]}


def row_at(ts: datetime) -> Dict[str, Any]:
    """Nearest hourly row to `ts`, clamped to the record."""
    record = build_record()
    idx = int((ts - RECORD_START).total_seconds() // 3600)
    return record[min(max(idx, 0), len(record) - 1)]


def window(start: datetime, end: datetime) -> List[Dict[str, Any]]:
    record = build_record()
    lo = max(0, int((start - RECORD_START).total_seconds() // 3600))
    hi = min(len(record), int((end - RECORD_START).total_seconds() // 3600) + 1)
    return record[lo:hi]
