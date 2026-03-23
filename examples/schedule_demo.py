#!/usr/bin/env python3
"""
Example script demonstrating the use of DemosatScheduler.

This script loads ephemeris data, calculates communication windows and orbit events,
and then uses the DemosatScheduler to generate a schedule of activities.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Import from demosat_seq package
from demosat_data_utils.ephemeris import EphemerisContainer
from demosat_data_utils.comm_windows import CommWindowContainer
from demosat_data_utils.orbit_events import OrbitEventContainer
from demosat_data_utils.ground_stations import GroundStationContainer

from tts_html_utils.gantt_chart.gantt_chart import InteractiveGantt
from tts_html_utils.core.compiler import HtmlCompiler

from demosat_plan.demosat_scheduler import DemosatScheduler

import spiceypy as sp

# Define SPICE kernel paths
spice_base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demosat_seq", "demo", "spice")

sp.furnsh(os.path.join(spice_base, "de430.bsp"))  # Planetary ephemerides
sp.furnsh(os.path.join(spice_base, "naif0012.tls"))  # Leap seconds
sp.furnsh(os.path.join(spice_base, "pck00010.tpc"))
sp.furnsh(os.path.join(spice_base, "earth_latest_high_prec.bpc"))
print("SPICE kernels loaded successfully")

def main():
    """Main function to demonstrate the DemosatScheduler."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate and visualize a DemoSat schedule")
    parser.add_argument("--output", type=str, default="schedule_output.html", help="Output file for visualization")
    parser.add_argument("--json-output", type=str, help="Output file for JSON data (defaults to same name as --output with .json extension)")
    parser.add_argument("--min-elevation", type=float, default=30.0, help="Minimum elevation for comm windows")
    args = parser.parse_args()
    
    # Define the path to the ephemeris file
    ephemeris_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "demosat_seq", "demo", "ephemeris.txt"
    )
    
    # Ensure the path exists
    if not os.path.exists(ephemeris_path):
        print(f"Warning: Ephemeris file not found at {ephemeris_path}")
        # Try an alternative path
        ephemeris_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "demosat_seq", "ephemeris.txt"
        )
        if not os.path.exists(ephemeris_path):
            print(f"Warning: Ephemeris file not found at alternate path {ephemeris_path}")
            # One more attempt with a simpler path
            ephemeris_path = "../../demosat_seq/demo/ephemeris.txt"
            print(f"Trying with path: {ephemeris_path}")
    
    print(f"Using ephemeris file: {ephemeris_path}")
    
    # Load the ephemeris data
    print(f"Loading ephemeris data from {ephemeris_path}...")
    ephem_container = EphemerisContainer(csv_path=ephemeris_path, cast_fields=True)

        
    start_time = min(item.time for item in ephem_container)
    end_time = max(item.time for item in ephem_container[:3000])
    
    print(f"Ephemeris time range: {start_time} to {end_time}")
    
    # Create a ground station container with default stations
    stations = GroundStationContainer()
    
    # Calculate communication windows
    print("Calculating communication windows...")
    comm_windows = CommWindowContainer(ephem=ephem_container, stations=stations, min_el=args.min_elevation)
    
    # Calculate orbit events
    print("Calculating orbit events...")
    orbit_events = OrbitEventContainer(ephem=ephem_container)

    # Create the scheduler
    print("Creating scheduler...")
    scheduler = DemosatScheduler(
        start_time=start_time,
        end_time=end_time,
        ephemeris_container=ephem_container,
        comm_window_container=comm_windows,
        orbit_event_container=orbit_events
    )
    
    # Build the schedule
    print("Building schedule...")
    scheduler.build_schedule()
    # Get the activities from the scheduler
    activities = scheduler.activities + scheduler.below_the_fold_activities
    # Sort activities: above-the-fold first in time order, then below-the-fold in time order
    # This sorting will be preserved in the JSON and displayed as-is in the Gantt chart
    activities.sort(key=lambda x: (getattr(x, 'below_the_fold', False), x.begin_time if hasattr(x, 'begin_time') and x.begin_time else datetime.min))
    
    # Print a summary of the schedule
    print("\nSchedule Summary:")
    print(f"Total activities: {len(activities)}")
    
    # Count activities by type
    activity_types = {}
    for activity in activities:
        activity_type = activity.__class__.__name__
        activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
    
    for activity_type, count in activity_types.items():
        print(f"  {activity_type}: {count}")
    
    # Save the scheduler data to JSON using the new to_json_file method
    json_output = args.json_output if args.json_output else 'schedule_output.json'
    print(f"\nSaving scheduler data to JSON: {json_output}")
    scheduler.to_json_file(json_output)
    
    # Generate the data for InteractiveGantt directly from activities
    # Convert each activity to JSON
    gantt_data = [activity.to_json() for activity in activities]
    # Convert datetime objects to ISO format strings
    def convert_datetime_to_iso(obj):
        if isinstance(obj, dict):
            return {k: convert_datetime_to_iso(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime_to_iso(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    # Apply the conversion to the entire data structure
    gantt_data = convert_datetime_to_iso(gantt_data)
    
    print("Initializing...")
    
    chart = InteractiveGantt(
        data=gantt_data,  # Pass the native Python dict directly
        name_key='name',
        start_key='begin_time',
        end_key='end_time',
        children_key='children',
        default_depth=0, # Only expand root items, keep children collapsed
        inner_width='1500px',
        height='100vh'  # Use full viewport height
    )

    print("Compiling...")
    compiler = HtmlCompiler(title="Schedule Visualization")
    
    
    compiler.add_body_component(chart)
    compiler.render_to_file(args.output)
    print(f"Done! Open '{args.output}'")
        
    # Uncomment the following lines for debugging
    # import pdb
    # pdb.set_trace()
if __name__ == "__main__":
    main()
