"""
Tests for the schedule_calibration_activities method in DemosatScheduler.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from demosat_plan.demosat_scheduler import DemosatScheduler
from demosat_plan.activities.spacecraft_activities import CalibrationActivity


class TestScheduleCalibrationActivities:
    """Tests for the schedule_calibration_activities method."""
    
    def test_schedule_calibration_activities_no_times(self):
        """Test scheduling calibration activities with no start/end times."""
        scheduler = DemosatScheduler()  # No start/end times
        scheduler.schedule_calibration_activities()
        assert len(scheduler.activities) == 0
    
    def test_schedule_calibration_activities_no_events(self, scheduler):
        """Test scheduling calibration activities with no orbit events."""
        scheduler.orbit_event_container = None
        scheduler.schedule_calibration_activities()
        assert len(scheduler.activities) == 0
    
    def test_schedule_calibration_activities(self, scheduler):
        """Test scheduling calibration activities at descending nodes."""
        mock_orbit = MagicMock()
        
        # Create a day's worth of descending nodes
        day = scheduler.start_time.date()
        midnight = datetime.combine(day, datetime.min.time())
        noon = datetime.combine(day, datetime.min.time()) + timedelta(hours=12)
        
        # Descending node after midnight
        desc_midnight = {
            'Time': midnight + timedelta(minutes=30),
            'Type': 'Descending Node Crossing',
            'Orbit Number': 1
        }
        
        # Descending node after noon
        desc_noon = {
            'Time': noon + timedelta(minutes=30),
            'Type': 'Descending Node Crossing',
            'Orbit Number': 2
        }
        
        # Another descending node (should be ignored for calibration)
        desc_other = {
            'Time': midnight + timedelta(hours=6),
            'Type': 'Descending Node Crossing',
            'Orbit Number': 3
        }
        
        mock_orbit.__iter__.return_value = iter([desc_midnight, desc_noon, desc_other])
        scheduler.orbit_event_container = mock_orbit
        
        # Mock _find_gap_for_activity to always return a gap
        with patch.object(scheduler, '_find_gap_for_activity') as mock_find_gap:
            # Return gaps that allow calibration activities
            mock_find_gap.side_effect = lambda start, duration, claims: (start, start + duration)
            
            # Call the method
            scheduler.schedule_calibration_activities()
            
            # Should add two calibration activities (one after midnight, one after noon)
            assert len(scheduler.activities) == 2
            
            # Check that both are calibration activities
            for activity in scheduler.activities:
                assert isinstance(activity, CalibrationActivity)
                
                # Check that one is AM and one is PM
                assert "AM" in activity.name or "PM" in activity.name
