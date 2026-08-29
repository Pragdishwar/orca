"""Seed content for the read-only tables (D-05, D-06, D-07, D-09, D-11).

PROVENANCE: SYNTHETIC. Ground names, zone polygons and PFZ points are
plausible for this stretch of the Kerala coast but are not surveyed data.
They are shaped to match the published formats so the ETL in SRS 9.1 can swap
in the real layers without changing any consumer. Nothing here may be
displayed without its provenance badge (SRS 4.4).
"""
from typing import Any, Dict, List

from backend.app.core.dataset import INLET
from backend.app.core.geo import circle_ring

# D-07: named grounds. R-6 - a boat is linked to one of these by name only;
# the coordinates live here, never against the boat.
NAMED_GROUNDS: List[Dict[str, Any]] = [
    {"ground_id": "G-MUTH-NEAR", "local_name": "Muthalapozhi Nearshore",
     "centroid_lat": 8.6480, "centroid_lon": 76.7350, "radius_km": 4.0},
    {"ground_id": "G-PARA", "local_name": "Paravur Shelf",
     "centroid_lat": 8.7600, "centroid_lon": 76.6600, "radius_km": 6.0},
    {"ground_id": "G-QUILON", "local_name": "Quilon Bank",
     "centroid_lat": 8.8500, "centroid_lon": 76.3000, "radius_km": 18.0},
    {"ground_id": "G-WADGE", "local_name": "Wadge Bank",
     "centroid_lat": 7.9500, "centroid_lon": 77.3000, "radius_km": 22.0},
    {"ground_id": "G-TVM-DEEP", "local_name": "Trivandrum Deep",
     "centroid_lat": 8.3000, "centroid_lon": 76.5000, "radius_km": 14.0},
    {"ground_id": "G-ANCHU", "local_name": "Anchuthengu Grounds",
     "centroid_lat": 8.6800, "centroid_lon": 76.7000, "radius_km": 5.0},
    {"ground_id": "G-VIZH", "local_name": "Vizhinjam Offshore",
     "centroid_lat": 8.3700, "centroid_lon": 76.9200, "radius_km": 9.0},
]


def _box(lat0: float, lon0: float, lat1: float, lon1: float) -> Dict[str, Any]:
    return {"type": "Polygon", "coordinates": [[
        [lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0],
    ]]}


# D-05: geofence zones.
ZONES: List[Dict[str, Any]] = [
    {"zone_id": "Z-IMBL-01", "name": "India-Sri Lanka IMBL approach", "type": "IMBL",
     "buffer_km": 5.0, "provenance": "SYNTHETIC",
     "geojson": _box(7.60, 77.10, 7.95, 77.80)},
    {"zone_id": "Z-MPA-01", "name": "Vizhinjam Reef Marine Protected Area", "type": "MPA",
     "buffer_km": 2.0, "provenance": "SYNTHETIC",
     "geojson": _box(8.32, 76.86, 8.42, 76.98)},
    {"zone_id": "Z-SENS-01", "name": "Anchuthengu Turtle Nesting Belt", "type": "SENSITIVE",
     "buffer_km": 2.0, "provenance": "SYNTHETIC",
     "geojson": _box(8.63, 76.68, 8.74, 76.76)},
    {"zone_id": "Z-REST-01", "name": "Vizhinjam Port Approach Channel", "type": "RESTRICTED",
     "buffer_km": 1.5, "provenance": "SYNTHETIC",
     "geojson": _box(8.36, 76.97, 8.41, 77.05)},
    {"zone_id": "Z-REST-02", "name": "Muthalapozhi Harbour Mouth Exclusion", "type": "RESTRICTED",
     "buffer_km": 0.5, "provenance": "SYNTHETIC",
     "geojson": _box(8.628, 76.780, 8.644, 76.792)},
    {"zone_id": "Z-SENS-02", "name": "Quilon Bank Trawl Ban Belt", "type": "SENSITIVE",
     "buffer_km": 3.0, "provenance": "SYNTHETIC",
     "geojson": _box(8.78, 76.20, 8.94, 76.42)},
]

# D-09: demo boat registry. threshold_bucket points at a D-10 hull class.
BOATS: List[Dict[str, Any]] = [
    {"boat_id": "B001", "hull_class": "FRP_SMALL", "length_m": 9.0, "engine_hp": 25,
     "crew": 4, "home_harbour": "Muthalapozhi", "threshold_bucket": "FRP_SMALL"},
    {"boat_id": "B002", "hull_class": "TRAWLER_MED", "length_m": 12.0, "engine_hp": 90,
     "crew": 6, "home_harbour": "Muthalapozhi", "threshold_bucket": "TRAWLER_MED"},
    {"boat_id": "B003", "hull_class": "PLYWOOD_CANOE", "length_m": 6.2, "engine_hp": 9,
     "crew": 3, "home_harbour": "Muthalapozhi", "threshold_bucket": "PLYWOOD_CANOE"},
    {"boat_id": "B004", "hull_class": "FRP_SMALL", "length_m": 8.4, "engine_hp": 15,
     "crew": 3, "home_harbour": "Muthalapozhi", "threshold_bucket": "FRP_SMALL"},
    {"boat_id": "B005", "hull_class": "TRAWLER_DEEP", "length_m": 19.5, "engine_hp": 180,
     "crew": 8, "home_harbour": "Muthalapozhi", "threshold_bucket": "TRAWLER_DEEP"},
]


