"""
AeroUnity - Unified Aerospace Mission Planning Framework

Main entry point for running both aircraft and spacecraft mission planning.
"""

import numpy as np
from datetime import datetime, timedelta
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.aircraft.models import AircraftParams, WindModel
from src.aircraft.planner import AircraftMissionPlanner
from src.aircraft.simulator import FlightSimulator
from src.spacecraft.orbit import OrbitalElements, GroundTarget, GroundStation
from src.spacecraft.planner import SpacecraftMissionPlanner
from src.spacecraft.scheduler import MissionScheduler
from shapely.geometry import Polygon


def run_aircraft_mission():
    """Run example aircraft mission planning."""
    print("=" * 70)
    print("AIRCRAFT MISSION PLANNING")
    print("=" * 70)
    
    # Define aircraft parameters
    aircraft_params = AircraftParams(
        max_speed=25.0,
        min_speed=10.0,
        max_climb_rate=3.0,
        max_bank_angle=np.radians(45),
        max_turn_rate=np.radians(30),
        battery_capacity=500.0 * 3600  # 500 Wh
    )
    
    # Define wind model
    wind_model = WindModel(
        wind_type='constant',
        base_wind=np.array([3.0, 2.0, 0.0]),  # 3 m/s east, 2 m/s north
        seed=42
    )
    
    # Define waypoints (x, y, altitude in meters)
    waypoints = [
        np.array([0.0, 0.0, 100.0]),      # Start
        np.array([1000.0, 500.0, 150.0]),  # WP1
        np.array([2000.0, 1500.0, 200.0]), # WP2
        np.array([3000.0, 1000.0, 150.0]), # WP3
        np.array([4000.0, 0.0, 100.0]),    # WP4
        np.array([5000.0, 500.0, 100.0]),  # End
    ]
    
    # Define no-fly zones (simplified polygons)
    no_fly_zones = [
        Polygon([(1500, 800), (1800, 800), (1800, 1200), (1500, 1200)]),
        Polygon([(3500, 200), (3800, 200), (3800, 600), (3500, 600)])
    ]
    
    print(f"\nMission Parameters:")
    print(f"  Waypoints: {len(waypoints)}")
    print(f"  No-fly zones: {len(no_fly_zones)}")
    print(f"  Wind: {wind_model.base_wind[:2]} m/s")
    print(f"  Max speed: {aircraft_params.max_speed} m/s")
    
    # Create planner
    planner = AircraftMissionPlanner(
        name="UAV_Mission_1",
        aircraft_params=aircraft_params,
        wind_model=wind_model,
        waypoints=waypoints,
        no_fly_zones=no_fly_zones
    )
    
    # Solve
    print("\nSolving...")
    solution = planner.solve()
    
    # Display results
    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)
    print(f"Route found: {len(solution['route_indices'])} waypoints")
    print(f"Total distance: {solution['distance']:.1f} m")
    print(f"Total time: {solution['total_time']:.1f} s ({solution['total_time']/60:.1f} min)")
    print(f"Total energy: {solution['total_energy']:.1f} J ({solution['total_energy']/3600:.1f} Wh)")
    
    # Validate constraints
    is_valid, violations = planner.validate_solution(solution)
    print(f"\nConstraint validation: {'PASS' if is_valid else 'FAIL'}")
    if violations:
        print("Violations:")
        for v in violations:
            print(f"  - {v}")
    
    # Save results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    import json
    with open(output_dir / "aircraft_solution.json", 'w') as f:
        # Convert numpy arrays to lists for JSON
        json_solution = {
            'route_indices': solution['route_indices'],
            'path': [p.tolist() for p in solution['path']],
            'times': solution['times'],
            'total_time': solution['total_time'],
            'total_energy': solution['total_energy'],
            'distance': solution['distance']
        }
        json.dump(json_solution, f, indent=2)
    
    print(f"\nResults saved to {output_dir / 'aircraft_solution.json'}")
    
    return solution


