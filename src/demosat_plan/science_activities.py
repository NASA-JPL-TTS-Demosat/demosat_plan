"""
Science-related activities for DemoSat.

This module contains activities related to science operations,
including hemisphere-specific and quadrant-specific science activities.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from tts_plan.activity import Activity
from demosat_plan.claimables import Claimables

class NHemisphereDayScience(Activity):
    """Northern Hemisphere Day Science activity.
    
    Science observations conducted over the Northern Hemisphere during daylight.
    Includes start and stop science activities as children.
    """
    TYPE = 'NHemisphereDayScience'
    DESCRIPTION = 'Northern Hemisphere Day Science'
    COLOR = '#4287f5'  # Bright blue
    
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        # Generate a default name if none provided
        if name is None:
            name = f"N_DAY_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        self.add_claim(Claimables.INSTRUMENT)
        self.add_claim(Claimables.ADCS)
        
        # Add start and stop science activities as children
        start_activity = StartNHemisphereDayScience(start_time=start_time, color=self.COLOR)
        self.add_child(start_activity)
        
        stop_activity = StopScience(start_time=end_time - StopScience.DURATION, color=self.COLOR)
        self.add_child(stop_activity)


class NHemisphereNightScience(Activity):
    """Northern Hemisphere Night Science activity.
    
    Science observations conducted over the Northern Hemisphere during night time.
    Includes start and stop science activities as children.
    """
    TYPE = 'NHemisphereNightScience'
    DESCRIPTION = 'Northern Hemisphere Night Science'
    COLOR = '#1a3c8a'  # Dark blue
    
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        # Generate a default name if none provided
        if name is None:
            name = f"N_NIGHT_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        self.add_claim(Claimables.INSTRUMENT)
        self.add_claim(Claimables.ADCS)
        
        # Add start and stop science activities as children
        start_activity = StartNHemisphereNightScience(start_time=start_time, color=self.COLOR)
        self.add_child(start_activity)
        
        stop_activity = StopScience(start_time=end_time - StopScience.DURATION, color=self.COLOR)
        self.add_child(stop_activity)


class SHemisphereDayScience(Activity):
    """Southern Hemisphere Day Science activity.
    
    Science observations conducted over the Southern Hemisphere during daylight.
    Includes start and stop science activities as children.
    """
    TYPE = 'SHemisphereDayScience'
    DESCRIPTION = 'Southern Hemisphere Day Science'
    COLOR = '#f54242'  # Bright red
    
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        # Generate a default name if none provided
        if name is None:
            name = f"S_DAY_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        self.add_claim(Claimables.INSTRUMENT)
        self.add_claim(Claimables.ADCS)
        
        # Add start and stop science activities as children
        start_activity = StartSHemisphereDayScience(start_time=start_time, color=self.COLOR)
        self.add_child(start_activity)
        
        stop_activity = StopScience(start_time=end_time - StopScience.DURATION, color=self.COLOR)
        self.add_child(stop_activity)


class SHemisphereNightScience(Activity):
    """Southern Hemisphere Night Science activity.
    
    Science observations conducted over the Southern Hemisphere during night time.
    Includes start and stop science activities as children.
    """
    TYPE = 'SHemisphereNightScience'
    DESCRIPTION = 'Southern Hemisphere Night Science'
    COLOR = '#8a1a1a'  # Dark red
    
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        # Generate a default name if none provided
        if name is None:
            name = f"S_NIGHT_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        self.add_claim(Claimables.INSTRUMENT)
        self.add_claim(Claimables.ADCS)
        
        # Add start and stop science activities as children
        start_activity = StartSHemisphereNightScience(start_time=start_time, color=self.COLOR)
        self.add_child(start_activity)
        
        stop_activity = StopScience(start_time=end_time - StopScience.DURATION, color=self.COLOR)
        self.add_child(stop_activity)

class StartScience(Activity):
    """Base class for science start activities.
    
    This class serves as a base for activities that initialize science operations
    for different hemispheres and day/night conditions.
    """
    TYPE = 'StartScience'
    DESCRIPTION = 'Start Science Operations'
    COLOR = '#32CD32'  # Lime Green
    DURATION = timedelta(seconds=1)  # Default duration
    
    def __init__(self, start_time: datetime, name: Optional[str] = None, 
                 duration: Optional[timedelta] = None, command: str = "DO_SCIENCE", **kwargs):
        # Use provided duration or default
        if duration is None:
            duration = self.DURATION
            
        # Generate a default name if none provided
        if name is None:
            name = f"START_SCIENCE_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=duration, name=name, **kwargs)
        self.add_claim(Claimables.INSTRUMENT)
        self.command = command


class StartNHemisphereDayScience(StartScience):
    """Start Northern Hemisphere Day Science activity.
    
    Initializes science operations for the Northern Hemisphere during daylight.
    """
    TYPE = 'StartNHemisphereDayScience'
    DESCRIPTION = 'Start Northern Hemisphere Day Science'
    COLOR = '#32CD32'  # Lime Green
    
    def __init__(self, start_time: datetime, name: Optional[str] = None, 
                 duration: Optional[timedelta] = None, **kwargs):
        if name is None:
            name = f"START_N_DAY_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(start_time=start_time, name=name, duration=duration, 
                         command="DO_SCIENCE N_HEMI DAY", **kwargs)


class StartNHemisphereNightScience(StartScience):
    """Start Northern Hemisphere Night Science activity.
    
    Initializes science operations for the Northern Hemisphere during night time.
    """
    TYPE = 'StartNHemisphereNightScience'
    DESCRIPTION = 'Start Northern Hemisphere Night Science'
    COLOR = '#32CD32'  # Lime Green
    
    def __init__(self, start_time: datetime, name: Optional[str] = None, 
                 duration: Optional[timedelta] = None, **kwargs):
        if name is None:
            name = f"START_N_NIGHT_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(start_time=start_time, name=name, duration=duration, 
                         command="DO_SCIENCE N_HEMI NIGHT", **kwargs)


class StartSHemisphereDayScience(StartScience):
    """Start Southern Hemisphere Day Science activity.
    
    Initializes science operations for the Southern Hemisphere during daylight.
    """
    TYPE = 'StartSHemisphereDayScience'
    DESCRIPTION = 'Start Southern Hemisphere Day Science'
    COLOR = '#32CD32'  # Lime Green
    
    def __init__(self, start_time: datetime, name: Optional[str] = None, 
                 duration: Optional[timedelta] = None, **kwargs):
        if name is None:
            name = f"START_S_DAY_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(start_time=start_time, name=name, duration=duration, 
                         command="DO_SCIENCE S_HEMI DAY", **kwargs)


class StartSHemisphereNightScience(StartScience):
    """Start Southern Hemisphere Night Science activity.
    
    Initializes science operations for the Southern Hemisphere during night time.
    """
    TYPE = 'StartSHemisphereNightScience'
    DESCRIPTION = 'Start Southern Hemisphere Night Science'
    COLOR = '#32CD32'  # Lime Green
    
    def __init__(self, start_time: datetime, name: Optional[str] = None, 
                 duration: Optional[timedelta] = None, **kwargs):
        if name is None:
            name = f"START_S_NIGHT_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(start_time=start_time, name=name, duration=duration, 
                         command="DO_SCIENCE S_HEMI NIGHT", **kwargs)


class StopScience(Activity):
    """Stop Science Operations activity.
    
    Terminates all science operations regardless of hemisphere or day/night condition.
    """
    TYPE = 'StopScience'
    DESCRIPTION = 'Stop Science Operations'
    COLOR = '#FF6347'  # Tomato Red
    DURATION = timedelta(seconds=1) # Default duration
    
    def __init__(self, start_time: datetime, name: Optional[str] = None, 
                 duration: Optional[timedelta] = None, **kwargs):
        # Use provided duration or default
        if duration is None:
            duration = self.DURATION
            
        # Generate a default name if none provided
        if name is None:
            name = f"STOP_SCIENCE_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=duration, name=name, **kwargs)
        self.add_claim(Claimables.INSTRUMENT)
        self.command = "STOP_SCIENCE"
