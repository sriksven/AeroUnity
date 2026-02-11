"""
Aircraft mission planner using unified planning framework.

This module implements the AircraftMissionPlanner which extends the base
MissionPlanner to handle UAV/fixed-wing route planning with constraints.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from ..core.planner_base import MissionPlanner
from ..core.objectives import MinimizeTimeObjective, MinimizeEnergyObjective
from .models import AircraftParams, AircraftState, WindModel, FlightDynamics
from .constraints import (AircraftGeofenceConstraint, AltitudeConstraint,
                         TurnRateConstraint, EnergyConstraint)


class AircraftMissionPlanner(MissionPlanner):
    """
    Aircraft mission planner using OR-Tools routing solver.
    
    This planner finds optimal routes through waypoints while respecting
    wind, energy, maneuver, and geofencing constraints.
    """
    
    def __init__(self, name: str, aircraft_params: AircraftParams,
                 wind_model: WindModel, waypoints: List[np.ndarray],
                 no_fly_zones: List[Any] = None):
        """
        Args:
            name: Mission name
            aircraft_params: Aircraft physical parameters
            wind_model: Wind model for simulation
            waypoints: List of waypoints to visit [x, y, altitude]
            no_fly_zones: List of Shapely Polygon objects for no-fly zones
        """
        super().__init__(name)
        
        self.aircraft_params = aircraft_params
        self.wind_model = wind_model
        self.waypoints = waypoints
        self.no_fly_zones = no_fly_zones or []
        self.flight_dynamics = FlightDynamics(aircraft_params, wind_model)
        
        # Define planning components
        self.define_decision_variables()
        self.define_constraints()
        self.define_objectives()
        
    def define_decision_variables(self) -> List[Any]:
        """
        Decision variables: order of waypoints to visit.
        
        For aircraft routing, the main decision is the sequence of waypoints.
        """
        # In OR-Tools routing, decision variables are implicit (route indices)
        return []
    
    def define_constraints(self) -> List[Any]:
        """Define aircraft-specific constraints."""
        constraints = []
        
        # Geofencing constraint
        if self.no_fly_zones:
            constraints.append(AircraftGeofenceConstraint(
                name="geofence",
                no_fly_polygons=self.no_fly_zones,
                constraint_type='hard'
            ))
        
        # Altitude constraints (example: 50m to 500m)
        constraints.append(AltitudeConstraint(
            name="altitude_limits",
            min_altitude=50.0,
            max_altitude=500.0,
            constraint_type='hard'
        ))
        
        # Turn rate constraint
        constraints.append(TurnRateConstraint(
            name="turn_rate",
            max_turn_rate=self.aircraft_params.max_turn_rate,
            cruise_speed=self.aircraft_params.max_speed * 0.8,
            constraint_type='hard'
        ))
        
        # Energy constraint
        constraints.append(EnergyConstraint(
            name="energy_budget",
            initial_energy=self.aircraft_params.battery_capacity,
            min_reserve=self.aircraft_params.battery_capacity * 0.1,
            constraint_type='hard'
        ))
        
        self.constraints = constraints
        return constraints
    
    def define_objectives(self) -> List[Any]:
        """Define optimization objectives."""
        objectives = [
            MinimizeTimeObjective(name="minimize_mission_time")
        ]
        
        self.objectives = objectives
        return objectives
    
    def compute_distance_matrix(self) -> np.ndarray:
        """
        Compute Euclidean distance matrix between all waypoints.
        
        Returns:
            Distance matrix [n_waypoints x n_waypoints]
        """
        n = len(self.waypoints)
        dist_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    diff = self.waypoints[i] - self.waypoints[j]
                    dist_matrix[i, j] = np.linalg.norm(diff)
                    
        return dist_matrix
    
    def solve(self) -> Dict[str, Any]:
        """
        Solve the aircraft routing problem using OR-Tools.
        
        Returns:
            Solution dictionary with route, times, and metrics
        """
        # Create routing model
        manager = pywrapcp.RoutingIndexManager(
            len(self.waypoints),  # number of locations
            1,  # number of vehicles (aircraft)
            0   # depot (start location)
        )
        
        routing = pywrapcp.RoutingModel(manager)
        
        # Compute distance matrix (in meters)
        dist_matrix = self.compute_distance_matrix()
        
        # Convert to integer for OR-Tools (use cm for precision)
        dist_matrix_int = (dist_matrix * 100).astype(int)
        
        def distance_callback(from_index, to_index):
            """Return distance between two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return dist_matrix_int[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = 10
        
        # Solve
        assignment = routing.SolveWithParameters(search_parameters)
        
        if assignment:
            # Extract solution
            route = []
            index = routing.Start(0)
            
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route.append(node)
                index = assignment.Value(routing.NextVar(index))
                
            # Add final node
            route.append(manager.IndexToNode(index))
            
            # Build solution with actual waypoints
            path = [self.waypoints[i] for i in route]
            
            # Simulate to get times and energy
            times, energy = self.simulate_path(path)
            
            solution = {
                'route_indices': route,
                'path': path,
                'times': times,
                'total_time': times[-1] if times else 0.0,
                'total_energy': energy,
                'distance': assignment.ObjectiveValue() / 100.0,  # Convert back to meters
            }
            
            self.solution = solution
            return solution
        else:
            # No solution found
            return {
                'route_indices': [],
                'path': [],
                'times': [],
                'total_time': 0.0,
                'total_energy': 0.0,
                'distance': 0.0,
            }
    
    def simulate_path(self, path: List[np.ndarray]) -> Tuple[List[float], float]:
        """
        Simulate flight along a path to compute times and energy.
        
        Args:
            path: List of waypoints
            
        Returns:
            (times, total_energy)
        """
        if len(path) < 2:
            return [0.0], 0.0
            
        # Initialize state at first waypoint
        state = AircraftState(
            time=0.0,
            position=path[0],
            velocity=np.array([self.aircraft_params.max_speed * 0.8, 0.0, 0.0]),
            heading=0.0,
            energy_remaining=self.aircraft_params.battery_capacity
        )
        
        times = [0.0]
        total_energy = 0.0
        
        # Simulate each segment
        for i in range(len(path) - 1):
            start = path[i]
            end = path[i + 1]
            
            # Compute segment
            segment_time, segment_energy = self.simulate_segment(state, start, end)
            
            state.time += segment_time
            state.position = end
            state.energy_remaining -= segment_energy
            
            times.append(state.time)
            total_energy += segment_energy
            
        return times, total_energy
    
    def simulate_segment(self, state: AircraftState, 
                        start: np.ndarray, end: np.ndarray) -> Tuple[float, float]:
        """
        Simulate a single segment between two waypoints.
        
        Returns:
            (segment_time, segment_energy)
        """
        distance = np.linalg.norm(end - start)
        cruise_speed = self.aircraft_params.max_speed * 0.8
        
        # Simple estimate: time = distance / speed
        segment_time = distance / cruise_speed
        
        # Energy estimate: power * time
        avg_power = self.aircraft_params.power_consumption_base
        segment_energy = avg_power * segment_time
        
        return segment_time, segment_energy
