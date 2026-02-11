"""
Spacecraft mission validation and robustness testing.

This module implements schedule feasibility checks, mission value metrics,
and stress tests for spacecraft missions.
"""

import numpy as np
from typing import List, Dict, Any
import json
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spacecraft.orbit import OrbitalElements, GroundTarget, GroundStation
from src.spacecraft.planner import SpacecraftMissionPlanner
from src.spacecraft.scheduler import MissionScheduler


class SpacecraftValidator:
    """Validates spacecraft mission planning with robustness tests."""
    
    def __init__(self, output_dir: str = "outputs/validation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def schedule_feasibility_check(self, 
                                   scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check schedule feasibility (no overlaps, constraints satisfied).
        
        Returns:
            Dictionary with feasibility check results
        """
        print("\nRunning schedule feasibility checks...")
        
        planner = self._create_planner(scenario)
        solution = planner.solve()
        
        checks = {
            'schedule_valid': True,
            'num_activities': len(solution['schedule']),
            'overlaps': self._check_overlaps(solution['schedule']),
            'constraint_violations': [],
            'coverage_stats': self._compute_coverage(solution, scenario)
        }
        
        # Validate constraints
        is_valid, violations = planner.validate_solution(solution)
        checks['schedule_valid'] = is_valid
        checks['constraint_violations'] = violations
        
        # Save results
        with open(self.output_dir / 'spacecraft_feasibility.json', 'w') as f:
            json.dump(checks, f, indent=2, default=str)
        
        print(f"OK Schedule valid: {checks['schedule_valid']}")
        print(f"OK Total activities: {checks['num_activities']}")
        print(f"OK Overlaps found: {checks['overlaps']['count']}")
        print(f"OK Target coverage: {checks['coverage_stats']['targets_observed']}/{checks['coverage_stats']['total_targets']}")
        
        return checks
    
    def mission_value_metrics(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute mission value and science return metrics.
        
        Returns:
            Dictionary with mission value metrics
        """
        print("\nComputing mission value metrics...")
        
        planner = self._create_planner(scenario)
        solution = planner.solve()
        
        metrics = {
            'total_science_value': solution['mission_value'],
            'num_observations': solution['num_observations'],
            'num_downlinks': solution['num_downlinks'],
            'observations_per_day': solution['num_observations'] / scenario['mission_duration_days'],
            'downlinks_per_day': solution['num_downlinks'] / scenario['mission_duration_days'],
            'observation_efficiency': self._compute_efficiency(solution, planner),
            'schedule_stats': MissionScheduler.compute_statistics(solution['schedule'])
        }
        
        # Save metrics
        with open(self.output_dir / 'spacecraft_value_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        print(f"OK Total science value: {metrics['total_science_value']:.1f}")
        print(f"OK Observations: {metrics['num_observations']}")
        print(f"OK Downlinks: {metrics['num_downlinks']}")
        print(f"OK Utilization: {metrics['schedule_stats']['utilization_percent']:.1f}%")
        
        return metrics
    
    def stress_test_scenarios(self, base_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run stress tests with harder scenarios.
        
        Returns:
            Dictionary with stress test results
        """
        print("\nRunning stress test scenarios...")
        
        stress_tests = {
            'baseline': self._run_scenario(base_scenario, "Baseline"),
            'high_priority_targets': self._run_high_priority_test(base_scenario),
            'limited_ground_stations': self._run_limited_stations_test(base_scenario),
            'short_mission': self._run_short_mission_test(base_scenario)
        }
        
        # Save results
        with open(self.output_dir / 'spacecraft_stress_tests.json', 'w') as f:
            json.dump(stress_tests, f, indent=2, default=str)
        
        print("\nStress Test Summary:")
        for test_name, result in stress_tests.items():
            print(f"  {test_name}: {result['num_observations']} obs, value={result['mission_value']:.1f}")
        
        return stress_tests
    
    def _create_planner(self, scenario: Dict[str, Any]) -> SpacecraftMissionPlanner:
        """Create spacecraft planner from scenario."""
        return SpacecraftMissionPlanner(
            name=scenario.get('name', 'Validation_Mission'),
            orbital_elements=scenario['orbital_elements'],
            ground_targets=scenario['ground_targets'],
            ground_stations=scenario['ground_stations'],
            mission_duration_days=scenario.get('mission_duration_days', 7)
        )
    
    def _check_overlaps(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for overlapping activities in schedule."""
        overlaps = []
        
        for i in range(len(schedule)):
            for j in range(i + 1, len(schedule)):
                act1 = schedule[i]
                act2 = schedule[j]
                
                # Check if time ranges overlap
                if (act1['start_time'] < act2['end_time'] and 
                    act2['start_time'] < act1['end_time']):
                    overlaps.append({
                        'activity_1': i,
                        'activity_2': j,
                        'type_1': act1['type'],
                        'type_2': act2['type']
                    })
        
        return {
            'count': len(overlaps),
            'overlaps': overlaps
        }
    
    def _compute_coverage(self, solution: Dict[str, Any], 
                         scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Compute target coverage statistics."""
        observed_targets = set()
        
        for activity in solution['schedule']:
            if activity['type'] == 'observation':
                observed_targets.add(activity['target_id'])
        
        return {
            'targets_observed': len(observed_targets),
            'total_targets': len(scenario['ground_targets']),
            'coverage_percent': (len(observed_targets) / len(scenario['ground_targets'])) * 100
        }
    
    def _compute_efficiency(self, solution: Dict[str, Any], 
                           planner: SpacecraftMissionPlanner) -> Dict[str, Any]:
        """Compute observation efficiency metrics."""
        total_windows = sum(len(windows) for windows in planner.target_windows.values())
        
        return {
            'total_visibility_windows': total_windows,
            'observations_scheduled': solution['num_observations'],
            'window_utilization_percent': (solution['num_observations'] / total_windows * 100) if total_windows > 0 else 0
        }
    
    def _run_scenario(self, scenario: Dict[str, Any], name: str) -> Dict[str, Any]:
        """Run a single scenario and return results."""
        scenario['name'] = name
        planner = self._create_planner(scenario)
        solution = planner.solve()
        
        return {
            'name': name,
            'mission_value': solution['mission_value'],
            'num_observations': solution['num_observations'],
            'num_downlinks': solution['num_downlinks']
        }
    
    def _run_high_priority_test(self, base_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test with high-priority targets."""
        scenario = base_scenario.copy()
        
        # Double the priority of all targets
        high_priority_targets = []
        for target in base_scenario['ground_targets']:
            new_target = GroundTarget(
                name=target.name,
                latitude=target.latitude,
                longitude=target.longitude,
                priority=target.priority * 2.0,
                min_elevation=target.min_elevation
            )
            high_priority_targets.append(new_target)
        
        scenario['ground_targets'] = high_priority_targets
        return self._run_scenario(scenario, "High Priority Targets")
    
    def _run_limited_stations_test(self, base_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test with limited ground stations."""
        scenario = base_scenario.copy()
        scenario['ground_stations'] = base_scenario['ground_stations'][:1]  # Only one station
        return self._run_scenario(scenario, "Limited Ground Stations")
    
    def _run_short_mission_test(self, base_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test with shorter mission duration."""
        scenario = base_scenario.copy()
        scenario['mission_duration_days'] = 3  # 3 days instead of 7
        return self._run_scenario(scenario, "Short Mission (3 days)")


def run_spacecraft_validation():
    """Run complete spacecraft validation suite."""
    print("=" * 70)
    print("SPACECRAFT VALIDATION SUITE")
    print("=" * 70)
    
    # Define test scenario
    epoch = datetime(2026, 2, 11, 0, 0, 0)
    scenario = {
        'orbital_elements': OrbitalElements(
            semi_major_axis=6371.0 + 550.0,
            eccentricity=0.001,
            inclination=np.radians(97.4),
            raan=np.radians(0.0),
            arg_periapsis=np.radians(0.0),
            true_anomaly=np.radians(0.0),
            epoch=epoch
        ),
        'ground_targets': [
            GroundTarget("Target_1", 37.7749, -122.4194, priority=10.0),
            GroundTarget("Target_2", 40.7128, -74.0060, priority=8.0),
            GroundTarget("Target_3", 51.5074, -0.1278, priority=9.0),
            GroundTarget("Target_4", 35.6762, 139.6503, priority=7.0),
            GroundTarget("Target_5", -33.8688, 151.2093, priority=6.0),
        ],
        'ground_stations': [
            GroundStation("GS_Alaska", 64.8378, -147.7164),
            GroundStation("GS_Hawaii", 19.8968, -155.5828),
            GroundStation("GS_Norway", 69.6492, 18.9553),
        ],
        'mission_duration_days': 7
    }
    
    validator = SpacecraftValidator()
    
    # Run tests
    feasibility_results = validator.schedule_feasibility_check(scenario)
    value_results = validator.mission_value_metrics(scenario)
    stress_results = validator.stress_test_scenarios(scenario)
    
    print("\n" + "=" * 70)
    print("SPACECRAFT VALIDATION COMPLETE")
    print("=" * 70)
    print(f"OK Schedule valid: {feasibility_results['schedule_valid']}")
    print(f"OK Mission value: {value_results['total_science_value']:.1f}")
    print(f"OK Stress tests completed: {len(stress_results)}")
    print(f"OK Results saved to outputs/validation/")
    
    return {
        'feasibility': feasibility_results,
        'value_metrics': value_results,
        'stress_tests': stress_results
    }


if __name__ == "__main__":
    run_spacecraft_validation()
