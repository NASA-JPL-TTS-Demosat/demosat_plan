"""
Tests for the DemosatScheduler class.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from demosat_plan.demosat_scheduler import DemosatScheduler
from demosat_plan.claimables import Claimables
from demosat_plan.comm_activities import (
    XbandCommWindow, SbandCommWindow, 
    WgsXbandCommWindow, AsfSbandCommWindow
)
from demosat_plan.orbit_events import (
    AscendingNode, DescendingNode, NPoleCrossing, SPoleCrossing,
    EarthShadow, NHemisphereDay, NHemisphereNight, 
    SHemisphereDay, SHemisphereNight
)
from demosat_plan.science_activities import (
    NHemisphereDayScience, NHemisphereNightScience,
    SHemisphereDayScience, SHemisphereNightScience
)
from demosat_plan.spacecraft_activities import (
    SlewActivity, CalibrationActivity, AdcsYaw
)


class TestDemosatSchedulerInit:
    """Tests for DemosatScheduler initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        scheduler = DemosatScheduler()
        
        assert scheduler.start_time is None
        assert scheduler.end_time is None
        assert scheduler.ephemeris_container is None
        assert scheduler.comm_window_container is None
        assert scheduler.orbit_event_container is None
        assert scheduler.last_calibration_time is None
        assert scheduler.activities == []
        assert scheduler.below_the_fold_activities == []
    
    def test_init_with_times(self):
        """Test initialization with start and end times."""
        start_time = datetime(2025, 1, 1)
        end_time = datetime(2025, 1, 2)
        
        scheduler = DemosatScheduler(start_time=start_time, end_time=end_time)
        
        assert scheduler.start_time == start_time
        assert scheduler.end_time == end_time
        assert scheduler.ephemeris_container is None
        assert scheduler.comm_window_container is None
        assert scheduler.orbit_event_container is None
    
    def test_init_with_containers(self, mock_ephemeris_container, mock_comm_window_container, mock_orbit_event_container):
        """Test initialization with all containers."""
        start_time = datetime(2025, 1, 1)
        end_time = datetime(2025, 1, 2)
        
        scheduler = DemosatScheduler(
            start_time=start_time,
            end_time=end_time,
            ephemeris_container=mock_ephemeris_container,
            comm_window_container=mock_comm_window_container,
            orbit_event_container=mock_orbit_event_container
        )
        
        assert scheduler.start_time == start_time
        assert scheduler.end_time == end_time
        assert scheduler.ephemeris_container == mock_ephemeris_container
        assert scheduler.comm_window_container == mock_comm_window_container
        assert scheduler.orbit_event_container == mock_orbit_event_container


class TestDemosatSchedulerBuildSchedule:
    """Tests for the build_schedule method."""
    
    def test_build_schedule_calls_all_methods(self, scheduler_with_containers):
        """Test that build_schedule calls all the necessary scheduling methods."""
        # Create spy methods
        with patch.object(scheduler_with_containers, 'schedule_orbit_events') as mock_orbit_events, \
             patch.object(scheduler_with_containers, 'schedule_shadow_events') as mock_shadow_events, \
             patch.object(scheduler_with_containers, 'schedule_orbit_quadrants') as mock_orbit_quadrants, \
             patch.object(scheduler_with_containers, 'schedule_adcs_yaw_activities') as mock_adcs_yaw, \
             patch.object(scheduler_with_containers, 'schedule_comm_windows') as mock_comm_windows, \
             patch.object(scheduler_with_containers, 'schedule_calibration_activities') as mock_calibration, \
             patch.object(scheduler_with_containers, 'schedule_science_activities') as mock_science:
            
            # Call the method
            scheduler_with_containers.build_schedule()
            
            # Verify all methods were called in the correct order
            mock_orbit_events.assert_called_once()
            mock_shadow_events.assert_called_once()
            mock_orbit_quadrants.assert_called_once()
            mock_adcs_yaw.assert_called_once()
            mock_comm_windows.assert_called_once()
            mock_calibration.assert_called_once()
            mock_science.assert_called_once()
    
    def test_clear_schedule(self, scheduler_with_containers):
        """Test that clear_schedule clears all activities."""
        # Add some activities
        activity1 = MagicMock()
        activity2 = MagicMock()
        scheduler_with_containers.activities = [activity1]
        scheduler_with_containers.below_the_fold_activities = [activity2]
        
        # Call clear_schedule
        scheduler_with_containers.clear_schedule()
        
        # Verify activities are cleared
        assert scheduler_with_containers.activities == []
        assert scheduler_with_containers.below_the_fold_activities == []


class TestFindGapForActivity:
    """Tests for the _find_gap_for_activity method."""
    
    def test_find_gap_no_activities(self, scheduler):
        """Test finding a gap when there are no activities."""
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        duration = timedelta(minutes=30)
        
        gap = scheduler._find_gap_for_activity(start_time, duration)
        
        assert gap is not None
        assert gap[0] == start_time
        assert gap[1] == scheduler.end_time
    
    def test_find_gap_with_activities(self, scheduler):
        """Test finding a gap with existing activities."""
        # Set up activities
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        
        # Add an activity from 11:00 to 12:00
        activity = MagicMock()
        activity.begin_time = datetime(2025, 1, 1, 11, 0, 0)
        activity.end_time = datetime(2025, 1, 1, 12, 0, 0)
        scheduler.activities = [activity]
        
        # Look for a gap after 10:00 with 30 minute duration
        gap = scheduler._find_gap_for_activity(start_time, timedelta(minutes=30))
        
        assert gap is not None
        assert gap[0] == start_time
        assert gap[1] == activity.begin_time
    
    def test_find_gap_with_resource_conflict(self, scheduler):
        """Test finding a gap with resource conflicts."""
        # Set up activities
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        
        # Add an activity from 10:15 to 10:45 that claims XBAND
        activity = MagicMock()
        activity.begin_time = datetime(2025, 1, 1, 10, 15, 0)
        activity.end_time = datetime(2025, 1, 1, 10, 45, 0)
        activity.claims = [Claimables.XBAND]
        scheduler.activities = [activity]
        
        # Look for a gap after 10:00 with 30 minute duration that claims XBAND
        gap = scheduler._find_gap_for_activity(start_time, timedelta(minutes=30), [Claimables.XBAND])
        
        # Should find a gap after the activity
        assert gap is not None
        assert gap[0] == activity.end_time
        
        # Look for a gap that claims a different resource (should find one starting at start_time)
        gap = scheduler._find_gap_for_activity(start_time, timedelta(minutes=30), [Claimables.SBAND])
        
        assert gap is not None
        assert gap[0] == activity.end_time
    
    def test_find_gap_no_suitable_gap(self, scheduler):
        """Test when no suitable gap is found."""
        # Set end time to be very close to start time
        scheduler.end_time = datetime(2025, 1, 1, 10, 5, 0)
        
        # Look for a gap that's longer than available time
        gap = scheduler._find_gap_for_activity(datetime(2025, 1, 1, 10, 0, 0), timedelta(minutes=10))
        
        assert gap is None
