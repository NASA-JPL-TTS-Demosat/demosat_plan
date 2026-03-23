"""
Resource claimables for DemoSat activities.

This module defines the resources that can be claimed by activities
to prevent resource conflicts during scheduling.
"""

from enum import Enum, auto

class Claimables(Enum):
    """Enum of resources that can be claimed by activities."""
    CPU = auto()
    INSTRUMENT = auto()
    XBAND = auto()
    SBAND = auto()
    ADCS = auto()
    # Quadrant-specific claimables
    QUADRANT_N_DAY = auto()    # North Hemisphere Day
    QUADRANT_N_NIGHT = auto()  # North Hemisphere Night
    QUADRANT_S_DAY = auto()    # South Hemisphere Day
    QUADRANT_S_NIGHT = auto()  # South Hemisphere Night
