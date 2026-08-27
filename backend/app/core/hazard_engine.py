import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

def normalize(val: float, min_val: float, max_val: float) -> float:
    """Min-max normalization bounded to [0, 1]."""
    if val <= min_val:
        return 0.0
    if val >= max_val:
        return 1.0
    return (val - min_val) / (max_val - min_val)

def calculate_hazard_index(
    wave_data: Dict[str, float],
    tide_data: Dict[str, Any],
    inlet_geometry: Dict[str, float],
    lightning_flag: int,
    cyclone_flag: int,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Computes a deterministic hazard index (SRS 5.3) in [0, 1].

    Lightning and cyclone are treated as override-strength signals rather than
    weighted contributions: either one is disqualifying on its own regardless
    of wave state, so it saturates the index at 1.0.
    """
    if weights is None:
        weights = {
            'w1': 0.3, 'w2': 0.15, 'w3': 0.15, 
            'w4': 0.1, 'w5': 0.1, 'w6': 0.1, 'w7': 0.1
        }
    
    # Overrides: either flag saturates the index, keeping the [0, 1] contract.
    if lightning_flag == 1 or cyclone_flag == 1:
        return 1.0

    hs = wave_data.get('hs', 0.0)
    tp = wave_data.get('tp', 0.0)
    wave_dir = wave_data.get('dir', 0.0)
    swell_hs = wave_data.get('swell_hs', 0.0)
    
    stage = str(tide_data.get('stage', 'flood')).lower()
    rate = float(tide_data.get('rate', 0.0))
    
    channel_bearing = inlet_geometry.get('channel_bearing', 0.0)
    
    # Normalizations based on Kerala hindcast ranges
    n_hs = normalize(hs, 0.0, 5.0)
    n_tp = normalize(tp, 4.0, 22.0)
    
    # Wave alignment: cos-similarity between wave direction and channel axis clipped to [0, 1]
    diff_rad = math.radians(wave_dir - channel_bearing)
    align_val = max(0.0, math.cos(diff_rad))
    
    # Ebb penalty: an outgoing tide against incoming swell steepens the bar.
    k = 0.3
    ebb_penalty = min(1.0, k * abs(rate)) if stage == 'ebb' else 0.0
    
    # Swell ratio: long-period swell dominating wind sea is the dangerous case.
    swell_ratio = min(1.0, swell_hs / max(hs, 0.01))
    
    index = (
        weights.get('w1', 0.3) * n_hs +
        weights.get('w2', 0.15) * n_tp +
        weights.get('w3', 0.15) * align_val +
        weights.get('w4', 0.1) * ebb_penalty +
        weights.get('w5', 0.1) * swell_ratio +
        weights.get('w6', 0.1) * float(lightning_flag) +
        weights.get('w7', 0.1) * float(cyclone_flag)
    )
    
    # Weights sum to 1 and every term is bounded to [0, 1], so the index is too.
    return float(min(1.0, max(0.0, index)))


def evaluate_verdict(index: float, hull_threshold: Any) -> str:
    """
    Evaluates the final verdict string against hull-specific thresholds.
    """
    if index < hull_threshold.index_marginal:
        return 'SAFE'
    elif hull_threshold.index_marginal <= index < hull_threshold.index_unsafe:
        return 'MARGINAL'
    else:
        return 'DO_NOT_CROSS'


def compute_return_window_and_turnback(
    hourly_forecast: List[Dict[str, Any]],
    departure_time: datetime,
    return_deadline: datetime,
    boat_speed_knots: float,
    distance_nm: float,
    hull_threshold: Any
) -> Tuple[Optional[Tuple[datetime, datetime]], Optional[datetime]]:
    """
    Computes the contiguous return window and absolute turn-back time.
    """
    if boat_speed_knots <= 0:
        travel_time_hours = 0.0
    else:
        travel_time_hours = distance_nm / boat_speed_knots
        
    travel_timedelta = timedelta(hours=travel_time_hours)
    
    # Filter valid forecasts within the given departure and deadline window
    valid_forecasts = [
        f for f in hourly_forecast 
        if departure_time <= f['timestamp'] <= return_deadline
    ]
    
    # Sort strictly by timestamp
    valid_forecasts.sort(key=lambda x: x['timestamp'])
    
    window_start = None
    window_end = None
    
    for f in valid_forecasts:
        index = calculate_hazard_index(
            f.get('wave_data', {}),
            f.get('tide_data', {}),
            f.get('inlet_geometry', {}),
            f.get('lightning_flag', 0),
            f.get('cyclone_flag', 0)
        )
        
        verdict = evaluate_verdict(index, hull_threshold)
        
        if verdict != 'DO_NOT_CROSS':
            if window_start is None:
                window_start = f['timestamp']
            window_end = f['timestamp']
        else:
            if window_start is not None:
                # Contiguous span breaks
                break
                
    if window_start is None or window_end is None:
        return None, None
        
    turnback_time = window_end - travel_timedelta
    
    if turnback_time < departure_time:
        return (window_start, window_end), None
        
    return (window_start, window_end), turnback_time