def run_spacecraft_mission():
    """Run example spacecraft mission planning."""
    print("\n" + "=" * 70)
    print("SPACECRAFT MISSION PLANNING")
    print("=" * 70)
    
    # Define orbital elements (LEO CubeSat)
    epoch = datetime(2026, 2, 11, 0, 0, 0)
    orbital_elements = OrbitalElements(
        semi_major_axis=6371.0 + 550.0,  # 550 km altitude
        eccentricity=0.001,  # Nearly circular
        inclination=np.radians(97.4),  # Sun-synchronous
        raan=np.radians(0.0),
        arg_periapsis=np.radians(0.0),
        true_anomaly=np.radians(0.0),
        epoch=epoch
    )
    
    # Define ground targets
    ground_targets = [
        GroundTarget("Target_1", 37.7749, -122.4194, priority=10.0),  # San Francisco
        GroundTarget("Target_2", 40.7128, -74.0060, priority=8.0),    # New York
        GroundTarget("Target_3", 51.5074, -0.1278, priority=9.0),     # London
        GroundTarget("Target_4", 35.6762, 139.6503, priority=7.0),    # Tokyo
        GroundTarget("Target_5", -33.8688, 151.2093, priority=6.0),   # Sydney
    ]
    
    # Define ground stations
    ground_stations = [
        GroundStation("GS_Alaska", 64.8378, -147.7164),
        GroundStation("GS_Hawaii", 19.8968, -155.5828),
        GroundStation("GS_Norway", 69.6492, 18.9553),
    ]
    
    print(f"\nMission Parameters:")
    print(f"  Orbit altitude: 550 km")
    print(f"  Inclination: 97.4° (sun-synchronous)")
    print(f"  Ground targets: {len(ground_targets)}")
    print(f"  Ground stations: {len(ground_stations)}")
    print(f"  Mission duration: 7 days")
    
    # Create planner
    print("\nComputing visibility windows...")
    planner = SpacecraftMissionPlanner(
        name="CubeSat_Mission_1",
        orbital_elements=orbital_elements,
        ground_targets=ground_targets,
        ground_stations=ground_stations,
        mission_duration_days=7
    )
    
    print(f"Target visibility windows computed: {sum(len(w) for w in planner.target_windows.values())}")
    print(f"Station contact windows computed: {sum(len(w) for w in planner.station_windows.values())}")
    
    # Solve
    print("\nSolving...")
    solution = planner.solve()
    
    # Display results
    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)
    print(f"Observations scheduled: {solution['num_observations']}")
    print(f"Downlinks scheduled: {solution['num_downlinks']}")
    print(f"Total science value: {solution['mission_value']:.1f}")
    
    # Validate constraints
    is_valid, violations = planner.validate_solution(solution)
    print(f"\nConstraint validation: {'PASS' if is_valid else 'FAIL'}")
    if violations:
        print("Violations:")
        for v in violations:
            print(f"  - {v}")
    
    # Compute statistics
    stats = MissionScheduler.compute_statistics(solution['schedule'])
    print(f"\nSchedule Statistics:")
    print(f"  Total activities: {stats['total_activities']}")
    print(f"  Mission duration: {stats['total_duration_hours']:.1f} hours")
    print(f"  Active time: {stats['active_time_hours']:.2f} hours")
    print(f"  Utilization: {stats['utilization_percent']:.1f}%")
    
    # Save results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    MissionScheduler.export_to_json(solution['schedule'], 
                                    output_dir / "spacecraft_schedule.json")
    MissionScheduler.export_to_csv(solution['schedule'],
                                   output_dir / "spacecraft_schedule.csv")
    
    print(f"\nResults saved to {output_dir}/spacecraft_schedule.*")
    
    return solution


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AeroUnity - Unified Aerospace Mission Planning Framework"
    )
    parser.add_argument(
        '--mission',
        choices=['aircraft', 'spacecraft', 'both'],
        default='both',
        help='Which mission to run'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("AeroUnity - Unified Aerospace Mission Planning Framework")
    print("AeroHack 2026 Challenge Submission")
    print("=" * 70)
    
    try:
        if args.mission in ['aircraft', 'both']:
            aircraft_solution = run_aircraft_mission()
        
        if args.mission in ['spacecraft', 'both']:
            spacecraft_solution = run_spacecraft_mission()
        
        print("\n" + "=" * 70)
        print("MISSION PLANNING COMPLETE")
        print("=" * 70)
        print("\nBoth missions demonstrate the unified planning framework:")
        print("  OK Common constraint representation")
        print("  OK Common objective functions")
        print("  OK Shared solver approach (OR-Tools)")
        print("  OK Constraint validation")
        print("\nCheck the 'outputs/' directory for detailed results.")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
