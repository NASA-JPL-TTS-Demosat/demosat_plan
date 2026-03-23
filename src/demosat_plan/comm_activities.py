"""
Communication-related activities for DemoSat.

This module contains activities related to spacecraft communications,
including X-band and S-band communication windows for various ground stations,
as well as setup and breakdown activities for these windows.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from tts_plan.activity import Activity, TemporalRelation
from demosat_plan.claimables import Claimables

class CommSetup(Activity):
    """Communication setup activity.
    
    This activity represents the setup procedure for a communication window.
    It runs at the beginning of a comm window and executes a station and band-specific
    sequence to prepare the spacecraft for communication.
    
    The activity always takes 30 seconds and calls a sequence with the naming pattern:
    "STA_Qband_setup" where STA is the 3-letter station acronym and Q is X or S for the band.
    """
    TYPE = 'CommSetup'
    DESCRIPTION = 'Communication setup activity'
    SETUP_DURATION = timedelta(seconds=30)  # Fixed 30-second setup duration
    
    def __init__(self, start_time: datetime, station_acronym: str, band: str, **kwargs):
        """Initialize a communication setup activity.
        
        Args:
            start_time: When the setup begins
            station_acronym: Three-letter acronym for the ground station (e.g., 'WGS', 'ASF', 'MCO')
            band: Communication band ('X' or 'S')
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        name = f"{station_acronym}_{band}BAND_SETUP"
        sequence_name = f"{station_acronym}_{band}band_setup"
        
        super().__init__(
            begin_time=start_time, 
            duration=self.SETUP_DURATION, 
            name=name, 
            seqid=sequence_name,
            **kwargs
        )
        
        # Claim appropriate band resource
        if band.upper() == 'X':
            self.add_claim(Claimables.XBAND)
        elif band.upper() == 'S':
            self.add_claim(Claimables.SBAND)


