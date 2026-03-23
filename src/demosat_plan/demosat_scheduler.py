"""
DemoSat-specific scheduler implementation.

This module extends the base Scheduler class with DemoSat-specific
functionality for generating schedules based on ephemeris data,
communication windows, and orbit events.
"""

from typing import List, Dict, Any, Optional, Union, Type
from datetime import datetime, timedelta

from tts_html_utils.gantt_chart.gantt_chart import InteractiveGantt

from tts_plan.scheduler import Scheduler
from tts_plan.activity import Activity

# Import from claimables module
from demosat_plan.claimables import Claimables

# Import from orbit_events module
from demosat_plan.orbit_events import (
    AscendingNode, DescendingNode, NPoleCrossing, SPoleCrossing,
    EarthShadow, NHemisphereDay, NHemisphereNight,
    SHemisphereDay, SHemisphereNight
)

# Import from comm_activities module
from demosat_plan.comm_activities import (
    XbandCommWindow, SbandCommWindow,
    WgsXbandCommWindow, WgsSbandCommWindow,
    AsfXbandCommWindow, AsfSbandCommWindow,
    McoXbandCommWindow, McoSbandCommWindow
)

# Import from science_activities module
from demosat_plan.science_activities import (
    NHemisphereDayScience, NHemisphereNightScience,
    SHemisphereDayScience, SHemisphereNightScience,
)

# Import from spacecraft_activities module
from demosat_plan.spacecraft_activities import (
    SlewActivity, CalibrationActivity, AdcsYaw
)

import tts_spice.furnish
import spiceypy as sp

# Load SPICE kernels using tts_spice
tts_spice.furnish.leap_seconds()  
tts_spice.furnish.planetary_ephemerides()  
tts_spice.furnish.planetary_constants()  
tts_spice.furnish.rotation_kernels("earth") 



