"""
Aircraft-specific constraints for mission planning.

This module defines constraints specific to aircraft missions including
geofencing, altitude restrictions, maneuver limits, and energy constraints.
"""

import numpy as np
from typing import List, Dict, Any
from shapely.geometry import Polygon, Point, LineString


class AircraftGeofenceConstraint:
    """Ensure aircraft path stays outside no-fly zones."""
    
    def __init__(self, name: str, no_fly_polygons: List[Polygon],
                 constraint_type: str = 'hard'):
        self.name = name
        self.no_fly_polygons = no_fly_polygons
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if any waypoint or path segment violates geofence."""
        path = state.get('path', [])
        
        if not path:
            return True, 0.0
        
        max_violation = 0.0
        
        for i, waypoint in enumerate(path):
            point = Point(waypoint[0], waypoint[1])
            
            for zone in self.no_fly_polygons:
                if zone.contains(point):
                    # Compute penetration depth
                    distance = point.distance(zone.exterior)
                    max_violation = max(max_violation, distance)
                    
        return max_violation == 0.0, max_violation


class AltitudeConstraint:
    """Enforce minimum and maximum altitude limits."""
    
    def __init__(self, name: str, min_altitude: float, max_altitude: float,
                 constraint_type: str = 'hard'):
        self.name = name
        self.min_altitude = min_altitude
        self.max_altitude = max_altitude
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check altitude constraints along path."""
        path = state.get('path', [])
        
        if not path:
            return True, 0.0
            
        max_violation = 0.0
        
        for waypoint in path:
            altitude = waypoint[2] if len(waypoint) > 2 else 0.0
            
            if altitude < self.min_altitude:
                max_violation = max(max_violation, self.min_altitude - altitude)
            elif altitude > self.max_altitude:
                max_violation = max(max_violation, altitude - self.max_altitude)
                
        return max_violation == 0.0, max_violation


class TurnRateConstraint:
    """Enforce maximum turn rate between waypoints."""
    
    def __init__(self, name: str, max_turn_rate: float, cruise_speed: float,
                 constraint_type: str = 'hard'):
        """
        Args:
            max_turn_rate: Maximum turn rate in rad/s
            cruise_speed: Typical cruise speed in m/s
        """
        self.name = name
        self.max_turn_rate = max_turn_rate
        self.cruise_speed = cruise_speed
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if turn rates between waypoints are feasible."""
        path = state.get('path', [])
        times = state.get('times', [])
        
        if len(path) < 2:
            return True, 0.0
            
        max_violation = 0.0
        
        for i in range(len(path) - 2):
            # Compute heading changes
            v1 = np.array(path[i+1][:2]) - np.array(path[i][:2])
            v2 = np.array(path[i+2][:2]) - np.array(path[i+1][:2])
            
            if np.linalg.norm(v1) < 1e-6 or np.linalg.norm(v2) < 1e-6:
                continue
                
            # Angle between segments
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            turn_angle = np.arccos(cos_angle)
            
            # Time available for turn
            if times and i+1 < len(times) and i < len(times):
                time_available = times[i+1] - times[i]
            else:
                # Estimate from distance and speed
                time_available = np.linalg.norm(v1) / self.cruise_speed
                
            # Required turn rate
            required_turn_rate = turn_angle / max(time_available, 0.1)
            
            if required_turn_rate > self.max_turn_rate:
                max_violation = max(max_violation, 
                                   required_turn_rate - self.max_turn_rate)
                
        return max_violation == 0.0, max_violation


class EnergyConstraint:
    """Ensure aircraft has sufficient energy for entire mission."""
    
    def __init__(self, name: str, initial_energy: float, 
                 min_reserve: float = 0.0,
                 constraint_type: str = 'hard'):
        self.name = name
        self.initial_energy = initial_energy
        self.min_reserve = min_reserve
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if mission energy consumption is within limits."""
        total_energy = state.get('total_energy', 0.0)
        
        energy_remaining = self.initial_energy - total_energy
        
        if energy_remaining < self.min_reserve:
            violation = self.min_reserve - energy_remaining
            return False, violation
        else:
            return True, 0.0
