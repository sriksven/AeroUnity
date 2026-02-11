"""
Aircraft mission validation and robustness testing.

This module implements Monte-Carlo wind uncertainty tests, constraint
violation checks, and performance metrics for aircraft missions.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
import json
from pathlib import Path
import matplotlib.pyplot as plt
from shapely.geometry import Polygon


def convert_to_json_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    return obj

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aircraft.models import AircraftParams, WindModel
from src.aircraft.planner import AircraftMissionPlanner
from src.aircraft.simulator import FlightSimulator


class AircraftValidator:
    """Validates aircraft mission planning with robustness tests."""
    
    def __init__(self, output_dir: str = "outputs/validation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def monte_carlo_wind_test(self, 
                              base_scenario: Dict[str, Any],
                              num_trials: int = 100) -> Dict[str, Any]:
        """
        Run Monte-Carlo simulation with varying wind conditions.
        
        Args:
            base_scenario: Base mission scenario configuration
            num_trials: Number of Monte-Carlo trials
            
        Returns:
            Dictionary with test results and statistics
        """
        print(f"\nRunning Monte-Carlo wind uncertainty test ({num_trials} trials)...")
        
        results = {
            'trials': [],
            'success_count': 0,
            'failure_count': 0,
            'times': [],
            'energies': [],
            'distances': []
        }
        
        aircraft_params = base_scenario['aircraft_params']
        waypoints = base_scenario['waypoints']
        no_fly_zones = base_scenario.get('no_fly_zones', [])
        base_wind = base_scenario.get('base_wind', np.array([3.0, 2.0, 0.0]))
        
        for trial in range(num_trials):
            # Generate random wind variation
            wind_variation = np.random.randn(2) * 2.0  # ±2 m/s variation
            trial_wind = base_wind.copy()
            trial_wind[:2] += wind_variation
            
            # Create wind model for this trial
            wind_model = WindModel(
                wind_type='constant',
                base_wind=trial_wind,
                seed=trial
            )
            
            # Create planner
            planner = AircraftMissionPlanner(
                name=f"Trial_{trial}",
                aircraft_params=aircraft_params,
                wind_model=wind_model,
                waypoints=waypoints,
                no_fly_zones=no_fly_zones
            )
            
            # Solve
            solution = planner.solve()
            
            # Validate
            is_valid, violations = planner.validate_solution(solution)
            
            trial_result = {
                'trial': trial,
                'wind': trial_wind.tolist(),
                'success': is_valid,
                'total_time': solution['total_time'],
                'total_energy': solution['total_energy'],
                'distance': solution['distance'],
                'violations': violations
            }
            
            results['trials'].append(trial_result)
            
            if is_valid:
                results['success_count'] += 1
                results['times'].append(solution['total_time'])
                results['energies'].append(solution['total_energy'])
                results['distances'].append(solution['distance'])
            else:
                results['failure_count'] += 1
        
        # Compute statistics
        results['success_rate'] = results['success_count'] / num_trials
        
        if results['times']:
            results['time_stats'] = {
                'mean': np.mean(results['times']),
                'std': np.std(results['times']),
                'min': np.min(results['times']),
                'max': np.max(results['times'])
            }
            results['energy_stats'] = {
                'mean': np.mean(results['energies']),
                'std': np.std(results['energies']),
                'min': np.min(results['energies']),
                'max': np.max(results['energies'])
            }
        
        # Save results
        with open(self.output_dir / 'aircraft_monte_carlo.json', 'w') as f:
            json.dump(convert_to_json_serializable(results), f, indent=2)
        
        print(f"✓ Success rate: {results['success_rate']*100:.1f}%")
        print(f"✓ Mean time: {results['time_stats']['mean']:.1f} ± {results['time_stats']['std']:.1f} s")
        print(f"✓ Mean energy: {results['energy_stats']['mean']:.1f} ± {results['energy_stats']['std']:.1f} J")
        
        return results
    
    def constraint_violation_check(self, 
                                   scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detailed constraint violation checking.
        
        Returns:
            Dictionary with constraint check results
        """
        print("\nRunning detailed constraint violation checks...")
        
        aircraft_params = scenario['aircraft_params']
        waypoints = scenario['waypoints']
        no_fly_zones = scenario.get('no_fly_zones', [])
        wind_model = WindModel(
            wind_type='constant',
            base_wind=scenario.get('base_wind', np.array([3.0, 2.0, 0.0])),
            seed=42
        )
        
        planner = AircraftMissionPlanner(
            name="Constraint_Check",
            aircraft_params=aircraft_params,
            wind_model=wind_model,
            waypoints=waypoints,
            no_fly_zones=no_fly_zones
        )
        
        solution = planner.solve()
        is_valid, violations = planner.validate_solution(solution)
        
        # Detailed checks
        checks = {
            'overall_valid': is_valid,
            'violations': violations,
            'geofence_check': self._check_geofence(solution['path'], no_fly_zones),
            'energy_check': self._check_energy(solution, aircraft_params),
            'path_continuity': self._check_path_continuity(solution['path'])
        }
        
        # Save results
        with open(self.output_dir / 'aircraft_constraint_checks.json', 'w') as f:
            json.dump(convert_to_json_serializable(checks), f, indent=2)
        
        print(f"✓ Overall valid: {checks['overall_valid']}")
        print(f"✓ Geofence violations: {checks['geofence_check']['violations']}")
        print(f"✓ Energy remaining: {checks['energy_check']['remaining_percent']:.1f}%")
        
        return checks
    
    def _check_geofence(self, path: List[np.ndarray], 
                       no_fly_zones: List[Polygon]) -> Dict[str, Any]:
        """Check if path violates any geofences."""
        from shapely.geometry import Point
        
        violations = 0
        violation_points = []
        
        for i, waypoint in enumerate(path):
            point = Point(waypoint[0], waypoint[1])
            
            for zone in no_fly_zones:
                if zone.contains(point):
                    violations += 1
                    violation_points.append(i)
                    break
        
        return {
            'violations': violations,
            'violation_indices': violation_points,
            'total_waypoints': len(path)
        }
    
    def _check_energy(self, solution: Dict[str, Any], 
                     params: AircraftParams) -> Dict[str, Any]:
        """Check energy consumption."""
        total_energy = solution['total_energy']
        capacity = params.battery_capacity
        remaining = capacity - total_energy
        
        return {
            'consumed': total_energy,
            'capacity': capacity,
            'remaining': remaining,
            'remaining_percent': (remaining / capacity) * 100
        }
    
    def _check_path_continuity(self, path: List[np.ndarray]) -> Dict[str, Any]:
        """Check if path is continuous (no jumps)."""
        max_segment_length = 0.0
        
        for i in range(len(path) - 1):
            segment_length = np.linalg.norm(path[i+1] - path[i])
            max_segment_length = max(max_segment_length, segment_length)
        
        return {
            'max_segment_length': max_segment_length,
            'continuous': max_segment_length < 10000.0  # 10km threshold
        }
    
    def performance_metrics(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute comprehensive performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        print("\nComputing performance metrics...")
        
        aircraft_params = scenario['aircraft_params']
        waypoints = scenario['waypoints']
        wind_model = WindModel(
            wind_type='constant',
            base_wind=scenario.get('base_wind', np.array([3.0, 2.0, 0.0])),
            seed=42
        )
        
        planner = AircraftMissionPlanner(
            name="Performance_Test",
            aircraft_params=aircraft_params,
            wind_model=wind_model,
            waypoints=waypoints,
            no_fly_zones=scenario.get('no_fly_zones', [])
        )
        
        solution = planner.solve()
        
        # Compute metrics
        metrics = {
            'total_time_s': solution['total_time'],
            'total_time_min': solution['total_time'] / 60.0,
            'total_distance_m': solution['distance'],
            'total_distance_km': solution['distance'] / 1000.0,
            'total_energy_j': solution['total_energy'],
            'total_energy_wh': solution['total_energy'] / 3600.0,
            'avg_speed_ms': solution['distance'] / solution['total_time'] if solution['total_time'] > 0 else 0,
            'energy_efficiency_j_per_m': solution['total_energy'] / solution['distance'] if solution['distance'] > 0 else 0,
            'waypoints_visited': len(solution['route_indices'])
        }
        
        # Save metrics
        with open(self.output_dir / 'aircraft_performance_metrics.json', 'w') as f:
            json.dump(convert_to_json_serializable(metrics), f, indent=2)
        
        print(f"✓ Mission time: {metrics['total_time_min']:.1f} min")
        print(f"✓ Distance: {metrics['total_distance_km']:.2f} km")
        print(f"✓ Energy: {metrics['total_energy_wh']:.1f} Wh")
        print(f"✓ Avg speed: {metrics['avg_speed_ms']:.1f} m/s")
        
        return metrics


def run_aircraft_validation():
    """Run complete aircraft validation suite."""
    print("=" * 70)
    print("AIRCRAFT VALIDATION SUITE")
    print("=" * 70)
    
    # Define test scenario
    scenario = {
        'aircraft_params': AircraftParams(
            max_speed=25.0,
            min_speed=10.0,
            max_climb_rate=3.0,
            max_bank_angle=np.radians(45),
            max_turn_rate=np.radians(30),
            battery_capacity=500.0 * 3600
        ),
        'waypoints': [
            np.array([0.0, 0.0, 100.0]),
            np.array([1000.0, 500.0, 150.0]),
            np.array([2000.0, 1500.0, 200.0]),
            np.array([3000.0, 1000.0, 150.0]),
            np.array([4000.0, 0.0, 100.0]),
            np.array([5000.0, 500.0, 100.0]),
        ],
        'no_fly_zones': [
            Polygon([(1500, 800), (1800, 800), (1800, 1200), (1500, 1200)]),
            Polygon([(3500, 200), (3800, 200), (3800, 600), (3500, 600)])
        ],
        'base_wind': np.array([3.0, 2.0, 0.0])
    }
    
    validator = AircraftValidator()
    
    # Run tests
    mc_results = validator.monte_carlo_wind_test(scenario, num_trials=100)
    constraint_results = validator.constraint_violation_check(scenario)
    performance_results = validator.performance_metrics(scenario)
    
    print("\n" + "=" * 70)
    print("AIRCRAFT VALIDATION COMPLETE")
    print("=" * 70)
    print(f"✓ Monte-Carlo success rate: {mc_results['success_rate']*100:.1f}%")
    print(f"✓ Constraint violations: {len(constraint_results['violations'])}")
    print(f"✓ Results saved to outputs/validation/")
    
    return {
        'monte_carlo': mc_results,
        'constraints': constraint_results,
        'performance': performance_results
    }


if __name__ == "__main__":
    run_aircraft_validation()
