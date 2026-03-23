"""
Tests for the schedule_orbit_events and schedule_shadow_events methods in DemosatScheduler.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from demosat_plan.orbit_events import (
    AscendingNode, DescendingNode, EarthShadow, NHemisphereDay
)
from demosat_plan.demosat_scheduler import DemosatScheduler

class TestScheduleOrbitEvents:
    """Tests for the schedule_orbit_events method."""
    
    def test_schedule_orbit_events_none(self, scheduler):
        """Test scheduling orbit events when container is None."""
        scheduler.orbit_event_container = None
        scheduler.schedule_orbit_events()
        assert len(scheduler.activities) == 0
        assert len(scheduler.below_the_fold_activities) == 0
    
    def test_schedule_orbit_events(self, scheduler):
        """Test scheduling various orbit events."""
        mock_orbit = MagicMock()
        
        # Ascending node
        asc_event = {
            'Time': scheduler.start_time + timedelta(hours=1),
            'Type': 'Ascending Node Crossing',
            'Orbit Number': 1
        }
        
        # Descending node
        desc_event = {
            'Time': scheduler.start_time + timedelta(hours=2),
            'Type': 'Descending Node Crossing',
            'Orbit Number': 1
        }
        
        mock_orbit.__iter__.return_value = iter([asc_event, desc_event])
        scheduler.orbit_event_container = mock_orbit
        
        scheduler.schedule_orbit_events()
        
        # Check that orbit events were added
        all_activities = scheduler.activities + scheduler.below_the_fold_activities
        assert len(all_activities) == 2
        
        # Check that we have one of each type
        activity_types = [type(activity) for activity in all_activities]
        assert AscendingNode in activity_types
        assert DescendingNode in activity_types


class TestScheduleShadowEvents:
    """Tests for the schedule_shadow_events method."""
    
    def test_schedule_shadow_events_none(self, scheduler):
        """Test scheduling shadow events when container is None."""
        scheduler.orbit_event_container = None
        scheduler.schedule_shadow_events()
        assert len(scheduler.activities) == 0
        assert len(scheduler.below_the_fold_activities) == 0
    
    def test_schedule_shadow_events(self, scheduler):
        """Test scheduling shadow events."""
        mock_orbit = MagicMock()
        
        # Into shadow event
        into_shadow = {
            'Time': scheduler.start_time + timedelta(hours=1),
            'Type': 'Terminator crossing into shadow',
            'Orbit Number': 1
        }
        
        # Out of shadow event
        out_of_shadow = {
            'Time': scheduler.start_time + timedelta(hours=2),
            'Type': 'Terminator crossing out of shadow',
            'Orbit Number': 1
        }
        
        mock_orbit.__iter__.return_value = iter([into_shadow, out_of_shadow])
        scheduler.orbit_event_container = mock_orbit
        
        scheduler.schedule_shadow_events()
        
        # Check that a shadow event was added
        all_activities = scheduler.activities + scheduler.below_the_fold_activities
        assert len(all_activities) == 1
        
        # Check that it's an EarthShadow activity
        shadow = all_activities[0]
        assert isinstance(shadow, EarthShadow)
        assert shadow.begin_time == into_shadow['Time']
        assert shadow.end_time == out_of_shadow['Time']

