"""
Tests for the schedule_comm_windows method in DemosatScheduler.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from demosat_plan.claimables import Claimables
from demosat_plan.activities.comm_activities import WgsXbandCommWindow


class TestScheduleCommWindows:
    """Tests for the schedule_comm_windows method."""
    
    def test_schedule_comm_windows_none(self, scheduler):
        """Test scheduling comm windows when container is None."""
        scheduler.comm_window_container = None
        scheduler.schedule_comm_windows()
        assert len(scheduler.activities) == 0
    
    def test_schedule_xband_comm_windows(self, scheduler):
        """Test scheduling X-band comm windows."""
        mock_comm = MagicMock()
        
        # WGS X-band window
        wgs_window = {
            'Start Time': scheduler.start_time + timedelta(hours=1),
            'End Time': scheduler.start_time + timedelta(hours=2),
            'Station': 'WGS XBAND',
            'Abbreviation': 'WGS'
        }
        
        mock_comm.__iter__.return_value = iter([wgs_window])
        scheduler.comm_window_container = mock_comm
        scheduler.schedule_comm_windows()
        
        assert len(scheduler.activities) == 1
        activity = scheduler.activities[0]
        assert isinstance(activity, WgsXbandCommWindow)
        assert activity.begin_time == wgs_window['Start Time']
        assert activity.end_time == wgs_window['End Time']
        assert Claimables.XBAND in [c.resource for c in activity.claims]
    
    def test_schedule_sband_comm_windows(self, scheduler):
        """Test scheduling S-band comm windows."""
        mock_comm = MagicMock()
        
        # ASF S-band window
        asf_window = {
            'Start Time': scheduler.start_time + timedelta(hours=3),
            'End Time': scheduler.start_time + timedelta(hours=4),
            'Station': 'ASF SBAND',
            'Abbreviation': 'ASF'
        }
        
        mock_comm.__iter__.return_value = iter([asf_window])
        scheduler.comm_window_container = mock_comm
        scheduler.schedule_comm_windows()
        
        assert len(scheduler.activities) == 1
        activity = scheduler.activities[0]
        assert 'ASF' in activity.name
        assert activity.begin_time == asf_window['Start Time']
        assert activity.end_time == asf_window['End Time']
        assert Claimables.SBAND in [c.resource for c in activity.claims]
