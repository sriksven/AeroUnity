"""
Spacecraft-specific constraints for mission planning.

This module defines constraints for spacecraft missions including
pointing/slew limits, power budget, and operational duty cycle.
"""

import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta


class PointingSlewConstraint:
    """Enforce maximum slew rate between observations."""
    
    def __init__(self, name: str, max_slew_rate: float,
                 constraint_type: str = 'hard'):
        """
        Args:
            max_slew_rate: Maximum slew rate in degrees/second
        """
        self.name = name
        self.max_slew_rate = max_slew_rate
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if slew maneuvers are feasible."""
        schedule = state.get('schedule', [])
        
        if len(schedule) < 2:
            return True, 0.0
            
        max_violation = 0.0
        
        for i in range(len(schedule) - 1):
            current = schedule[i]
            next_item = schedule[i + 1]
            
            # Skip if not both observations
            if current.get('type') != 'observation' or next_item.get('type') != 'observation':
                continue
                
            # Compute slew angle (simplified)
            pos1 = current.get('target_position', np.array([0, 0, 1]))
            pos2 = next_item.get('target_position', np.array([0, 0, 1]))
            
            slew_angle = np.arccos(np.clip(np.dot(pos1, pos2), -1.0, 1.0))
            slew_angle_deg = np.degrees(slew_angle)
            
            # Time available
            time_available = (next_item['start_time'] - current['end_time']).total_seconds()
            
            if time_available > 0:
                required_rate = slew_angle_deg / time_available
                
                if required_rate > self.max_slew_rate:
                    max_violation = max(max_violation, required_rate - self.max_slew_rate)
        
        return max_violation == 0.0, max_violation


class PowerBudgetConstraint:
    """Ensure spacecraft power budget is maintained."""
    
    def __init__(self, name: str, battery_capacity: float,
                 solar_power: float, min_battery_level: float = 0.2,
                 constraint_type: str = 'hard'):
        """
        Args:
            battery_capacity: Battery capacity in Wh
            solar_power: Solar panel power generation in W
            min_battery_level: Minimum battery level (0.0 to 1.0)
        """
        self.name = name
        self.battery_capacity = battery_capacity
        self.solar_power = solar_power
        self.min_battery_level = min_battery_level
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if power budget is maintained throughout mission."""
        schedule = state.get('schedule', [])
        
        if not schedule:
            return True, 0.0
            
        # Simulate power consumption
        battery_level = 1.0  # Start at full charge
        min_level_reached = 1.0
        
        for item in schedule:
            duration = (item['end_time'] - item['start_time']).total_seconds() / 3600.0  # hours
            
            # Power consumption based on activity type
            if item['type'] == 'observation':
                power_consumption = 50.0  # W (imaging)
            elif item['type'] == 'downlink':
                power_consumption = 80.0  # W (transmission)
            else:
                power_consumption = 20.0  # W (idle)
            
            # Net power (consumption - generation)
            # Simplified: assume 50% of time in sunlight
            net_power = power_consumption - (self.solar_power * 0.5)
            
            # Update battery
            energy_change = net_power * duration  # Wh
            battery_level -= energy_change / self.battery_capacity
            battery_level = np.clip(battery_level, 0.0, 1.0)
            
            min_level_reached = min(min_level_reached, battery_level)
        
        if min_level_reached < self.min_battery_level:
            violation = self.min_battery_level - min_level_reached
            return False, violation
        else:
            return True, 0.0


class DutyCycleConstraint:
    """Limit maximum operations per orbit (thermal/duty cycle proxy)."""
    
    def __init__(self, name: str, max_ops_per_orbit: int,
                 orbital_period: float,
                 constraint_type: str = 'hard'):
        """
        Args:
            max_ops_per_orbit: Maximum number of operations per orbit
            orbital_period: Orbital period in seconds
        """
        self.name = name
        self.max_ops_per_orbit = max_ops_per_orbit
        self.orbital_period = orbital_period
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if duty cycle limits are respected."""
        schedule = state.get('schedule', [])
        
        if not schedule:
            return True, 0.0
            
        # Count operations per orbit
        start_time = schedule[0]['start_time']
        orbit_start = start_time
        ops_in_orbit = 0
        max_violation = 0
        
        for item in schedule:
            # Check if we've moved to next orbit
            time_since_orbit_start = (item['start_time'] - orbit_start).total_seconds()
            
            if time_since_orbit_start > self.orbital_period:
                # New orbit
                orbit_start = item['start_time']
                ops_in_orbit = 0
            
            # Count observation and downlink as operations
            if item['type'] in ['observation', 'downlink']:
                ops_in_orbit += 1
                
                if ops_in_orbit > self.max_ops_per_orbit:
                    max_violation = max(max_violation, ops_in_orbit - self.max_ops_per_orbit)
        
        return max_violation == 0, float(max_violation)


class DownlinkConstraint:
    """Ensure observations are downlinked within time window."""
    
    def __init__(self, name: str, max_storage_time: float = 86400.0,
                 constraint_type: str = 'soft'):
        """
        Args:
            max_storage_time: Maximum time data can be stored before downlink (seconds)
        """
        self.name = name
        self.max_storage_time = max_storage_time
        self.constraint_type = constraint_type
        self.violation_penalty = 10.0  # Penalty per observation not downlinked
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if all observations are downlinked in time."""
        schedule = state.get('schedule', [])
        
        # Track observations and their downlinks
        observations = {}
        downlinked = set()
        
        for item in schedule:
            if item['type'] == 'observation':
                obs_id = item.get('target_id', item['start_time'])
                observations[obs_id] = item['end_time']
            elif item['type'] == 'downlink':
                # Mark associated observations as downlinked
                obs_ids = item.get('observation_ids', [])
                downlinked.update(obs_ids)
        
        # Count observations not downlinked
        not_downlinked = len(observations) - len(downlinked)
        
        if not_downlinked > 0:
            return False, float(not_downlinked)
        else:
            return True, 0.0