def pfz_points(lat: float = None, lon: float = None) -> List[Dict[str, Any]]:
    """D-06: PFZ advisory points, dynamically generated around the target to support nationwide queries."""
    import random
    if lat is None or lon is None:
        lat, lon = INLET["lat"], INLET["lon"]
        
    rng = random.Random(hash((round(lat, 1), round(lon, 1))))
    pts = []
    for i in range(24):
        # Scatter within roughly +/- 0.5 degrees (~55km) of the center
        p_lat = round(rng.uniform(lat - 0.5, lat + 0.5), 4)
        p_lon = round(rng.uniform(lon - 0.5, lon + 0.5), 4)
        pts.append({
            "pfz_id": f"PFZ-{i + 1:03d}",
            "lat": p_lat,
            "lon": p_lon,
            "depth_m": round(rng.uniform(25, 180), 1),
            "validity_hrs": 24,
            "confidence": round(rng.uniform(0.55, 0.95), 2),
            "provenance": "SYNTHETIC",
        })
    return pts


def official_advisories() -> List[Dict[str, Any]]:
    """D-11: the bulletin the advisory strip shows alongside ORCA's own output.

    Text is generated in the published bulletin shape, not captured from a real
    INCOIS or IMD issue, and is badged accordingly.
    """
    from datetime import timedelta

    from backend.app.core.dataset import RECORD_START, build_record

    record = build_record()
    out = []
    # One bulletin per day at 05:30 UTC, derived from that day's conditions so
    # it agrees with ORCA most days and genuinely disagrees on some.
    by_day: Dict[Any, Dict[str, Any]] = {}
    for row in record:
        d = row["ts"].date()
        cur = by_day.get(d)
        if cur is None or row["hs_m"] > cur["hs_m"]:
            by_day[d] = row

    for d, row in sorted(by_day.items()):
        hs = row["hs_m"]
        if row["cyclone_flag"]:
            sev, txt = "severe", (
                "Cyclone warning in force. Fishermen are advised not to venture into "
                "the sea off the Kerala coast until further notice.")
        elif hs >= 3.0:
            sev, txt = "warning", (
                f"Rough sea conditions with wave heights around {hs:.1f} m are likely along "
                "the Kerala coast. Fishermen are advised not to venture into the sea.")
        elif hs >= 2.0:
            sev, txt = "advisory", (
                f"Moderate to rough seas with wave heights around {hs:.1f} m are likely. "
                "Small craft are advised to exercise caution.")
        else:
            sev, txt = "advisory", (
                "Sea conditions are expected to remain generally favourable for fishing "
                "operations along the Kerala coast.")
        out.append({
            "issue_ts": (RECORD_START + timedelta(
                days=(d - RECORD_START.date()).days, hours=5, minutes=30)).isoformat(),
            "date": d.isoformat(),
            "issuer": "INCOIS",
            "region": "Kerala coast",
            "text_en": txt,
            "text_ml": "",
            "severity": sev,
            "provenance": "SYNTHETIC_STRUCTURED",
        })
    return out


def ground_rings() -> List[Dict[str, Any]]:
    """GeoJSON features for the named grounds, for the map layer."""
    return [{
        "type": "Feature",
        "properties": {"ground_id": g["ground_id"], "local_name": g["local_name"],
                       "radius_km": g["radius_km"], "provenance": "SYNTHETIC"},
        "geometry": {"type": "Polygon", "coordinates": [
            circle_ring(g["centroid_lat"], g["centroid_lon"], g["radius_km"])]},
    } for g in NAMED_GROUNDS]


def inlet_feature() -> Dict[str, Any]:
    """D-04: the inlet itself, plus its channel axis, as map features."""
    import math
    lat, lon = INLET["lat"], INLET["lon"]
    bearing = math.radians(INLET["channel_bearing_deg"])
    reach_km = 3.0
    dlat = (reach_km / 110.574) * math.cos(bearing)
    dlon = (reach_km / (111.320 * math.cos(math.radians(lat)))) * math.sin(bearing)
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature",
             "properties": {"kind": "inlet", **{k: v for k, v in INLET.items()}},
             "geometry": {"type": "Point", "coordinates": [lon, lat]}},
            {"type": "Feature",
             "properties": {"kind": "channel_axis",
                            "bearing_deg": INLET["channel_bearing_deg"]},
             "geometry": {"type": "LineString", "coordinates": [
                 [round(lon, 6), round(lat, 6)],
                 [round(lon + dlon, 6), round(lat + dlat, 6)]]}},
        ],
    }
