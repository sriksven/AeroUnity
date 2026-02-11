"""
Objective function definitions.

This module provides objective functions that can be used by both
aircraft and spacecraft mission planners.
"""

from typing import Dict, Any, Callable
import numpy as np


class MinimizeTimeObjective:
    """Minimize total mission time."""
    
    def __init__(self, name: str = "minimize_time"):
        self.name = name
        self.objective_type = 'minimize'
        
    def evaluate(self, solution: Dict[str, Any]) -> float:
        """Return total mission time."""
        return solution.get('total_time', 0.0)


class MinimizeEnergyObjective:
    """Minimize total energy consumption."""
    
    def __init__(self, name: str = "minimize_energy"):
        self.name = name
        self.objective_type = 'minimize'
        
    def evaluate(self, solution: Dict[str, Any]) -> float:
        """Return total energy consumed."""
        return solution.get('total_energy', 0.0)


class MaximizeValueObjective:
    """Maximize mission value (e.g., science value, targets captured)."""
    
    def __init__(self, name: str = "maximize_value"):
        self.name = name
        self.objective_type = 'maximize'
        
    def evaluate(self, solution: Dict[str, Any]) -> float:
        """Return total mission value."""
        return solution.get('mission_value', 0.0)


class WeightedObjective:
    """Combine multiple objectives with weights."""
    
    def __init__(self, name: str, objectives: list, weights: list):
        """
        Args:
            objectives: List of objective instances
            weights: List of weights (same length as objectives)
        """
        self.name = name
        self.objectives = objectives
        self.weights = weights
        self.objective_type = 'maximize'  # After weighting
        
    def evaluate(self, solution: Dict[str, Any]) -> float:
        """Compute weighted sum of objectives."""
        total = 0.0
        
        for obj, weight in zip(self.objectives, self.weights):
            value = obj.evaluate(solution)
            
            # Convert minimize to maximize by negating
            if obj.objective_type == 'minimize':
                value = -value
                
            total += weight * value
            
        return total


class CustomObjective:
    """Objective defined by a custom evaluation function."""
    
    def __init__(self, name: str, 
                 eval_func: Callable[[Dict[str, Any]], float],
                 objective_type: str = 'maximize'):
        self.name = name
        self.eval_func = eval_func
        self.objective_type = objective_type
        
    def evaluate(self, solution: Dict[str, Any]) -> float:
        """Evaluate using custom function."""
        return self.eval_func(solution)
