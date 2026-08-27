import pytest
from datetime import datetime, timedelta
from backend.app.core.hazard_engine import (
    calculate_hazard_index,
    evaluate_verdict,
    compute_return_window_and_turnback
)

class MockHullThreshold:
    def __init__(self, m: float, u: float):
        self.index_marginal = m
        self.index_unsafe = u

def test_calculate_hazard_index_ebb_penalty():
    flood_index = calculate_hazard_index(
        {'hs': 2.0, 'tp': 10.0, 'dir': 180, 'swell_hs': 1.0},
        {'stage': 'flood', 'rate': 1.5},
        {'channel_bearing': 180},
        0, 0
    )
    
    ebb_index = calculate_hazard_index(
        {'hs': 2.0, 'tp': 10.0, 'dir': 180, 'swell_hs': 1.0},
        {'stage': 'ebb', 'rate': 1.5},
        {'channel_bearing': 180},
        0, 0
    )
    
    assert ebb_index > flood_index
    # Ebb penalty is k * abs(rate) -> 0.3 * 1.5 = 0.45 
    # w4 * 0.45 -> 0.1 * 0.45 = 0.045
    assert abs((ebb_index - flood_index) - 0.045) < 1e-6

def test_calculate_hazard_index_wave_alignment():
    aligned_index = calculate_hazard_index(
        {'hs': 2.0, 'tp': 10.0, 'dir': 270, 'swell_hs': 1.0},
        {'stage': 'flood', 'rate': 1.0},
        {'channel_bearing': 270},
        0, 0
    )
    
    perp_index = calculate_hazard_index(
        {'hs': 2.0, 'tp': 10.0, 'dir': 180, 'swell_hs': 1.0},
        {'stage': 'flood', 'rate': 1.0},
        {'channel_bearing': 270},
        0, 0
    )
    
    assert aligned_index > perp_index

def test_calculate_hazard_index_override():
    index = calculate_hazard_index(
        {'hs': 0.5, 'tp': 5.0, 'dir': 90, 'swell_hs': 0.1},
        {'stage': 'flood', 'rate': 0.5},
        {'channel_bearing': 90},
        lightning_flag=1, cyclone_flag=0
    )
    assert index == 99.9

def test_evaluate_verdict_boundaries():
    threshold = MockHullThreshold(0.4, 0.7)
    
    assert evaluate_verdict(0.2, threshold) == 'SAFE'
    assert evaluate_verdict(0.4, threshold) == 'MARGINAL'
    assert evaluate_verdict(0.65, threshold) == 'MARGINAL'
    assert evaluate_verdict(0.7, threshold) == 'DO_NOT_CROSS'
    assert evaluate_verdict(1.5, threshold) == 'DO_NOT_CROSS'
    assert evaluate_verdict(99.9, threshold) == 'DO_NOT_CROSS'

def test_compute_return_window_and_turnback():
    threshold = MockHullThreshold(0.4, 0.7)
    base_time = datetime(2026, 8, 27, 8, 0)
    
    hourly_forecast = []
    for i in range(6):
        timestamp = base_time + timedelta(hours=i)
        hs = 1.0 if i < 4 else 5.0  # safe for hours 0-3, DO_NOT_CROSS for hours 4-5
        
        cyclone = 1 if i >= 4 else 0
        hourly_forecast.append({
            'timestamp': timestamp,
            'wave_data': {'hs': hs, 'tp': 8.0, 'dir': 90, 'swell_hs': 0.5},
            'tide_data': {'stage': 'flood', 'rate': 1.0},
            'inlet_geometry': {'channel_bearing': 90},
            'lightning_flag': 0,
            'cyclone_flag': cyclone
        })
        
    departure = base_time
    deadline = base_time + timedelta(hours=6)
    
    # Distance: 15 nm, Speed: 10 knots -> Travel time: 1.5 hours
    window, turnback = compute_return_window_and_turnback(
        hourly_forecast, departure, deadline,
        boat_speed_knots=10.0, distance_nm=15.0,
        hull_threshold=threshold
    )
    
    assert window is not None
    assert window[0] == base_time
    assert window[1] == base_time + timedelta(hours=3) # Hour 3 is the last safe hour
    
    # turnback_time = window[1] - 1.5 hours
    assert turnback == base_time + timedelta(hours=1, minutes=30)
