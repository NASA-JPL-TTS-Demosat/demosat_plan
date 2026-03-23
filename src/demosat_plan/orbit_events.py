"""
Orbit event activities for DemoSat.

This module contains activities related to orbit events such as
ascending/descending nodes, pole crossings, Earth shadow periods,
and orbit quadrants.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from tts_plan.activity import Activity
from demosat_plan.claimables import Claimables

class OrbitEvent(Activity):
    """Base class for orbit events."""
    HIGHLIGHT_FULL_HEIGHT = True
    BELOW_THE_FOLD = True

class AscendingNode(OrbitEvent):
    """Ascending node crossing event."""
    TYPE = 'AscendingNode'
    DESCRIPTION = 'Ascending node crossing'

class DescendingNode(OrbitEvent):
    """Descending node crossing event."""
    TYPE = 'DescendingNode'
    DESCRIPTION = 'Descending node crossing'

class NPoleCrossing(OrbitEvent):
    """North pole crossing event."""
    TYPE = 'NPoleCrossing'
    DESCRIPTION = 'North pole crossing'

class SPoleCrossing(OrbitEvent):
    """South pole crossing event."""
    TYPE = 'SPoleCrossing'
    DESCRIPTION = 'South pole crossing'

class EarthShadow(OrbitEvent):
    """Earth shadow activity.
    
    This activity represents periods when the spacecraft is in Earth's shadow.
    It's displayed below the fold with a dark gray color and full height highlighting.
    """
    TYPE = 'EarthShadow'
    DESCRIPTION = 'Earth shadow period'
    HIGHLIGHT_FULL_HEIGHT = True
    BELOW_THE_FOLD = True
    
    def __init__(self, start_time: datetime, end_time: datetime, orbit_number: int = None, **kwargs):
        """Initialize an Earth shadow activity.
        
        Args:
            start_time: When the spacecraft enters Earth's shadow
            end_time: When the spacecraft exits Earth's shadow
            orbit_number: Optional orbit number for the shadow event
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        name = f"EARTH_SHADOW"
        if orbit_number is not None:
            name += f"_{orbit_number}"
        
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        self.color = '#333333'  # Dark gray

class Quadrant(Activity):
    """Base class for orbit quadrants."""
    BELOW_THE_FOLD = True

class NHemisphereDay(Quadrant):
    """North Hemisphere Day quadrant."""
    TYPE = 'NHemisphereDay'
    DESCRIPTION = 'North Hemisphere Day Quadrant'
    COLOR = '#32CD32'  # Lime Green (brighter for day)
    
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        """Initialize a North Hemisphere Day quadrant.
        
        Args:
            start_time: When the quadrant begins
            end_time: When the quadrant ends
            name: Optional name for the quadrant
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        # Generate a default name if none provided
        if name is None:
            name = f"N_DAY_QUADRANT_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        # Claim this specific quadrant resource
        self.add_claim(Claimables.QUADRANT_N_DAY)
        
    
class SHemisphereDay(Quadrant):
    """South Hemisphere Day quadrant."""
    TYPE = 'SHemisphereDay'
    DESCRIPTION = 'South Hemisphere Day Quadrant'
    COLOR = '#32CD32'  # Lime Green (brighter for day)
    
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        """Initialize a South Hemisphere Day quadrant.
        
        Args:
            start_time: When the quadrant begins
            end_time: When the quadrant ends
            name: Optional name for the quadrant
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        # Generate a default name if none provided
        if name is None:
            name = f"S_DAY_QUADRANT_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        # Claim this specific quadrant resource
        self.add_claim(Claimables.QUADRANT_S_DAY)

class NHemisphereNight(Quadrant):
    """North Hemisphere Night quadrant."""
    TYPE = 'NHemisphereNight'
    DESCRIPTION = 'North Hemisphere Night Quadrant'
    COLOR = '#006400'  # Dark Green (darker for night)
    
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        """Initialize a North Hemisphere Night quadrant.
        
        Args:
            start_time: When the quadrant begins
            end_time: When the quadrant ends
            name: Optional name for the quadrant
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        # Generate a default name if none provided
        if name is None:
            name = f"N_NIGHT_QUADRANT_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        # Claim this specific quadrant resource
        self.add_claim(Claimables.QUADRANT_N_NIGHT)

class SHemisphereNight(Quadrant):
    """South Hemisphere Night quadrant."""
    TYPE = 'SHemisphereNight'
    DESCRIPTION = 'South Hemisphere Night Quadrant'
    COLOR = '#006400'  # Dark Green (darker for night)
    
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        """Initialize a South Hemisphere Night quadrant.
        
        Args:
            start_time: When the quadrant begins
            end_time: When the quadrant ends
            name: Optional name for the quadrant
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        # Generate a default name if none provided
        if name is None:
            name = f"S_NIGHT_QUADRANT_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        # Claim this specific quadrant resource
        self.add_claim(Claimables.QUADRANT_S_NIGHT)
