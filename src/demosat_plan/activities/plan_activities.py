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

class HandoverActivity(Activity):
    """Communication setup activity.
    
    This activity represents the setup procedure for a communication window.
    It runs at the beginning of a comm window and executes a station and band-specific
    sequence to prepare the spacecraft for communication.
    
    The activity always takes 30 seconds and calls a sequence with the naming pattern:
    "STA_Qband_setup" where STA is the 3-letter station acronym and Q is X or S for the band.
    """
    TYPE = 'Handover'
    DESCRIPTION = 'Planned handover from one plan to the next'
    
    def __init__(self, handover_time: datetime, seqid: str = None):
        """Initialize a handover activity
        
        Args:
            handover_time: Time for the handover to occur. Handovers are instantaneous
            seqid: onboard sequence name for next plan's background sequence. If None, will defauly to background_YYYY_MM_DD
            band: Communication band ('X' or 'S')
            **kwargs: Additional keyword arguments passed to the parent Activity class
        """
        name = f"{handover_time.strftime('%Y_%m_%d')}_HANDOVER"
        seqid = seqid if seqid is not None else f"background_{handover_time.strftime('%Y_%m_%d')}"
        
        super().__init__(
            begin_time=handover_time, 
            duration=0, 
            name=name, 
            seqid=seqid,
        )
        
        # Right not handovers don't claim any resources. Some missions might want to enforce no activities
        # over handover, but many missions want to be able to do a handover at any time, even when an
        # activity is running, so we choose to do nothing here.
        # See https://github.jpl.nasa.gov/teamtools-studio/tts_plan/issues/17