class DemosatScheduler(Scheduler):
    """
    DemoSat-specific scheduler for generating activity schedules.
    
    This scheduler uses ephemeris data, communication windows, and orbit events
    to generate a schedule of activities for the DemoSat mission.
    """
    MISSION = "DemoSat"
    
    def __init__(self, 
                 start_time: datetime = None, 
                 end_time: datetime = None,
                 ephemeris_container = None,
                 comm_window_container = None,
                 orbit_event_container = None):
        """
        Initialize a new DemosatScheduler.
        
        Args:
            start_time: Start time of the scheduling period
            end_time: End time of the scheduling period
            ephemeris_container: Container with spacecraft ephemeris data
            comm_window_container: Container with communication window data
            orbit_event_container: Container with orbit event data
        """
        super().__init__(start_time, end_time)
        
        self.ephemeris_container = ephemeris_container
        self.comm_window_container = comm_window_container
        self.orbit_event_container = orbit_event_container
        
        # Track when the last calibration was scheduled
        self.last_calibration_time = None
        
    def build_schedule(self) -> List[Activity]:
        """
        Build a schedule of activities based on the available data.
        
        This method implements the mission-specific scheduling logic for DemoSat.
        The general approach is:
        1. Schedule all communication windows
        2. Schedule orbit events
        3. Schedule Earth shadow events
        4. Schedule science activities around other constraints
        5. Schedule calibration activities at the first descending node after midnight and noon each day
        6. Schedule ADCS Yaw activities at each ascending node
        
        Returns:
            List of Activity objects representing the schedule
        """
        # Clear any existing activities
        self.activities = []
        self.below_the_fold_activities = []
        
        # Schedule orbit events (these are fixed points in the orbit)
        self.schedule_orbit_events()
        
        # Schedule Earth shadow events
        self.schedule_shadow_events()
        
        # Schedule orbit quadrants based on orbit events
        self.schedule_orbit_quadrants()

        # Schedule ADCS Yaw activities at ascending nodes
        self.schedule_adcs_yaw_activities()

        # Schedule communication windows first (highest priority)
        self.schedule_comm_windows()
                
        # Schedule calibration activities at descending nodes
        self.schedule_calibration_activities()

        # Schedule science activities in available time slots
        self.schedule_science_activities()
        
    def clear_schedule(self):
        """
        Clear the schedule of activities.
        
        This method is for demonstration purposes only and should not be used in production.
        """
        self.activities = []
        self.below_the_fold_activities = []

    def schedule_comm_windows(self) -> None:
        """
        Schedule all communication windows from the comm window container.
        """
        if self.comm_window_container is None:
            return
            
        # Filter windows by time range and minimum elevation
        for window in self.comm_window_container:
            # Skip windows outside our scheduling period
            if (self.start_time and window['End Time'] < self.start_time or
                self.end_time and window['Start Time'] > self.end_time):
                continue
                
                
            # Create the appropriate window type based on station and band
            station = window['Abbreviation']
            start_time = window['Start Time']
            end_time = window['End Time']
            
            # Determine the window class based on station abbreviation
            if 'XBAND' in window['Station'].upper():
                if station == 'WGS':
                    comm_window = WgsXbandCommWindow(start_time, end_time)
                elif station == 'ASF':
                    comm_window = AsfXbandCommWindow(start_time, end_time)
                elif station == 'MCO':
                    comm_window = McoXbandCommWindow(start_time, end_time)
                else:
                    # Generic X-band window for unknown stations
                    comm_window = XbandCommWindow(start_time, end_time, f"{station}_XBAND", station_acronym=station)
            else:
                # Assume S-band for anything not explicitly X-band
                if station == 'WGS':
                    comm_window = WgsSbandCommWindow(start_time, end_time)
                elif station == 'ASF':
                    comm_window = AsfSbandCommWindow(start_time, end_time)
                elif station == 'MCO':
                    comm_window = McoSbandCommWindow(start_time, end_time)
                else:
                    # Generic S-band window for unknown stations
                    comm_window = SbandCommWindow(start_time, end_time, f"{station}_SBAND", station_acronym=station)
            
            # Add the window to our schedule
            self.add_activity(comm_window)
    
    def schedule_orbit_events(self) -> None:
        """
        Schedule orbit events from the orbit event container.
        """
        if self.orbit_event_container is None or not hasattr(self.orbit_event_container, '__iter__'):
            return
            
        # Process each orbit event
        for event in self.orbit_event_container:
            # Skip events outside our scheduling period
            if (self.start_time and event['Time'] < self.start_time or
                self.end_time and event['Time'] > self.end_time):
                continue
                
            event_time = event['Time']
            event_type = event['Type']
            
            # Skip shadow events - they're handled separately
            if 'shadow' in event_type.lower():
                continue
                
            min_duration = timedelta(seconds=0)
            
            # Get orbit number with a default value if not present
            orbit_number = event['Orbit Number']
            
            if 'Ascending' in event_type:
                orbit_event = AscendingNode(begin_time=event_time, duration=min_duration, 
                                           name=f"ASC_NODE_{orbit_number}")
            elif 'Descending' in event_type:
                orbit_event = DescendingNode(begin_time=event_time, duration=min_duration, 
                                            name=f"DESC_NODE_{orbit_number}")
            elif 'North Pole' in event_type:
                orbit_event = NPoleCrossing(begin_time=event_time, duration=min_duration, 
                                           name=f"N_POLE_{orbit_number}")
            elif 'South Pole' in event_type:
                orbit_event = SPoleCrossing(begin_time=event_time, duration=min_duration, 
                                           name=f"S_POLE_{orbit_number}")
            else:
                # Skip unknown event types
                continue
            
            # Add a comment to indicate this is a point event with artificial duration
            if hasattr(orbit_event, 'description'):
                if orbit_event.description is not None:
                    orbit_event.description += " (point event)"
                else:
                    orbit_event.description = "Point event"
                
                # Ensure the orbit event is marked as below-the-fold
                orbit_event.below_the_fold = True
                
            # Add the event to our schedule
            self.add_activity(orbit_event)
            
    def schedule_orbit_quadrants(self) -> None:
        """
        Schedule orbit quadrants based on orbit events.
        
        This method identifies quadrant boundaries (hemisphere + day/night transitions)
        and creates quadrant activities to mark the time periods.
        """
        # If we don't have start/end times, we can't schedule quadrants
        if not self.start_time or not self.end_time:
            return
            
        # If we don't have orbit events, we'll use a default quadrant for the entire scheduling period
        if self.orbit_event_container is None or not hasattr(self.orbit_event_container, '__iter__'):
            # Default to North Day quadrant for the entire scheduling period
            default_quadrant = NHemisphereDay(start_time=self.start_time, end_time=self.end_time)
            self.add_activity(default_quadrant)
            return
            
        # Check if orbit_event_container has any events
        try:
            event_count = len(list(self.orbit_event_container))
            if event_count == 0:
                # Default to North Day quadrant for the entire scheduling period
                default_quadrant = NHemisphereDay(start_time=self.start_time, end_time=self.end_time)
                self.add_activity(default_quadrant)
                return
        except Exception:
            # Default to North Day quadrant for the entire scheduling period
            default_quadrant = NHemisphereDay(start_time=self.start_time, end_time=self.end_time)
            self.add_activity(default_quadrant)
            return
            
        # First, identify the quadrant boundaries
        # We need to find all pole crossings and day/night transitions
        north_pole_crossings = []  # North pole crossings
        south_pole_crossings = []  # South pole crossings
        into_sunlight = []  # Day side (terminator crossing into sunlight)
        into_shadow = []    # Night side (terminator crossing into shadow)
        hemisphere_transitions = []  # Ascending/Descending node crossings
        
        # Process orbit events to identify quadrant boundaries
        
        for event in self.orbit_event_container:

            # Get event time using attribute access
            event_time = event.time if hasattr(event, 'time') else None
            
            # Get event type from source dictionary
            event_type = None
            if hasattr(event, 'source') and 'Type' in event.source:
                event_type = event.source['Type']
            
            # Skip events outside our scheduling period
            if (self.start_time and event_time and event_time < self.start_time or
                self.end_time and event_time and event_time > self.end_time):
                continue
            
            # Skip events with missing time or type
            if not event_time or not event_type:
                continue
                
            # Categorize the event
            if 'North Pole Crossing' in event_type:
                north_pole_crossings.append((event_time, 'NorthPole'))
            elif 'South Pole Crossing' in event_type:
                south_pole_crossings.append((event_time, 'SouthPole'))
            elif 'Ascending Node Crossing' in event_type:
                # Ascending Node marks transition from South to North hemisphere
                hemisphere_transitions.append((event_time, 'SouthToNorth'))
            elif 'Descending Node Crossing' in event_type:
                # Descending Node marks transition from North to South hemisphere
                hemisphere_transitions.append((event_time, 'NorthToSouth'))
            elif 'Terminator crossing out of shadow' in event_type:
                # Spacecraft is exiting shadow and entering daylight
                # After this event, the spacecraft will be in daylight
                into_sunlight.append((event_time, 'IntoSunlight'))
            elif 'Terminator crossing into shadow' in event_type:
                # Spacecraft is entering shadow (night)
                # After this event, the spacecraft will be in shadow/night
                into_shadow.append((event_time, 'IntoShadow'))
        
        # Combine all events and sort by time
        all_events = north_pole_crossings + south_pole_crossings + into_sunlight + into_shadow + hemisphere_transitions
        all_events.sort()
        
        if not all_events:
            # No quadrant boundaries found, use default quadrant
            default_quadrant = NHemisphereDay(start_time=self.start_time, end_time=self.end_time)
            self.add_activity(default_quadrant)
            return
        
        # Determine the initial quadrant (before the first event)
        # We need to analyze the first few events to determine the initial state
        # Look at the first event to determine our initial state
        first_event_type = all_events[0][1]
        
        # Set initial state based on first event
        if first_event_type in ['NorthToSouth', 'SouthToNorth']:
            # If first event is a hemisphere transition, determine which hemisphere we're starting in
            is_north = first_event_type == 'NorthToSouth'  # If first event is North->South, we start in North
        elif first_event_type == 'NorthPole':
            is_north = False  # If first event is North Pole, we're coming from South
        elif first_event_type == 'SouthPole':
            is_north = True   # If first event is South Pole, we're coming from North
        else:
            # Default to North if we can't determine
            is_north = True
            
        # For day/night transitions
        # With the corrected shadow calculation:
        # - 'IntoShadow' means the spacecraft is transitioning from day to night
        #   After this event, the spacecraft will be in night
        # - 'IntoSunlight' means the spacecraft is transitioning from night to day
        #   After this event, the spacecraft will be in day
        if first_event_type == 'IntoShadow':
            is_day = False   # After this event, we'll be in night
        elif first_event_type == 'IntoSunlight':
            is_day = True    # After this event, we'll be in day
        else:
            # Default to day if we can't determine
            is_day = True
            
        # Set the current quadrant based on our determined initial state
        if is_north and is_day:
            current_quadrant = 'NorthDay'
        elif is_north and not is_day:
            current_quadrant = 'NorthNight'
        elif not is_north and is_day:
            current_quadrant = 'SouthDay'
        else:  # not is_north and not is_day
            current_quadrant = 'SouthNight'
                    
        # Handle the initial period (from start_time to first event)
        if all_events[0][0] > self.start_time:
            quadrant_start = self.start_time
            initial_quadrant_end = all_events[0][0]
            
            # Create the appropriate quadrant activity
            if current_quadrant == 'NorthDay':
                quadrant = NHemisphereDay(start_time=quadrant_start, end_time=initial_quadrant_end)
            elif current_quadrant == 'NorthNight':
                quadrant = NHemisphereNight(start_time=quadrant_start, end_time=initial_quadrant_end)
            elif current_quadrant == 'SouthDay':
                quadrant = SHemisphereDay(start_time=quadrant_start, end_time=initial_quadrant_end)
            elif current_quadrant == 'SouthNight':
                quadrant = SHemisphereNight(start_time=quadrant_start, end_time=initial_quadrant_end)
                
            # Add the quadrant activity to our schedule
            self.add_activity(quadrant)
        
        for i, (event_time, event_type) in enumerate(all_events):
            # Determine which quadrant we're transitioning to
            if event_type == 'NorthPole':
                is_north = True
            elif event_type == 'SouthPole':
                is_north = False
            elif event_type == 'SouthToNorth':  # Ascending node - transition from South to North
                is_north = True
            elif event_type == 'NorthToSouth':  # Descending node - transition from North to South
                is_north = False
            elif event_type == 'IntoSunlight':
                is_day = True     # After this event, we'll be in day
            elif event_type == 'IntoShadow':
                is_day = False    # After this event, we'll be in night
                
            # Determine the new quadrant based on hemisphere and day/night
            if is_north and is_day:
                next_quadrant = 'NorthDay'
            elif is_north and not is_day:
                next_quadrant = 'NorthNight'
            elif not is_north and is_day:
                next_quadrant = 'SouthDay'
            else:  # not is_north and not is_day
                next_quadrant = 'SouthNight'
                
            # If this isn't the last event, create a quadrant that spans to the next event
            if i < len(all_events) - 1:
                quadrant_start = event_time
                quadrant_end = all_events[i+1][0]
                
                # Create the appropriate quadrant activity
                if next_quadrant == 'NorthDay':
                    quadrant = NHemisphereDay(start_time=quadrant_start, end_time=quadrant_end)
                elif next_quadrant == 'NorthNight':
                    quadrant = NHemisphereNight(start_time=quadrant_start, end_time=quadrant_end)
                elif next_quadrant == 'SouthDay':
                    quadrant = SHemisphereDay(start_time=quadrant_start, end_time=quadrant_end)
                elif next_quadrant == 'SouthNight':
                    quadrant = SHemisphereNight(start_time=quadrant_start, end_time=quadrant_end)
                    
                # Add the quadrant activity to our schedule
                self.add_activity(quadrant)
            
            # Update for the next iteration
            current_quadrant = next_quadrant
        
        # Handle the final period (from last event to end_time)
        if all_events[-1][0] < self.end_time:
            quadrant_start = all_events[-1][0]
            quadrant_end = self.end_time
            
            # Create the appropriate quadrant activity
            if current_quadrant == 'NorthDay':
                quadrant = NHemisphereDay(start_time=quadrant_start, end_time=quadrant_end)
            elif current_quadrant == 'NorthNight':
                quadrant = NHemisphereNight(start_time=quadrant_start, end_time=quadrant_end)
            elif current_quadrant == 'SouthDay':
                quadrant = SHemisphereDay(start_time=quadrant_start, end_time=quadrant_end)
            elif current_quadrant == 'SouthNight':
                quadrant = SHemisphereNight(start_time=quadrant_start, end_time=quadrant_end)
                
            # Add the quadrant activity to our schedule
            self.add_activity(quadrant)
    
    def schedule_shadow_events(self) -> None:
        """
        Schedule Earth shadow events from the orbit event container.
        
        This method looks for pairs of "into shadow" and "out of shadow" events
        and creates EarthShadow activities spanning the time between them.
        """
        if self.orbit_event_container is None or not hasattr(self.orbit_event_container, '__iter__'):
            return
            
        # Find all shadow entry/exit events
        shadow_entries = []
        shadow_exits = []
        
        for event in self.orbit_event_container:
            # Skip events outside our scheduling period
            if (self.start_time and event['Time'] < self.start_time or
                self.end_time and event['Time'] > self.end_time):
                continue
                
            event_time = event['Time']
            event_type = event['Type']
            orbit_number = event['Orbit Number']  # Use get() with default value
            
            if event_type == 'Terminator crossing into shadow':
                shadow_entries.append((event_time, orbit_number))
            elif event_type == 'Terminator crossing out of shadow':
                shadow_exits.append((event_time, orbit_number))
        
        # Sort by time
        shadow_entries.sort(key=lambda x: x[0])
        shadow_exits.sort(key=lambda x: x[0])
        
        # Create shadow activities from entry/exit pairs
        for i, (entry_time, entry_orbit) in enumerate(shadow_entries):
            # Find the next exit after this entry
            matching_exits = [exit_data for exit_data in shadow_exits 
                             if exit_data[0] > entry_time]
            
            if matching_exits:
                # Use the first exit after this entry
                exit_time, exit_orbit = matching_exits[0]
                
                # Use the entry's orbit number if available, otherwise use exit's
                orbit_number = entry_orbit if entry_orbit is not None else exit_orbit
                
                # Create the shadow activity
                shadow = EarthShadow(
                    start_time=entry_time,
                    end_time=exit_time,
                    orbit_number=orbit_number
                )
                
                # Add the shadow activity to our schedule
                self.add_activity(shadow)
                
                # Remove this exit so it's not used again
                shadow_exits.remove((exit_time, exit_orbit))
    
    def schedule_science_activities(self) -> None:
        """
        Schedule science activities for each quadrant of the orbit.
        
        This method finds all quadrant activities that have been scheduled and
        schedules appropriate science activities for each one.
        """
        # If we don't have start/end times, we can't schedule science activities
        if not self.start_time or not self.end_time:
            return
        
        # Find all quadrant activities that have been scheduled
        # Check both regular activities and below-the-fold activities
        quadrant_activities = []
        for activity in self.activities + self.below_the_fold_activities:
            if isinstance(activity, (NHemisphereDay, NHemisphereNight, SHemisphereDay, SHemisphereNight)):
                quadrant_activities.append(activity)
                        
        # If no quadrants were found, use a default quadrant for the entire period
        if not quadrant_activities:
            default_quadrant_type = 'NorthDay'
            # Schedule science activities for the default quadrant
            self._schedule_science_for_quadrant(default_quadrant_type, self.start_time, self.end_time)
            return
        
        # Schedule science activities for each quadrant
        for quadrant in quadrant_activities:
            quadrant_type = None
            if isinstance(quadrant, NHemisphereDay):
                quadrant_type = 'NorthDay'
            elif isinstance(quadrant, NHemisphereNight):
                quadrant_type = 'NorthNight'
            elif isinstance(quadrant, SHemisphereDay):
                quadrant_type = 'SouthDay'
            elif isinstance(quadrant, SHemisphereNight):
                quadrant_type = 'SouthNight'
            
            if quadrant_type:
                self._schedule_science_for_quadrant(quadrant_type, quadrant.begin_time, quadrant.end_time)

    def _schedule_science_for_quadrant(self, quadrant_type: str, start_time: datetime, end_time: datetime) -> None:
        """
        Schedule science activities for a specific quadrant.
        
        Args:
            quadrant_type: Type of quadrant ('NorthDay', 'NorthNight', 'SouthDay', 'SouthNight')
            start_time: Start time of the quadrant
            end_time: End time of the quadrant
        """
        # Find gaps for science activities within this quadrant
        current_time = start_time
        
        # Define the claims that science activities will make
        science_claims = [Claimables.INSTRUMENT, Claimables.ADCS]
        
        while current_time < end_time:
            # Check if there's a gap for a science activity, considering resource claims
            gap = self._find_gap_for_activity(current_time, timedelta(minutes=5), science_claims)  # Minimum 1 minute
            
            if gap and gap[0] < end_time:
                # We found a gap within this quadrant, schedule a science activity
                science_start = gap[0]
                # Science activity should end at the end of the gap or the end of the quadrant,
                # whichever comes first
                science_end = min(gap[1], end_time)
                
                # Ensure the science activity is at least the minimum duration
                if science_end - science_start < timedelta(minutes=5):
                    # Skip this gap as it's too small
                    current_time = science_end
                    continue
                
                # Create the appropriate quadrant-specific science activity
                if quadrant_type == 'NorthDay':
                    science = NHemisphereDayScience(start_time=science_start, end_time=science_end)
                elif quadrant_type == 'NorthNight':
                    science = NHemisphereNightScience(start_time=science_start, end_time=science_end)
                elif quadrant_type == 'SouthDay':
                    science = SHemisphereDayScience(start_time=science_start, end_time=science_end)
                elif quadrant_type == 'SouthNight':
                    science = SHemisphereNightScience(start_time=science_start, end_time=science_end)
                
                # Add the science activity to our schedule
                self.add_activity(science)
                
                # Move to the end of this science activity
                current_time = science_end
            else:
                # No gap found, or gap extends beyond quadrant end
                # Move past the next activity or a small increment if no gap found
                if gap:
                    current_time = gap[1]
                else:
                    # No more gaps in this quadrant or increment by a minute to avoid infinite loop
                    current_time += timedelta(minutes=1)
                    if current_time >= end_time:
                        break
    
    def schedule_calibration_activities(self) -> None:
        """
        Schedule calibration activities at descending nodes.
        
        This method adds calibration activities at the first descending node
        after midnight and the first descending node after noon each day.
        """
        # If we don't have start/end times, we can't schedule calibrations
        if not self.start_time or not self.end_time:
            return
            
        # If we don't have orbit events, we can't find descending nodes
        if self.orbit_event_container is None or not hasattr(self.orbit_event_container, '__iter__'):
            return
            
        # Find all descending node events within our scheduling period
        descending_nodes = []
        
        for event in self.orbit_event_container:
            # Skip events outside our scheduling period
            if (self.start_time and event['Time'] < self.start_time or
                self.end_time and event['Time'] > self.end_time):
                continue
                
            # Only consider descending node events
            if 'Descending' in event['Type']:
                descending_nodes.append(event['Time'])
        
        # Sort descending nodes by time
        descending_nodes.sort()
        
        if not descending_nodes:
            return
            
        # Group descending nodes by day
        nodes_by_day = {}
        for node_time in descending_nodes:
            # Use date as key
            day = node_time.date()
            if day not in nodes_by_day:
                nodes_by_day[day] = []
            nodes_by_day[day].append(node_time)
        
        # For each day, find the first node after midnight and the first after noon
        for day, nodes in nodes_by_day.items():
            # Create datetime objects for midnight and noon on this day
            midnight = datetime.combine(day, datetime.min.time())
            noon = datetime.combine(day, datetime.min.time()) + timedelta(hours=12)
            
            # Find first node after midnight
            after_midnight = None
            for node_time in nodes:
                if node_time >= midnight:
                    after_midnight = node_time
                    break
            
            # Find first node after noon
            after_noon = None
            for node_time in nodes:
                if node_time >= noon:
                    after_noon = node_time
                    break
            
            # Schedule calibrations at these nodes if found
            for node_time in [after_midnight, after_noon]:
                if node_time is not None:
                    # Calculate the start time to center the calibration at the node time
                    # For a 5-minute calibration, start 2.5 minutes before the node time
                    calib_start = node_time - timedelta(minutes=2.5)
                    calib_end = calib_start + timedelta(minutes=5)
                    
                    # Define the claims that calibration activities will make
                    calibration_claims = [Claimables.INSTRUMENT, Claimables.ADCS]
                    
                    # Check if there's a gap for the calibration, considering resource claims
                    gap = self._find_gap_for_activity(calib_start, timedelta(minutes=5), calibration_claims)
                    
                    if gap:
                        # Schedule the calibration in this gap
                        # If the gap doesn't allow for perfect centering, adjust as needed
                        if gap[0] > calib_start:
                            # Gap starts later than our ideal start time
                            calib_start = gap[0]
                            calib_end = calib_start + timedelta(minutes=5)
                        
                        # Determine if this is a morning or afternoon calibration
                        time_of_day = "AM" if node_time.hour < 12 else "PM"
                        
                        # Create the calibration activity centered at the descending node
                        calibration = CalibrationActivity(
                            start_time=calib_start,
                            end_time=calib_end,
                            name=f"CALIB_DN_{time_of_day}_{node_time.strftime('%Y%m%dT%H%M%S')}"
                        )
                        
                        # Add description to indicate this is centered at a descending node
                        calibration.description = f"Calibration centered at descending node {time_of_day} on {node_time.strftime('%Y-%m-%d')}."
                        
                        self.add_activity(calibration)
                        self.last_calibration_time = calib_end
    
    def add_activity(self, activity: Activity) -> None:
        """
        Add an activity to the schedule with appropriate color.
        
        This method overrides the base class method to apply colors to activities
        based on their type and station.
        
        Args:
            activity: The activity to add to the schedule
        """
        # Apply color based on activity type
        activity_type = activity.__class__.__name__
                
        # Call the parent class method to add the activity
        super().add_activity(activity)
    

    def schedule_adcs_yaw_activities(self) -> None:
        """
        Schedule ADCS Yaw activities at each ascending node.
        
        This method adds a 5-minute AdcsYaw activity centered on each ascending node.
        """
        # If we don't have orbit events, we can't find ascending nodes
        if self.orbit_event_container is None or not hasattr(self.orbit_event_container, '__iter__'):
            return
            
        # Find all ascending node events within our scheduling period
        ascending_nodes = []
        south_pole_crossings = []
        
        for event in self.orbit_event_container:
            # Skip events outside our scheduling period
            if (self.start_time and event['Time'] < self.start_time or
                self.end_time and event['Time'] > self.end_time):
                continue
                
            # Only consider ascending node events
            if 'Ascending' in event['Type']:
                ascending_nodes.append(event['Time'])
            elif 'South Pole Crossing' in event['Type']:
                south_pole_crossings.append(event['Time'])
        
        # Sort ascending nodes by time
        ascending_nodes.sort()
        
        # Schedule an AdcsYaw activity at each ascending node
        for node_time in ascending_nodes:
            # Calculate the start and end times for a 5-minute activity centered on the node
            yaw_duration = timedelta(minutes=5)
            
            # Define the claims that ADCS Yaw activities will make
            yaw_claims = [Claimables.ADCS, Claimables.INSTRUMENT, Claimables.XBAND]
            
            # Check if there's a gap for the yaw activity, considering resource claims
            start_time = node_time - (yaw_duration / 2)
            # Check for a gap that can accommodate this activity
            gap = self._find_gap_for_activity(start_time, yaw_duration, yaw_claims) #TO DO: Don't just find a gap. Make this mandatory and throw an error if it cannot be scheduled
            
            if gap:
                # Adjust start time if necessary to fit in the gap
                adjusted_start = gap[0]
                
                # Create the AdcsYaw activity
                yaw_activity = AdcsYaw(
                    node_time=node_time,
                    duration=yaw_duration,
                    name=f"ADCS_YAW_{node_time.strftime('%Y%m%dT%H%M%S')}",
                    degrees=180 #for the purposes of this demo it doesn't matter if it's plus or minus. it just needs to be the opposite of the other yaw
                )
                
                # Add the activity to the schedule
                self.add_activity(yaw_activity)

        # Schedule an AdcsYaw activity at each South Pole crossing
        for crossing_time in south_pole_crossings:
            # Calculate the start and end times for a 5-minute activity centered on the crossing
            yaw_duration = timedelta(minutes=5)
            
            # Define the claims that ADCS Yaw activities will make
            yaw_claims = [Claimables.ADCS, Claimables.INSTRUMENT, Claimables.XBAND]
            
            # Check if there's a gap for the yaw activity, considering resource claims
            start_time = crossing_time - (yaw_duration / 2)
            # Check for a gap that can accommodate this activity
            gap = self._find_gap_for_activity(start_time, yaw_duration, yaw_claims)
            
            if gap:
                # Adjust start time if necessary to fit in the gap
                adjusted_start = gap[0]
                
                # Create the AdcsYaw activity
                yaw_activity = AdcsYaw(
                    node_time=crossing_time,
                    duration=yaw_duration,
                    name=f"ADCS_YAW_SPOLE_{crossing_time.strftime('%Y%m%dT%H%M%S')}",
                    degrees= -180 #for the purposes of this demo it doesn't matter if it's plus or minus. it just needs to be the opposite of the other yaw
                )
                
                # Add the activity to the schedule
                self.add_activity(yaw_activity)


    def _find_gap_for_activity(self, after_time: datetime, min_duration: timedelta, claims=None) -> Optional[tuple]:
        """
        Find a gap in the schedule for an activity with the given minimum duration and resource claims.
        
        Args:
            after_time: Time after which to look for a gap
            min_duration: Minimum duration needed for the activity
            claims: Optional list of resources that the activity will claim
            
        Returns:
            Tuple of (start_time, end_time) for the gap, or None if no suitable gap found
        """
        # Get all activities that end after the specified time
        future_activities = sorted(
            [a for a in self.activities if a.end_time > after_time],
            key=lambda a: a.begin_time
        )
        
        # Start looking from the specified time
        current_time = after_time
        
        while True:
            # If we've reached the end of the scheduling period, check if there's a valid gap at the end
            if not future_activities:
                if self.end_time and self.end_time - current_time >= min_duration:
                    # For the final gap, check for resource conflicts
                    if claims:
                        # Find all activities that overlap with this final gap
                        overlapping = [a for a in self.activities if 
                                      (a.begin_time < self.end_time and a.end_time > current_time)]
                        
                        # Check if any overlapping activity claims the same resources
                        has_conflict = False
                        for a in overlapping:
                            if hasattr(a, 'claims') and a.claims:
                                for claim in claims:
                                    if claim in a.claims:
                                        has_conflict = True
                                        break
                            if has_conflict:
                                break
                        
                        if not has_conflict:
                            return (current_time, self.end_time)
                    else:
                        # No claims to check, so this final gap is valid
                        return (current_time, self.end_time)
                
                # No more activities and no valid gap at the end
                return None
            
            # Get the next activity
            next_activity = future_activities[0]
            
            # If there's a gap before this activity, check if it's big enough
            if next_activity.begin_time - current_time >= min_duration:
                # Check for resource conflicts during this gap
                if claims:
                    # Find all activities that overlap with this gap
                    overlapping = [a for a in self.activities if 
                                  (a.begin_time < next_activity.begin_time and a.end_time > current_time)]
                    
                    # Check if any overlapping activity claims the same resources
                    has_conflict = False
                    for a in overlapping:
                        if hasattr(a, 'claims') and a.claims:
                            # Check if any claim conflicts
                            for claim in claims:
                                if claim in a.claims:
                                    has_conflict = True
                                    break
                        if has_conflict:
                            break
                    
                    if not has_conflict:
                        # Found a valid gap with no conflicts
                        return (current_time, next_activity.begin_time)
                    else:
                        # Found a conflict, move past the conflicting activities
                        # Find the latest end time of all conflicting activities
                        conflict_end_time = max([a.end_time for a in overlapping if 
                                               hasattr(a, 'claims') and any(claim in a.claims for claim in claims)])
                        current_time = max(current_time, conflict_end_time)
                else:
                    # No claims to check, so this gap is valid
                    return (current_time, next_activity.begin_time)
            else:
                # Gap is too small, move past this activity
                current_time = max(current_time, next_activity.end_time)
            
            # Remove activities that end before or at the current time
            future_activities = [a for a in future_activities if a.end_time > current_time]

    def to_gantt_chart(self):
        activities = self.merge_above_and_below_the_fold()
        activities.sort(key=lambda x: (x.BELOW_THE_FOLD, x.begin_time))
        gantt_data = [activity.to_json() for activity in activities]
        gantt_data = self._convert_datetime_to_iso(gantt_data)
        return InteractiveGantt(
                data=gantt_data,  # Pass the native Python dict directly
                name_key='name',
                start_key='begin_time',
                end_key='end_time',
                children_key='children',
                default_depth=0, # Only expand root items, keep children collapsed
                inner_width='1500px',
                height='100vh'  # Use full viewport height
            )
 


    def _convert_datetime_to_iso(self, obj):
        if isinstance(obj, dict):
            return {k: self._convert_datetime_to_iso(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime_to_iso(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj       