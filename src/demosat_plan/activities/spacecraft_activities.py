"""
Spacecraft operation activities for DemoSat.

This module contains activities related to spacecraft operations,
including slews, calibrations, and ADCS operations.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from tts_plan.activity import Activity
from demosat_plan.claimables import Claimables

class CalibrationActivity(Activity):
    """Instrument calibration activity.
    
    This activity represents a calibration procedure for the spacecraft's instruments.
    It requires both the instrument itself and the ADCS (Attitude Determination and Control System)
    since precise pointing is typically needed during calibration procedures.
    
    Calibration activities are essential for maintaining instrument accuracy and
    ensuring the quality of science data throughout the mission.
    """
    TYPE = 'CalibrationActivity'
    DESCRIPTION = 'Instrument calibration activity'
    COLOR = "#FFA500"
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        """Initialize a calibration activity.
        
        Args:
            start_time: When the calibration activity begins
            end_time: When the calibration activity ends
            name: Optional name for the activity (default: auto-generated based on time)
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        # Generate a default name if none provided
        if name is None:
            name = f"CALIB_{start_time.strftime('%Y%m%dT%H%M%S')}"
            
        super().__init__(
            begin_time=start_time, 
            duration=end_time-start_time, 
            name=name, 
            seqid="dark_side_calibration",
            **kwargs
            )
        
        # Claim required resources
        self.add_claim(Claimables.INSTRUMENT)
        self.add_claim(Claimables.ADCS)

class SlewSettle(Activity):
    """Slew settle period activity.
    
    This represents the period after a slew maneuver where the spacecraft is allowed
    to settle into its new attitude. During this time, the spacecraft's pointing
    stabilizes to the required accuracy for science or communication operations.
    
    This activity is always 1 minute long and is automatically added at the end of
    a SlewActivity.
    """
    TYPE = 'SlewSettle'
    DESCRIPTION = 'Slew settle period'
    SETTLE_DURATION = timedelta(minutes=1)  # Fixed 1-minute settle duration
    
    def __init__(self, end_time: datetime, parent_name: str, **kwargs):
        """Initialize a slew settle activity.
        
        Args:
            end_time: When the settle period ends (same as parent slew end time)
            parent_name: Name of the parent slew activity
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        # Calculate start time based on the fixed duration
        start_time = end_time - self.SETTLE_DURATION
        name = f"{parent_name}_SETTLE"
        
        super().__init__(begin_time=start_time, duration=self.SETTLE_DURATION, name=name, **kwargs)
        
        # Claim the same resources as the slew
        self.add_claim(Claimables.ADCS)
        self.add_claim(Claimables.INSTRUMENT)


class SlewActivity(Activity):
    """Spacecraft slew (attitude change) activity.
    
    This activity represents a maneuver to change the spacecraft's pointing direction.
    It automatically includes a 1-minute settle period at the end.
    
    When users specify a slew duration, they're specifying the active slew time only.
    The total activity duration will be the specified duration plus the 1-minute settle time.
    """
    TYPE = 'SlewActivity'
    DESCRIPTION = 'Slew activity'
    
    def __init__(self, start_time: datetime, duration: timedelta = None, end_time: datetime = None, 
                 name: str = None, include_settle: bool = True, **kwargs):
        """Initialize a slew activity with an automatic settle period.
        
        Args:
            start_time: When the slew begins
            duration: Duration of the active slew (excluding settle time)
            end_time: When the entire activity (including settle) ends
            name: Optional name for the activity
            include_settle: Whether to include the settle period (default: True)
            **kwargs: Additional keyword arguments passed to the parent Activity class
            
        Note:
            Provide either duration OR end_time, not both.
            - If duration is provided, end_time will be calculated as start_time + duration + settle_time
            - If end_time is provided, duration will be calculated as end_time - start_time - settle_time
        """
        settle_time = SlewSettle.SETTLE_DURATION if include_settle else timedelta(0)
        
        # Generate a default name if none provided
        if name is None:
            name = f"SLEW_{start_time.strftime('%Y%m%dT%H%M%S')}"
        
        # Calculate the appropriate duration or end time
        if duration is not None and end_time is not None:
            raise ValueError("Provide either duration OR end_time, not both")
        elif duration is not None:
            # User specified duration (active slew only)
            total_duration = duration + settle_time
            actual_end_time = start_time + total_duration
        elif end_time is not None:
            # User specified end time (including settle)
            total_duration = end_time - start_time
            if total_duration <= settle_time and include_settle:
                raise ValueError(f"Total duration must be greater than settle time ({settle_time})")
        else:
            raise ValueError("Either duration or end_time must be provided")
        
        # Initialize with the total duration (including settle if applicable)
        super().__init__(begin_time=start_time, duration=total_duration, name=name, **kwargs)
        
        # Claim required resources
        self.add_claim(Claimables.ADCS)
        self.add_claim(Claimables.INSTRUMENT)
        
        # Add settle activity as a child if requested
        if include_settle:
            settle = SlewSettle(end_time=self.end_time, parent_name=self.name)
            self.activities.append(settle)

class AdcsYaw(Activity):
    """ADCS Yaw activity centered on ascending nodes.
    
    This activity represents a yaw maneuver performed by the Attitude Determination
    and Control System (ADCS) at each ascending node crossing.
    """
    TYPE = 'AdcsYaw'
    DESCRIPTION = 'ADCS Yaw maneuver at ascending node'
    COLOR = '#800080'  # Purple
    
    def __init__(self, node_time: datetime, duration: timedelta = timedelta(minutes=5), degrees: float = 180, name: str = None, **kwargs):
        """Initialize an ADCS Yaw activity centered on an ascending node.
        
        Args:
            node_time: Time of the ascending node (center of the activity)
            duration: Total duration of the activity (default: 5 minutes)
            degrees: Rotation angle in degrees (default: 180)
            name: Optional name for the activity
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        # Calculate start time to center the activity on the node time
        start_time = node_time - (duration / 2)
        
        # Generate a default name if none provided
        if name is None:
            name = f"ADCS_YAW_{node_time.strftime('%Y%m%dT%H%M%S')}"
        
        super().__init__(
            begin_time=start_time,
            duration=duration, 
            name=name, 
            command=f"ADCS_YAW {degrees}",
            **kwargs)
        
        # Store node_time and degrees in metadata for serialization
        self.metadata['node_time'] = node_time
        self.metadata['degrees'] = degrees
        
        # Claim ADCS resource
        self.add_claim(Claimables.ADCS)
        self.add_claim(Claimables.INSTRUMENT)
        self.add_claim(Claimables.XBAND)
        
        # Add description to indicate this is centered at an ascending node
        self.description = f"ADCS Yaw maneuver centered at ascending node on {node_time.strftime('%Y-%m-%d %H:%M:%S')}."
