"""
Complete AeroUnity validation and results generation pipeline.

This script runs both missions with full validation, generates all plots,
and creates the complete results bundle for submission.
"""

import numpy as np
from datetime import datetime
from pathlib import Path
import json
from shapely.geometry import Polygon

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.aircraft.models import AircraftParams, WindModel
from src.aircraft.planner import AircraftMissionPlanner
from src.spacecraft.orbit import OrbitalElements, GroundTarget, GroundStation
from src.spacecraft.planner import SpacecraftMissionPlanner
from src.spacecraft.scheduler import MissionScheduler
from src.visualization.aircraft_viz import AircraftVisualizer
from src.visualization.spacecraft_viz import SpacecraftVisualizer
from validation.aircraft_validation import AircraftValidator
from validation.spacecraft_validation import SpacecraftValidator


def run_complete_pipeline():
    """Run complete validation and visualization pipeline."""
    
    print("\n" + "=" * 80)
    print(" " * 20 + "AEROUNITY - COMPLETE VALIDATION PIPELINE")
    print("=" * 80)
    print("\nGenerating comprehensive results for AeroHack 2026 submission...")
    print("This will create all validation data, plots, and metrics.\n")
    
    # ========================================================================
    # AIRCRAFT MISSION
    # ========================================================================
    
    print("\n" + "─" * 80)
    print("PART 1: AIRCRAFT MISSION PLANNING & VALIDATION")
    print("─" * 80)
    
    # Define aircraft scenario
    aircraft_params = AircraftParams(
        max_speed=25.0,
        min_speed=10.0,
        max_climb_rate=3.0,
        max_bank_angle=np.radians(45),
        max_turn_rate=np.radians(30),
        battery_capacity=500.0 * 3600
    )
    
    waypoints = [
        np.array([0.0, 0.0, 100.0]),
        np.array([1000.0, 500.0, 150.0]),
        np.array([2000.0, 1500.0, 200.0]),
        np.array([3000.0, 1000.0, 150.0]),
        np.array([4000.0, 0.0, 100.0]),
        np.array([5000.0, 500.0, 100.0]),
    ]
    
    no_fly_zones = [
        Polygon([(1500, 800), (1800, 800), (1800, 1200), (1500, 1200)]),
        Polygon([(3500, 200), (3800, 200), (3800, 600), (3500, 600)])
    ]
    
    wind_model = WindModel(
        wind_type='constant',
        base_wind=np.array([3.0, 2.0, 0.0]),
        seed=42
    )
    
    # Run aircraft planner
    print("\n1. Running aircraft mission planner...")
    aircraft_planner = AircraftMissionPlanner(
        name="UAV_Mission",
        aircraft_params=aircraft_params,
        wind_model=wind_model,
        waypoints=waypoints,
        no_fly_zones=no_fly_zones
    )
    
    aircraft_solution = aircraft_planner.solve()
    print(f"   OK Route found: {len(aircraft_solution['route_indices'])} waypoints")
    print(f"   OK Total time: {aircraft_solution['total_time']/60:.1f} min")
    print(f"   OK Total energy: {aircraft_solution['total_energy']/3600:.1f} Wh")
    
    # Validate aircraft solution
    print("\n2. Validating aircraft constraints...")
    is_valid, violations = aircraft_planner.validate_solution(aircraft_solution)
    print(f"   OK Constraint check: {'PASS' if is_valid else 'FAIL'}")
    if violations:
        for v in violations:
            print(f"     - {v}")
    
    # Run aircraft validation suite
    print("\n3. Running aircraft validation suite...")
    aircraft_scenario = {
        'aircraft_params': aircraft_params,
        'waypoints': waypoints,
        'no_fly_zones': no_fly_zones,
        'base_wind': np.array([3.0, 2.0, 0.0])
    }
    
    aircraft_validator = AircraftValidator()
    mc_results = aircraft_validator.monte_carlo_wind_test(aircraft_scenario, num_trials=100)
    constraint_results = aircraft_validator.constraint_violation_check(aircraft_scenario)
    performance_metrics = aircraft_validator.performance_metrics(aircraft_scenario)
    
    # Generate aircraft visualizations
    print("\n4. Generating aircraft visualizations...")
    aircraft_viz = AircraftVisualizer()
    aircraft_viz.plot_flight_path(aircraft_solution, no_fly_zones)
    aircraft_viz.plot_altitude_profile(aircraft_solution)
    aircraft_viz.plot_performance_metrics(performance_metrics)
    aircraft_viz.plot_monte_carlo_results(mc_results)
    
    # ========================================================================
    # SPACECRAFT MISSION
    # ========================================================================
    
    print("\n" + "─" * 80)
    print("PART 2: SPACECRAFT MISSION PLANNING & VALIDATION")
    print("─" * 80)
    
    # Define spacecraft scenario
    epoch = datetime(2026, 2, 11, 0, 0, 0)
    orbital_elements = OrbitalElements(
        semi_major_axis=6371.0 + 550.0,
        eccentricity=0.001,
        inclination=np.radians(97.4),
        raan=np.radians(0.0),
        arg_periapsis=np.radians(0.0),
        true_anomaly=np.radians(0.0),
        epoch=epoch
    )
    
    ground_targets = [
        GroundTarget("San_Francisco", 37.7749, -122.4194, priority=10.0),
        GroundTarget("New_York", 40.7128, -74.0060, priority=8.0),
        GroundTarget("London", 51.5074, -0.1278, priority=9.0),
        GroundTarget("Tokyo", 35.6762, 139.6503, priority=7.0),
        GroundTarget("Sydney", -33.8688, 151.2093, priority=6.0),
    ]
    
    ground_stations = [
        GroundStation("GS_Alaska", 64.8378, -147.7164),
        GroundStation("GS_Hawaii", 19.8968, -155.5828),
        GroundStation("GS_Norway", 69.6492, 18.9553),
    ]
    
    # Run spacecraft planner
    print("\n1. Running spacecraft mission planner...")
    print("   (Computing visibility windows...)")
    spacecraft_planner = SpacecraftMissionPlanner(
        name="CubeSat_Mission",
        orbital_elements=orbital_elements,
        ground_targets=ground_targets,
        ground_stations=ground_stations,
        mission_duration_days=7
    )
    
    spacecraft_solution = spacecraft_planner.solve()
    print(f"   OK Observations scheduled: {spacecraft_solution['num_observations']}")
    print(f"   OK Downlinks scheduled: {spacecraft_solution['num_downlinks']}")
    print(f"   OK Science value: {spacecraft_solution['mission_value']:.1f}")
    
    # Validate spacecraft solution
    print("\n2. Validating spacecraft constraints...")
    is_valid, violations = spacecraft_planner.validate_solution(spacecraft_solution)
    print(f"   OK Constraint check: {'PASS' if is_valid else 'FAIL'}")
    if violations:
        for v in violations:
            print(f"     - {v}")
    
    # Run spacecraft validation suite
    print("\n3. Running spacecraft validation suite...")
    spacecraft_scenario = {
        'orbital_elements': orbital_elements,
        'ground_targets': ground_targets,
        'ground_stations': ground_stations,
        'mission_duration_days': 7
    }
    
    spacecraft_validator = SpacecraftValidator()
    feasibility_results = spacecraft_validator.schedule_feasibility_check(spacecraft_scenario)
    value_metrics = spacecraft_validator.mission_value_metrics(spacecraft_scenario)
    stress_results = spacecraft_validator.stress_test_scenarios(spacecraft_scenario)
    
    # Export spacecraft schedule
    print("\n4. Exporting spacecraft schedule...")
    output_dir = Path("outputs")
    MissionScheduler.export_to_json(spacecraft_solution['schedule'], 
                                    output_dir / "spacecraft_schedule.json")
    MissionScheduler.export_to_csv(spacecraft_solution['schedule'],
                                   output_dir / "spacecraft_schedule.csv")
    print("   OK Schedule exported to JSON and CSV")
    
    # Generate spacecraft visualizations
    print("\n5. Generating spacecraft visualizations...")
    spacecraft_viz = SpacecraftVisualizer()
    spacecraft_viz.plot_schedule_gantt(spacecraft_solution['schedule'])
    spacecraft_viz.plot_activity_timeline(spacecraft_solution['schedule'])
    spacecraft_viz.plot_mission_statistics(value_metrics['schedule_stats'])
    spacecraft_viz.plot_target_coverage(spacecraft_solution, ground_targets)
    
    # ========================================================================
    # SUMMARY REPORT
    # ========================================================================
    
    print("\n" + "=" * 80)
    print(" " * 30 + "VALIDATION COMPLETE")
    print("=" * 80)
    
    print("\nAIRCRAFT MISSION RESULTS:")
    print(f"   • Success Rate (Monte-Carlo): {mc_results['success_rate']*100:.1f}%")
    print(f"   • Constraint Violations: {len(constraint_results['violations'])}")
    print(f"   • Mission Time: {performance_metrics['total_time_min']:.1f} min")
    print(f"   • Energy Consumption: {performance_metrics['total_energy_wh']:.1f} Wh")
    print(f"   • Distance Traveled: {performance_metrics['total_distance_km']:.2f} km")
    
    print("\nSPACECRAFT MISSION RESULTS:")
    print(f"   • Schedule Valid: {feasibility_results['schedule_valid']}")
    print(f"   • Total Science Value: {value_metrics['total_science_value']:.1f}")
    print(f"   • Observations: {value_metrics['num_observations']}")
    print(f"   • Downlinks: {value_metrics['num_downlinks']}")
    print(f"   • Schedule Utilization: {value_metrics['schedule_stats']['utilization_percent']:.1f}%")
    
    print("\nOUTPUT FILES GENERATED:")
    print("   outputs/")
    print("   ├── aircraft_flight_path.png")
    print("   ├── aircraft_altitude_profile.png")
    print("   ├── aircraft_performance.png")
    print("   ├── aircraft_monte_carlo.png")
    print("   ├── spacecraft_schedule_gantt.png")
    print("   ├── spacecraft_timeline.png")
    print("   ├── spacecraft_statistics.png")
    print("   ├── spacecraft_coverage.png")
    print("   ├── spacecraft_schedule.json")
    print("   ├── spacecraft_schedule.csv")
    print("   └── validation/")
    print("       ├── aircraft_monte_carlo.json")
    print("       ├── aircraft_constraint_checks.json")
    print("       ├── aircraft_performance_metrics.json")
    print("       ├── spacecraft_feasibility.json")
    print("       ├── spacecraft_value_metrics.json")
    print("       └── spacecraft_stress_tests.json")
    
    print("\nAll validation and visualization complete!")
    print("=" * 80 + "\n")
    
    # Create summary JSON
    summary = {
        'aircraft': {
            'monte_carlo_success_rate': mc_results['success_rate'],
            'constraint_violations': len(constraint_results['violations']),
            'mission_time_min': performance_metrics['total_time_min'],
            'energy_wh': performance_metrics['total_energy_wh'],
            'distance_km': performance_metrics['total_distance_km']
        },
        'spacecraft': {
            'schedule_valid': feasibility_results['schedule_valid'],
            'science_value': value_metrics['total_science_value'],
            'num_observations': value_metrics['num_observations'],
            'num_downlinks': value_metrics['num_downlinks'],
            'utilization_percent': value_metrics['schedule_stats']['utilization_percent']
        }
    }
    
    with open(output_dir / "summary_results.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary


if __name__ == "__main__":
    run_complete_pipeline()
