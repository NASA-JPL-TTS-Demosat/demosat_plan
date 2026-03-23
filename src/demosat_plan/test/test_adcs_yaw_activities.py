"""
Tests for the schedule_adcs_yaw_activities method in DemosatScheduler.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from demosat_plan.demosat_scheduler import DemosatScheduler
from demosat_plan.spacecraft_activities import AdcsYaw


class TestScheduleAdcsYawActivities:
    """Tests for the schedule_adcs_yaw_activities method."""
    
    def test_schedule_adcs_yaw_activities_no_events(self, scheduler):
        """Test scheduling ADCS yaw activities with no orbit events."""
        scheduler.orbit_event_container = None
        scheduler.schedule_adcs_yaw_activities()
        assert len(scheduler.activities) == 0
    
    def test_schedule_adcs_yaw_activities(self, scheduler):
        """Test scheduling ADCS yaw activities at ascending nodes."""
        mock_orbit = MagicMock()
        
        # Ascending node
        asc_event = {
            'Time': scheduler.start_time + timedelta(hours=1),
            'Type': 'Ascending Node Crossing',
            'Orbit Number': 1
        }
        
        # South pole crossing
        spole_event = {
            'Time': scheduler.start_time + timedelta(hours=2),
            'Type': 'South Pole Crossing',
            'Orbit Number': 1
        }
        
        mock_orbit.__iter__.return_value = iter([asc_event, spole_event])
        scheduler.orbit_event_container = mock_orbit
        
        # Mock _find_gap_for_activity to always return a gap
        with patch.object(scheduler, '_find_gap_for_activity') as mock_find_gap:
            # Return gaps that allow yaw activities
            mock_find_gap.side_effect = lambda start, duration, claims: (start, start + duration)
            
            # Call the method
            scheduler.schedule_adcs_yaw_activities()
            
            # Should add two ADCS yaw activities (one at ascending node, one at south pole)
            assert len(scheduler.activities) == 2
            
            # Check that both are AdcsYaw activities
            for activity in scheduler.activities:
                assert isinstance(activity, AdcsYaw)
                
            # Check that one is for ascending node and one is for south pole
            activity_names = [activity.name for activity in scheduler.activities]
            assert any("ADCS_YAW_" in name and "SPOLE" not in name for name in activity_names)
            assert any("ADCS_YAW_SPOLE" in name for name in activity_names)
