"""
Pytest fixtures for demosat_plan tests.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from demosat_plan.claimables import Claimables
from demosat_plan.demosat_scheduler import DemosatScheduler


@pytest.fixture
def mock_ephemeris_container():
    """Create a mock ephemeris container."""
    mock_ephem = MagicMock()
    # Create sample ephemeris data
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    mock_items = []
    
    for i in range(100):
        item = MagicMock()
        item.time = start_time + timedelta(minutes=i*15)
        mock_items.append(item)
    
    mock_ephem.__iter__.return_value = iter(mock_items)
    mock_ephem.__getitem__.side_effect = lambda idx: mock_items[idx] if isinstance(idx, int) else mock_items[idx.start:idx.stop]
    
    return mock_ephem


@pytest.fixture
def mock_comm_window_container():
    """Create a mock comm window container."""
    mock_comm = MagicMock()
    
    # Create sample comm window data
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    windows = []
    
    # WGS X-band windows
    for i in range(5):
        window = {
            'Start Time': start_time + timedelta(hours=i*4),
            'End Time': start_time + timedelta(hours=i*4, minutes=20),
            'Station': 'WGS XBAND',
            'Abbreviation': 'WGS'
        }
        windows.append(window)
    
    # ASF S-band windows
    for i in range(5):
        window = {
            'Start Time': start_time + timedelta(hours=i*4 + 2),
            'End Time': start_time + timedelta(hours=i*4 + 2, minutes=15),
            'Station': 'ASF SBAND',
            'Abbreviation': 'ASF'
        }
        windows.append(window)
    
    mock_comm.__iter__.return_value = iter(windows)
    
    return mock_comm


@pytest.fixture
def mock_orbit_event_container():
    """Create a mock orbit event container."""
    mock_orbit = MagicMock()
    
    # Create sample orbit event data
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    events = []
    
    # Ascending nodes
    for i in range(10):
        event = {
            'Time': start_time + timedelta(hours=i*2),
            'Type': 'Ascending Node Crossing',
            'Orbit Number': i
        }
        events.append(event)
    
    # Descending nodes
    for i in range(10):
        event = {
            'Time': start_time + timedelta(hours=i*2 + 1),
            'Type': 'Descending Node Crossing',
            'Orbit Number': i
        }
        events.append(event)
    
    # North Pole crossings
    for i in range(10):
        event = {
            'Time': start_time + timedelta(hours=i*2, minutes=30),
            'Type': 'North Pole Crossing',
            'Orbit Number': i
        }
        events.append(event)
    
    # South Pole crossings
    for i in range(10):
        event = {
            'Time': start_time + timedelta(hours=i*2 + 1, minutes=30),
            'Type': 'South Pole Crossing',
            'Orbit Number': i
        }
        events.append(event)
    
    # Shadow events
    for i in range(10):
        # Into shadow
        event_in = {
            'Time': start_time + timedelta(hours=i*2, minutes=45),
            'Type': 'Terminator crossing into shadow',
            'Orbit Number': i
        }
        events.append(event_in)
        
        # Out of shadow
        event_out = {
            'Time': start_time + timedelta(hours=i*2 + 1, minutes=15),
            'Type': 'Terminator crossing out of shadow',
            'Orbit Number': i
        }
        events.append(event_out)
    
    mock_orbit.__iter__.return_value = iter(events)
    mock_orbit.__len__.return_value = len(events)
    
    return mock_orbit


@pytest.fixture
def scheduler():
    """Create a basic DemosatScheduler instance."""
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    end_time = datetime(2025, 1, 1, 23, 59, 59)
    
    return DemosatScheduler(start_time=start_time, end_time=end_time)


@pytest.fixture
def scheduler_with_containers(mock_ephemeris_container, mock_comm_window_container, mock_orbit_event_container):
    """Create a DemosatScheduler instance with mock containers."""
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    end_time = datetime(2025, 1, 1, 23, 59, 59)
    
    return DemosatScheduler(
        start_time=start_time,
        end_time=end_time,
        ephemeris_container=mock_ephemeris_container,
        comm_window_container=mock_comm_window_container,
        orbit_event_container=mock_orbit_event_container
    )
