"""
Aircraft flight dynamics and environmental models.

This module implements kinematic/point-mass flight models, wind models,
and energy consumption models for UAV/fixed-wing aircraft.
"""

import numpy as np
from typing import Tuple, Optional, Callable
from dataclasses import dataclass


@dataclass
class AircraftState:
    """Represents the state of an aircraft at a point in time."""
    time: float  # seconds
    position: np.ndarray  # [x, y, altitude] in meters
    velocity: np.ndarray  # [vx, vy, vz] in m/s
    heading: float  # radians
    energy_remaining: float  # Joules or battery percentage


@dataclass
class AircraftParams:
    """Physical parameters of the aircraft."""
    max_speed: float = 25.0  # m/s (typical UAV cruise speed)
    min_speed: float = 10.0  # m/s
    max_climb_rate: float = 3.0  # m/s
    max_descent_rate: float = 5.0  # m/s
    max_bank_angle: float = np.radians(45)  # radians
    max_turn_rate: float = np.radians(30)  # rad/s
    mass: float = 5.0  # kg
    drag_coefficient: float = 0.3
    power_consumption_base: float = 100.0  # Watts at cruise
    battery_capacity: float = 500.0 * 3600  # Joules (500 Wh)


class WindModel:
    """Models wind velocity as a function of position and time."""
    
    def __init__(self, wind_type: str = 'constant', 
                 base_wind: np.ndarray = np.array([0.0, 0.0, 0.0]),
                 seed: Optional[int] = None):
        """
        Args:
            wind_type: 'constant', 'spatial', or 'temporal'
            base_wind: Base wind vector [wx, wy, wz] in m/s
            seed: Random seed for stochastic wind
        """
        self.wind_type = wind_type
        self.base_wind = base_wind
        self.rng = np.random.RandomState(seed)
        
    def get_wind(self, position: np.ndarray, time: float) -> np.ndarray:
        """
        Get wind velocity at a given position and time.
        
        Args:
            position: [x, y, altitude] in meters
            time: Time in seconds
            
        Returns:
            Wind velocity [wx, wy, wz] in m/s
        """
        if self.wind_type == 'constant':
            return self.base_wind.copy()
            
        elif self.wind_type == 'spatial':
            # Simple spatial variation based on position
            x, y, z = position
            variation = np.array([
                0.1 * np.sin(x / 1000.0),
                0.1 * np.cos(y / 1000.0),
                0.0
            ])
            return self.base_wind + variation
            
        elif self.wind_type == 'temporal':
            # Time-varying wind
            variation = np.array([
                0.2 * np.sin(time / 100.0),
                0.2 * np.cos(time / 100.0),
                0.0
            ])
            return self.base_wind + variation
            
        else:
            return self.base_wind.copy()


class FlightDynamics:
    """Kinematic/point-mass flight dynamics model."""
    
    def __init__(self, params: AircraftParams, wind_model: WindModel):
        self.params = params
        self.wind_model = wind_model
        
    def compute_turn_radius(self, speed: float, bank_angle: float) -> float:
        """
        Compute turn radius for coordinated turn.
        
        R = v^2 / (g * tan(phi))
        """
        g = 9.81  # m/s^2
        if abs(bank_angle) < 1e-6:
            return np.inf
        return speed**2 / (g * np.tan(bank_angle))
    
    def compute_turn_rate(self, speed: float, bank_angle: float) -> float:
        """
        Compute turn rate (rad/s) for coordinated turn.
        
        omega = g * tan(phi) / v
        """
        g = 9.81
        return g * np.tan(bank_angle) / speed
    
    def compute_energy_rate(self, state: AircraftState) -> float:
        """
        Compute energy consumption rate (Watts).
        
        Simplified model: base power + drag-induced power
        """
        speed = np.linalg.norm(state.velocity)
        
        # Base power consumption
        power = self.params.power_consumption_base
        
        # Additional power for speed (simplified drag model)
        power += 0.5 * self.params.drag_coefficient * speed**3
        
        # Additional power for climbing
        if state.velocity[2] > 0:
            power += self.params.mass * 9.81 * state.velocity[2]
        
        return power
    
    def propagate(self, state: AircraftState, 
                  control_velocity: np.ndarray, 
                  dt: float) -> AircraftState:
        """
        Propagate aircraft state forward in time.
        
        Args:
            state: Current aircraft state
            control_velocity: Desired velocity [vx, vy, vz] in m/s (airspeed)
            dt: Time step in seconds
            
        Returns:
            New aircraft state
        """
        # Get wind at current position and time
        wind = self.wind_model.get_wind(state.position, state.time)
        
        # Ground velocity = airspeed + wind
        ground_velocity = control_velocity + wind
        
        # Update position
        new_position = state.position + ground_velocity * dt
        
        # Update heading
        if np.linalg.norm(ground_velocity[:2]) > 0.1:
            new_heading = np.arctan2(ground_velocity[1], ground_velocity[0])
        else:
            new_heading = state.heading
        
        # Compute energy consumption
        power = self.compute_energy_rate(state)
        energy_consumed = power * dt
        new_energy = state.energy_remaining - energy_consumed
        
        return AircraftState(
            time=state.time + dt,
            position=new_position,
            velocity=ground_velocity,
            heading=new_heading,
            energy_remaining=new_energy
        )
    
    def check_maneuver_feasibility(self, current_heading: float, 
                                   target_heading: float,
                                   speed: float, 
                                   time_available: float) -> bool:
        """
        Check if a heading change is feasible given turn rate limits.
        
        Args:
            current_heading: Current heading in radians
            target_heading: Target heading in radians
            speed: Current speed in m/s
            time_available: Time available for maneuver in seconds
            
        Returns:
            True if maneuver is feasible
        """
        # Compute required turn angle (shortest direction)
        delta_heading = target_heading - current_heading
        delta_heading = np.arctan2(np.sin(delta_heading), np.cos(delta_heading))
        
        # Maximum turn rate at max bank angle
        max_omega = self.compute_turn_rate(speed, self.params.max_bank_angle)
        
        # Time required for turn
        time_required = abs(delta_heading) / max_omega
        
        return time_required <= time_available
