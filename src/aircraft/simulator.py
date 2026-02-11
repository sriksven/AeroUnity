"""
Aircraft flight simulator.

This module simulates aircraft flight along planned routes, validating
constraints and computing detailed trajectories.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from .models import AircraftState, AircraftParams, WindModel, FlightDynamics


class FlightSimulator:
    """Simulates aircraft flight with detailed physics."""
    
    def __init__(self, aircraft_params: AircraftParams, wind_model: WindModel):
        self.params = aircraft_params
        self.wind_model = wind_model
        self.dynamics = FlightDynamics(aircraft_params, wind_model)
        
    def simulate_mission(self, waypoints: List[np.ndarray], 
                        dt: float = 1.0) -> Dict[str, Any]:
        """
        Simulate complete mission through waypoints.
        
        Args:
            waypoints: List of waypoints [x, y, altitude]
            dt: Time step for simulation (seconds)
            
        Returns:
            Dictionary with trajectory, states, and metrics
        """
        if len(waypoints) < 2:
            return {
                'trajectory': [],
                'states': [],
                'times': [],
                'total_time': 0.0,
                'total_energy': 0.0,
                'constraint_violations': []
            }
        
        # Initialize at first waypoint
        initial_state = AircraftState(
            time=0.0,
            position=waypoints[0].copy(),
            velocity=np.array([self.params.max_speed * 0.8, 0.0, 0.0]),
            heading=0.0,
            energy_remaining=self.params.battery_capacity
        )
        
        all_states = [initial_state]
        trajectory = [initial_state.position.copy()]
        times = [0.0]
        
        # Simulate each segment
        current_state = initial_state
        
        for i in range(len(waypoints) - 1):
            target = waypoints[i + 1]
            
            # Simulate segment to target
            segment_states = self.simulate_to_target(current_state, target, dt)
            
            if segment_states:
                all_states.extend(segment_states)
                trajectory.extend([s.position.copy() for s in segment_states])
                times.extend([s.time for s in segment_states])
                current_state = segment_states[-1]
        
        # Compute metrics
        total_time = current_state.time
        total_energy = (self.params.battery_capacity - 
                       current_state.energy_remaining)
        
        # Check for constraint violations
        violations = self.check_violations(all_states)
        
        return {
            'trajectory': trajectory,
            'states': all_states,
            'times': times,
            'total_time': total_time,
            'total_energy': total_energy,
            'constraint_violations': violations,
            'energy_remaining': current_state.energy_remaining
        }
    
    def simulate_to_target(self, initial_state: AircraftState,
                          target: np.ndarray, dt: float) -> List[AircraftState]:
        """
        Simulate flight from current state to target waypoint.
        
        Args:
            initial_state: Starting state
            target: Target position [x, y, altitude]
            dt: Time step
            
        Returns:
            List of states along the path
        """
        states = []
        current_state = initial_state
        
        max_iterations = 10000  # Safety limit
        tolerance = 5.0  # meters
        
        for _ in range(max_iterations):
            # Compute direction to target
            delta = target - current_state.position
            distance = np.linalg.norm(delta)
            
            if distance < tolerance:
                break
            
            # Compute desired velocity
            direction = delta / distance
            speed = min(self.params.max_speed * 0.8, distance / dt)
            desired_velocity = direction * speed
            
            # Limit climb/descent rate
            desired_velocity[2] = np.clip(
                desired_velocity[2],
                -self.params.max_descent_rate,
                self.params.max_climb_rate
            )
            
            # Propagate dynamics
            next_state = self.dynamics.propagate(
                current_state, desired_velocity, dt
            )
            
            states.append(next_state)
            current_state = next_state
            
            # Check if we've run out of energy
            if current_state.energy_remaining <= 0:
                break
        
        return states
    
    def check_violations(self, states: List[AircraftState]) -> List[str]:
        """
        Check for constraint violations in trajectory.
        
        Returns:
            List of violation descriptions
        """
        violations = []
        
        for i, state in enumerate(states):
            # Check energy
            if state.energy_remaining < 0:
                violations.append(f"Energy depleted at t={state.time:.1f}s")
                break
            
            # Check speed limits
            speed = np.linalg.norm(state.velocity)
            if speed > self.params.max_speed:
                violations.append(
                    f"Speed limit exceeded at t={state.time:.1f}s: "
                    f"{speed:.1f} > {self.params.max_speed:.1f} m/s"
                )
            
            # Check climb rate
            if abs(state.velocity[2]) > self.params.max_climb_rate:
                violations.append(
                    f"Climb rate exceeded at t={state.time:.1f}s: "
                    f"{abs(state.velocity[2]):.1f} > {self.params.max_climb_rate:.1f} m/s"
                )
        
        return violations
