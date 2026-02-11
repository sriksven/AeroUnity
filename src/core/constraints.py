"""
Constraint definitions and validation utilities.

This module provides concrete constraint implementations that can be used
by both aircraft and spacecraft mission planners.
"""

from typing import Dict, Any, Callable, List
import numpy as np
from dataclasses import dataclass


class NumericConstraint:
    """Constraint on a numeric value with bounds."""
    
    def __init__(self, name: str, variable_name: str, 
                 lower_bound: float = -np.inf, 
                 upper_bound: float = np.inf,
                 constraint_type: str = 'hard'):
        self.name = name
        self.variable_name = variable_name
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if value is within bounds."""
        value = state.get(self.variable_name, 0.0)
        
        if value < self.lower_bound:
            violation = self.lower_bound - value
            return False, violation
        elif value > self.upper_bound:
            violation = value - self.upper_bound
            return False, violation
        else:
            return True, 0.0


class CustomConstraint:
    """Constraint defined by a custom evaluation function."""
    
    def __init__(self, name: str, 
                 eval_func: Callable[[Dict[str, Any]], tuple[bool, float]],
                 constraint_type: str = 'hard'):
        self.name = name
        self.eval_func = eval_func
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Evaluate using custom function."""
        return self.eval_func(state)


class GeofenceConstraint:
    """Constraint to keep position outside of no-fly zones (polygons)."""
    
    def __init__(self, name: str, no_fly_zones: List[Any], 
                 constraint_type: str = 'hard'):
        """
        Args:
            no_fly_zones: List of Shapely Polygon objects
        """
        self.name = name
        self.no_fly_zones = no_fly_zones
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if position is inside any no-fly zone."""
        from shapely.geometry import Point
        
        position = state.get('position', None)
        if position is None:
            return True, 0.0
            
        point = Point(position[0], position[1])
        
        for zone in self.no_fly_zones:
            if zone.contains(point):
                # Violation is distance into the zone (simplified)
                violation = 1.0  # Could compute actual penetration depth
                return False, violation
                
        return True, 0.0


class ResourceConstraint:
    """Constraint on resource consumption (energy, battery, etc.)."""
    
    def __init__(self, name: str, resource_name: str, 
                 initial_amount: float, 
                 minimum_amount: float = 0.0,
                 constraint_type: str = 'hard'):
        self.name = name
        self.resource_name = resource_name
        self.initial_amount = initial_amount
        self.minimum_amount = minimum_amount
        self.constraint_type = constraint_type
        
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """Check if resource level is above minimum."""
        current_amount = state.get(self.resource_name, self.initial_amount)
        
        if current_amount < self.minimum_amount:
            violation = self.minimum_amount - current_amount
            return False, violation
        else:
            return True, 0.0


class ConstraintValidator:
    """Utility class for validating multiple constraints."""
    
    @staticmethod
    def validate_all(constraints: List[Any], 
                     state: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate all constraints against a state.
        
        Returns:
            (all_satisfied, list_of_violations)
        """
        violations = []
        
        for constraint in constraints:
            is_satisfied, violation_amount = constraint.evaluate(state)
            
            if not is_satisfied and constraint.constraint_type == 'hard':
                violations.append(
                    f"{constraint.name}: violation = {violation_amount:.4f}"
                )
        
        return len(violations) == 0, violations
    
    @staticmethod
    def compute_penalty(constraints: List[Any], 
                       state: Dict[str, Any]) -> float:
        """Compute total penalty from soft constraint violations."""
        total_penalty = 0.0
        
        for constraint in constraints:
            if constraint.constraint_type == 'soft':
                is_satisfied, violation_amount = constraint.evaluate(state)
                if not is_satisfied:
                    penalty = getattr(constraint, 'violation_penalty', 1.0)
                    total_penalty += penalty * violation_amount
        
        return total_penalty
