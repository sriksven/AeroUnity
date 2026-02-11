"""
AeroUnity - Unified Aerospace Mission Planning Framework

Core planning abstractions that work for both aircraft and spacecraft missions.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class DecisionVariable:
    """Represents a decision variable in the planning problem."""
    name: str
    domain: Any  # Can be continuous range, discrete set, etc.
    value: Optional[Any] = None


@dataclass
class Constraint:
    """Represents a constraint in the planning problem."""
    name: str
    constraint_type: str  # 'hard' or 'soft'
    violation_penalty: float = 0.0
    
    @abstractmethod
    def evaluate(self, state: Dict[str, Any]) -> tuple[bool, float]:
        """
        Evaluate constraint satisfaction.
        
        Returns:
            (is_satisfied, violation_amount)
        """
        pass


@dataclass
class Objective:
    """Represents an objective function to optimize."""
    name: str
    objective_type: str  # 'minimize' or 'maximize'
    
    @abstractmethod
    def evaluate(self, solution: Dict[str, Any]) -> float:
        """Compute objective value for a given solution."""
        pass


class MissionPlanner(ABC):
    """
    Abstract base class for mission planning.
    
    This unified interface is used by both aircraft and spacecraft planners.
    The key insight is that both domains share the same planning structure:
    - Decision variables (routes, schedules, resource allocations)
    - Constraints (physics, resources, operational limits)
    - Objectives (minimize time/energy, maximize value)
    - Solver (constraint programming, optimization)
    """
    
    def __init__(self, name: str):
        self.name = name
        self.decision_variables: List[DecisionVariable] = []
        self.constraints: List[Constraint] = []
        self.objectives: List[Objective] = []
        self.solution: Optional[Dict[str, Any]] = None
        
    @abstractmethod
    def define_decision_variables(self) -> List[DecisionVariable]:
        """Define the decision variables for this mission."""
        pass
    
    @abstractmethod
    def define_constraints(self) -> List[Constraint]:
        """Define all constraints for this mission."""
        pass
    
    @abstractmethod
    def define_objectives(self) -> List[Objective]:
        """Define optimization objectives."""
        pass
    
    @abstractmethod
    def solve(self) -> Dict[str, Any]:
        """
        Run the planning algorithm.
        
        Returns:
            solution: Dictionary containing the planned mission
        """
        pass
    
    def validate_solution(self, solution: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate that a solution satisfies all hard constraints.
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        
        for constraint in self.constraints:
            if constraint.constraint_type == 'hard':
                is_satisfied, violation_amount = constraint.evaluate(solution)
                if not is_satisfied:
                    violations.append(
                        f"{constraint.name}: violation = {violation_amount}"
                    )
        
        return len(violations) == 0, violations
    
    def compute_objective_value(self, solution: Dict[str, Any]) -> float:
        """Compute total objective value for a solution."""
        total = 0.0
        for objective in self.objectives:
            value = objective.evaluate(solution)
            if objective.objective_type == 'minimize':
                total -= value  # Convert to maximization
            else:
                total += value
        return total
    
    def get_metrics(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key performance metrics from a solution.
        
        Returns:
            Dictionary of metrics (implementation-specific)
        """
        is_valid, violations = self.validate_solution(solution)
        
        return {
            'is_valid': is_valid,
            'num_violations': len(violations),
            'violations': violations,
            'objective_value': self.compute_objective_value(solution),
        }