class CommBreakdown(Activity):
    """Communication breakdown activity.
    
    This activity represents the breakdown procedure for a communication window.
    It runs at the end of a comm window and executes a sequence to properly
    terminate the communication session.
    
    The activity always takes 10 seconds and calls the "break_down_comm" sequence.
    """
    TYPE = 'CommBreakdown'
    DESCRIPTION = 'Communication breakdown activity'
    BREAKDOWN_DURATION = timedelta(seconds=10)  # Fixed 10-second breakdown duration
    
    def __init__(self, end_time: datetime, station_acronym: str, band: str, **kwargs):
        """Initialize a communication breakdown activity.
        
        Args:
            end_time: When the breakdown ends (same as parent comm window end time)
            station_acronym: Three-letter acronym for the ground station
            band: Communication band ('X' or 'S')
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        # Calculate start time based on the fixed duration
        start_time = end_time - self.BREAKDOWN_DURATION
        name = f"{station_acronym}_{band}BAND_BREAKDOWN"
        
        super().__init__(
            begin_time=start_time, 
            duration=self.BREAKDOWN_DURATION, 
            name=name, 
            seqid="break_down_comm",
            **kwargs
        )
        
        # Claim appropriate band resource
        if band.upper() == 'X':
            self.add_claim(Claimables.XBAND)
        elif band.upper() == 'S':
            self.add_claim(Claimables.SBAND)


class XbandCommWindow(Activity):
    """X-band communication window."""
    TYPE = 'XbandCommWindow'
    DESCRIPTION = 'X-band communication window'
    HIGHLIGHT_FULL_HEIGHT = True
    BELOW_THE_FOLD = False  # Explicitly mark as above-the-fold

    def __init__(self, start_time: datetime, end_time: datetime, name: str, station_acronym: str = "GEN", **kwargs):
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        self.add_claim(Claimables.XBAND)
        self.add_claim(Claimables.ADCS)
        
        # Add constraint to prevent slewing 3 minutes before and 1 minute after the window
        # This is necessary because X-band communication requires precise pointing
        self.add_constraint(
            relation=TemporalRelation.NOT_DURING,
            target="SlewActivity",
            lead_time=timedelta(minutes=3),
            trail_time=timedelta(minutes=1),
            name="no_slew_around_xband",
            description="No slewing allowed 3 minutes before and 1 minute after X-band communication window"
        )
        
        # Add setup and breakdown activities as children
        setup = CommSetup(start_time=start_time, station_acronym=station_acronym, band="X")
        self.add_child(setup)
        
        breakdown = CommBreakdown(end_time=end_time, station_acronym=station_acronym, band="X")
        self.add_child(breakdown)

class SbandCommWindow(Activity):
    """S-band communication window."""
    TYPE = 'SbandCommWindow'
    DESCRIPTION = 'S-band communication window'
    HIGHLIGHT_FULL_HEIGHT = True
    BELOW_THE_FOLD = False  # Explicitly mark as above-the-fold

    def __init__(self, start_time: datetime, end_time: datetime, name: str, station_acronym: str = "GEN", **kwargs):
        super().__init__(begin_time=start_time, duration=end_time-start_time, name=name, **kwargs)
        self.add_claim(Claimables.SBAND)
        self.color = '#008000'        
        # Add setup and breakdown activities as children
        setup = CommSetup(start_time=start_time, station_acronym=station_acronym, band="S")
        self.add_child(setup)
        
        breakdown = CommBreakdown(end_time=end_time, station_acronym=station_acronym, band="S")
        self.add_child(breakdown)

# WGS (Wallops Ground Station) windows
class WgsXbandCommWindow(XbandCommWindow):
    """Wallops Ground Station X-band communication window."""
    TYPE = 'WgsXbandCommWindow'
    DESCRIPTION = 'Wallops Ground Station (WGS) X-band communication window'
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        if name is None:
            name = f"WGS_XBAND_{start_time.strftime('%Y%m%dT%H%M%S')}"
        super().__init__(start_time=start_time, end_time=end_time, name=name, station_acronym="WGS", **kwargs)

class WgsSbandCommWindow(SbandCommWindow):
    """Wallops Ground Station S-band communication window."""
    TYPE = 'WgsSbandCommWindow'
    DESCRIPTION = 'Wallops Ground Station (WGS) S-band communication window'
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        if name is None:
            name = f"WGS_SBAND_{start_time.strftime('%Y%m%dT%H%M%S')}"
        super().__init__(start_time=start_time, end_time=end_time, name=name, station_acronym="WGS", **kwargs)

# ASF (Alaska Satellite Facility) windows
class AsfXbandCommWindow(XbandCommWindow):
    """Alaska Satellite Facility X-band communication window."""
    TYPE = 'AsfXbandCommWindow'
    DESCRIPTION = 'Alaska Satellite Facility (ASF) X-band communication window'
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        if name is None:
            name = f"ASF_XBAND_{start_time.strftime('%Y%m%dT%H%M%S')}"
        super().__init__(start_time=start_time, end_time=end_time, name=name, station_acronym="ASF", **kwargs)

class AsfSbandCommWindow(SbandCommWindow):
    """Alaska Satellite Facility S-band communication window."""
    TYPE = 'AsfSbandCommWindow'
    DESCRIPTION = 'Alaska Satellite Facility (ASF) S-band communication window'
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        if name is None:
            name = f"ASF_SBAND_{start_time.strftime('%Y%m%dT%H%M%S')}"
        super().__init__(start_time=start_time, end_time=end_time, name=name, station_acronym="ASF", **kwargs)

# MCO (McMurdo Station) windows
class McoXbandCommWindow(XbandCommWindow):
    """McMurdo Station X-band communication window."""
    TYPE = 'McoXbandCommWindow'
    DESCRIPTION = 'McMurdo Station (MCO) X-band communication window'
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        if name is None:
            name = f"MCO_XBAND_{start_time.strftime('%Y%m%dT%H%M%S')}"
        super().__init__(start_time=start_time, end_time=end_time, name=name, station_acronym="MCO", **kwargs)

class McoSbandCommWindow(SbandCommWindow):
    """McMurdo Station S-band communication window."""
    TYPE = 'McoSbandCommWindow'
    DESCRIPTION = 'McMurdo Station (MCO) S-band communication window'
    def __init__(self, start_time: datetime, end_time: datetime, name: str = None, **kwargs):
        if name is None:
            name = f"MCO_SBAND_{start_time.strftime('%Y%m%dT%H%M%S')}"
        super().__init__(start_time=start_time, end_time=end_time, name=name, station_acronym="MCO", **kwargs)
