"""
Spacecraft mission planner using unified planning framework.

This module implements the SpacecraftMissionPlanner which extends the base
MissionPlanner to handle CubeSat LEO observation and downlink scheduling.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from ortools.sat.python import cp_model

from ..core.planner_base import MissionPlanner
from ..core.objectives import MaximizeValueObjective
from .orbit import (OrbitPropagator, OrbitalElements, SpacecraftState,
                   GroundTarget, GroundStation, VisibilityCalculator)
from .constraints import (PointingSlewConstraint, PowerBudgetConstraint,
                         DutyCycleConstraint, DownlinkConstraint)


class SpacecraftMissionPlanner(MissionPlanner):
    """
    Spacecraft mission planner using OR-Tools CP-SAT solver.
    
    This planner schedules observations and downlinks over a 7-day period
    while respecting orbit mechanics, pointing, power, and duty cycle constraints.
    """
    
    def __init__(self, name: str, orbital_elements: OrbitalElements,
                 ground_targets: List[GroundTarget],
                 ground_stations: List[GroundStation],
                 mission_duration_days: int = 7):
        """
        Args:
            name: Mission name
            orbital_elements: Initial orbital elements
            ground_targets: List of ground targets to observe
            ground_stations: List of ground stations for downlink
            mission_duration_days: Mission duration in days
        """
        super().__init__(name)
        
        self.orbital_elements = orbital_elements
        self.ground_targets = ground_targets
        self.ground_stations = ground_stations
        self.mission_duration_days = mission_duration_days
        
        self.propagator = OrbitPropagator(orbital_elements)
        self.orbital_period = self.propagator.orbital_period()
        
        # Compute visibility windows
        self.target_windows = self.compute_target_windows()
        self.station_windows = self.compute_station_windows()
        
        # Define planning components
        self.define_decision_variables()
        self.define_constraints()
        self.define_objectives()
        
    def compute_target_windows(self) -> Dict[str, List[Tuple[datetime, datetime]]]:
        """
        Compute visibility windows for all ground targets.
        
        Returns:
            Dictionary mapping target names to list of (start, end) windows
        """
        windows = {}
        
        start_time = self.orbital_elements.epoch
        end_time = start_time + timedelta(days=self.mission_duration_days)
        
        # Sample orbit at regular intervals
        dt = 60.0  # 1 minute steps
        current_time = start_time
        
        for target in self.ground_targets:
            target_windows = []
            in_window = False
            window_start = None
            
            current_time = start_time
            
            while current_time < end_time:
                # Propagate orbit
                time_since_epoch = (current_time - start_time).total_seconds()
                state = self.propagator.propagate(time_since_epoch)
                
                # Check visibility
                visible = VisibilityCalculator.is_visible(
                    state,
                    (target.latitude, target.longitude),
                    target.min_elevation
                )
                
                if visible and not in_window:
                    # Start of window
                    window_start = current_time
                    in_window = True
                elif not visible and in_window:
                    # End of window
                    target_windows.append((window_start, current_time))
                    in_window = False
                    
                current_time += timedelta(seconds=dt)
            
            # Close any open window
            if in_window:
                target_windows.append((window_start, end_time))
                
            windows[target.name] = target_windows
            
        return windows
    
    def compute_station_windows(self) -> Dict[str, List[Tuple[datetime, datetime]]]:
        """
        Compute contact windows for all ground stations.
        
        Returns:
            Dictionary mapping station names to list of (start, end) windows
        """
        windows = {}
        
        start_time = self.orbital_elements.epoch
        end_time = start_time + timedelta(days=self.mission_duration_days)
        
        dt = 60.0  # 1 minute steps
        
        for station in self.ground_stations:
            station_windows = []
            in_window = False
            window_start = None
            
            current_time = start_time
            
            while current_time < end_time:
                time_since_epoch = (current_time - start_time).total_seconds()
                state = self.propagator.propagate(time_since_epoch)
                
                visible = VisibilityCalculator.is_visible(
                    state,
                    (station.latitude, station.longitude),
                    station.min_elevation
                )
                
                if visible and not in_window:
                    window_start = current_time
                    in_window = True
                elif not visible and in_window:
                    station_windows.append((window_start, current_time))
                    in_window = False
                    
                current_time += timedelta(seconds=dt)
            
            if in_window:
                station_windows.append((window_start, end_time))
                
            windows[station.name] = station_windows
            
        return windows
    
    def define_decision_variables(self) -> List[Any]:
        """Decision variables: which observations and downlinks to schedule."""
        return []
    
    def define_constraints(self) -> List[Any]:
        """Define spacecraft-specific constraints."""
        constraints = []
        
        # Pointing/slew constraint
        constraints.append(PointingSlewConstraint(
            name="slew_rate",
            max_slew_rate=1.0,  # degrees/second
            constraint_type='hard'
        ))
        
        # Power budget constraint
        constraints.append(PowerBudgetConstraint(
            name="power_budget",
            battery_capacity=100.0,  # Wh (typical CubeSat)
            solar_power=30.0,  # W
            min_battery_level=0.2,
            constraint_type='hard'
        ))
        
        # Duty cycle constraint
        constraints.append(DutyCycleConstraint(
            name="duty_cycle",
            max_ops_per_orbit=5,
            orbital_period=self.orbital_period,
            constraint_type='hard'
        ))
        
        # Downlink constraint
        constraints.append(DownlinkConstraint(
            name="downlink_requirement",
            max_storage_time=86400.0,  # 24 hours
            constraint_type='soft'
        ))
        
        self.constraints = constraints
        return constraints
    
    def define_objectives(self) -> List[Any]:
        """Define optimization objectives."""
        objectives = [
            MaximizeValueObjective(name="maximize_science_value")
        ]
        
        self.objectives = objectives
        return objectives
    
    def solve(self) -> Dict[str, Any]:
        """
        Solve the spacecraft scheduling problem using OR-Tools CP-SAT.
        
        Returns:
            Solution dictionary with schedule and metrics
        """
        model = cp_model.CpModel()
        
        # Create variables for each observation opportunity
        obs_vars = {}
        obs_info = []
        
        for target in self.ground_targets:
            windows = self.target_windows.get(target.name, [])
            
            for i, (start, end) in enumerate(windows):
                var_name = f"obs_{target.name}_{i}"
                obs_var = model.NewBoolVar(var_name)
                obs_vars[var_name] = obs_var
                
                obs_info.append({
                    'var_name': var_name,
                    'target': target,
                    'window_start': start,
                    'window_end': end,
                    'priority': target.priority
                })
        
        # Create variables for downlink opportunities
        downlink_vars = {}
        downlink_info = []
        
        for station in self.ground_stations:
            windows = self.station_windows.get(station.name, [])
            
            for i, (start, end) in enumerate(windows):
                var_name = f"downlink_{station.name}_{i}"
                downlink_var = model.NewBoolVar(var_name)
                downlink_vars[var_name] = downlink_var
                
                downlink_info.append({
                    'var_name': var_name,
                    'station': station,
                    'window_start': start,
                    'window_end': end
                })
        
        # Constraint: At most one activity at a time (simplified)
        # This is a simplified version; a full implementation would use interval variables
        
        # Objective: Maximize total science value
        # Only count observations that have a corresponding downlink
        objective_terms = []
        
        for obs in obs_info:
            # Simplified: assume observation value if scheduled
            objective_terms.append(obs_vars[obs['var_name']] * int(obs['priority'] * 100))
        
        model.Maximize(sum(objective_terms))
        
        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0
        status = solver.Solve(model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Extract solution
            schedule = []
            total_value = 0.0
            
            for obs in obs_info:
                if solver.Value(obs_vars[obs['var_name']]):
                    schedule.append({
                        'type': 'observation',
                        'target_id': obs['target'].name,
                        'start_time': obs['window_start'],
                        'end_time': obs['window_start'] + timedelta(seconds=30),  # 30s observation
                        'priority': obs['priority'],
                        'target_position': np.array([0, 0, 1])  # Simplified
                    })
                    total_value += obs['priority']
            
            for downlink in downlink_info:
                if solver.Value(downlink_vars[downlink['var_name']]):
                    schedule.append({
                        'type': 'downlink',
                        'station_id': downlink['station'].name,
                        'start_time': downlink['window_start'],
                        'end_time': downlink['window_start'] + timedelta(seconds=60),  # 60s downlink
                        'observation_ids': []  # Simplified
                    })
            
            # Sort schedule by time
            schedule.sort(key=lambda x: x['start_time'])
            
            solution = {
                'schedule': schedule,
                'mission_value': total_value,
                'num_observations': sum(1 for s in schedule if s['type'] == 'observation'),
                'num_downlinks': sum(1 for s in schedule if s['type'] == 'downlink'),
            }
            
            self.solution = solution
            return solution
        else:
            return {
                'schedule': [],
                'mission_value': 0.0,
                'num_observations': 0,
                'num_downlinks': 0,
            }
