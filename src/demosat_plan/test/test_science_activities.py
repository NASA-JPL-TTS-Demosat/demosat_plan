"""
Tests for the schedule_science_activities method in DemosatScheduler.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from demosat_plan.demosat_scheduler import DemosatScheduler
from demosat_plan.activities.orbit_events import (
    NHemisphereDay, NHemisphereNight, SHemisphereDay, SHemisphereNight
)
from demosat_plan.activities.science_activities import (
    NHemisphereDayScience, NHemisphereNightScience,
    SHemisphereDayScience, SHemisphereNightScience
)


class TestScheduleScienceActivities:
    """Tests for the schedule_science_activities method."""
    
    def test_schedule_science_activities_no_times(self):
        """Test scheduling science activities with no start/end times."""
        scheduler = DemosatScheduler()  # No start/end times
        scheduler.schedule_science_activities()
        assert len(scheduler.activities) == 0
    
    def test_schedule_science_activities_no_quadrants(self, scheduler):
        """Test scheduling science activities with no quadrants."""
        # Ensure no quadrant activities exist
        scheduler.activities = []
        scheduler.below_the_fold_activities = []
        
        # Mock _schedule_science_for_quadrant to verify it's called with default quadrant
        with patch.object(scheduler, '_schedule_science_for_quadrant') as mock_schedule:
            scheduler.schedule_science_activities()
            mock_schedule.assert_called_once_with('NorthDay', scheduler.start_time, scheduler.end_time)
    
    def test_schedule_science_activities_with_quadrants(self, scheduler):
        """Test scheduling science activities with existing quadrants."""
        # Create quadrant activities
        n_day = NHemisphereDay(
            start_time=scheduler.start_time,
            end_time=scheduler.start_time + timedelta(hours=6)
        )
        s_night = SHemisphereNight(
            start_time=scheduler.start_time + timedelta(hours=6),
            end_time=scheduler.end_time
        )
        
        # Add to below-the-fold activities
        scheduler.below_the_fold_activities = [n_day, s_night]
        
        # Mock _schedule_science_for_quadrant to verify it's called for each quadrant
        with patch.object(scheduler, '_schedule_science_for_quadrant') as mock_schedule:
            scheduler.schedule_science_activities()
            
            # Should be called twice, once for each quadrant
            assert mock_schedule.call_count == 2
            
            # Check first call (NorthDay)
            args1 = mock_schedule.call_args_list[0][0]
            assert args1[0] == 'NorthDay'
            assert args1[1] == n_day.begin_time
            assert args1[2] == n_day.end_time
            
            # Check second call (SouthNight)
            args2 = mock_schedule.call_args_list[1][0]
            assert args2[0] == 'SouthNight'
            assert args2[1] == s_night.begin_time
            assert args2[2] == s_night.end_time
    
    def test_schedule_science_for_quadrant(self, scheduler):
        """Test the _schedule_science_for_quadrant method."""
        # Set up a clean scheduler with no activities
        scheduler.activities = []
        
        # Mock _find_gap_for_activity to return a gap
        start_time = scheduler.start_time
        end_time = scheduler.start_time + timedelta(hours=2)
        
        with patch.object(scheduler, '_find_gap_for_activity') as mock_find_gap:
            # Return a gap that covers the entire period
            mock_find_gap.return_value = (start_time, end_time)
            
            # Call the method for North Day quadrant
            scheduler._schedule_science_for_quadrant('NorthDay', start_time, end_time)
            
            # Should add a NHemisphereDayScience activity
            assert len(scheduler.activities) == 1
            activity = scheduler.activities[0]
            assert isinstance(activity, NHemisphereDayScience)
            assert activity.begin_time == start_time
            assert activity.end_time == end_time
