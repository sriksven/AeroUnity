"""
Unit tests for core planning framework.

This module tests the unified planning abstractions to ensure
consistency across aircraft and spacecraft implementations.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.planner_base import MissionPlanner, DecisionVariable, Constraint, Objective
from src.core.constraints import (NumericConstraint, CustomConstraint, 
                                  GeofenceConstraint, ResourceConstraint)
from src.core.objectives import (MinimizeTimeObjective, MinimizeEnergyObjective,
                                 MaximizeValueObjective, WeightedObjective)


class TestConstraints:
    """Test constraint implementations."""
    
    def test_numeric_constraint_within_bounds(self):
        """Test numeric constraint with value within bounds."""
        constraint = NumericConstraint(
            name="test_constraint",
            variable_name="value",
            lower_bound=0.0,
            upper_bound=10.0
        )
        
        state = {'value': 5.0}
        is_satisfied, violation = constraint.evaluate(state)
        
        assert is_satisfied == True
        assert violation == 0.0
    
    def test_numeric_constraint_below_lower_bound(self):
        """Test numeric constraint with value below lower bound."""
        constraint = NumericConstraint(
            name="test_constraint",
            variable_name="value",
            lower_bound=0.0,
            upper_bound=10.0
        )
        
        state = {'value': -2.0}
        is_satisfied, violation = constraint.evaluate(state)
        
        assert is_satisfied == False
        assert violation == 2.0
    
    def test_numeric_constraint_above_upper_bound(self):
        """Test numeric constraint with value above upper bound."""
        constraint = NumericConstraint(
            name="test_constraint",
            variable_name="value",
            lower_bound=0.0,
            upper_bound=10.0
        )
        
        state = {'value': 12.0}
        is_satisfied, violation = constraint.evaluate(state)
        
        assert is_satisfied == False
        assert violation == 2.0
    
    def test_resource_constraint_sufficient(self):
        """Test resource constraint with sufficient resources."""
        constraint = ResourceConstraint(
            name="battery",
            resource_name="battery_level",
            initial_amount=100.0,
            minimum_amount=20.0
        )
        
        state = {'battery_level': 50.0}
        is_satisfied, violation = constraint.evaluate(state)
        
        assert is_satisfied == True
        assert violation == 0.0
    
    def test_resource_constraint_insufficient(self):
        """Test resource constraint with insufficient resources."""
        constraint = ResourceConstraint(
            name="battery",
            resource_name="battery_level",
            initial_amount=100.0,
            minimum_amount=20.0
        )
        
        state = {'battery_level': 10.0}
        is_satisfied, violation = constraint.evaluate(state)
        
        assert is_satisfied == False
        assert violation == 10.0


class TestObjectives:
    """Test objective function implementations."""
    
    def test_minimize_time_objective(self):
        """Test time minimization objective."""
        objective = MinimizeTimeObjective()
        
        solution = {'total_time': 100.0}
        value = objective.evaluate(solution)
        
        assert value == 100.0
        assert objective.objective_type == 'minimize'
    
    def test_minimize_energy_objective(self):
        """Test energy minimization objective."""
        objective = MinimizeEnergyObjective()
        
        solution = {'total_energy': 500.0}
        value = objective.evaluate(solution)
        
        assert value == 500.0
        assert objective.objective_type == 'minimize'
    
    def test_maximize_value_objective(self):
        """Test value maximization objective."""
        objective = MaximizeValueObjective()
        
        solution = {'mission_value': 75.0}
        value = objective.evaluate(solution)
        
        assert value == 75.0
        assert objective.objective_type == 'maximize'
    
    def test_weighted_objective(self):
        """Test weighted combination of objectives."""
        obj1 = MinimizeTimeObjective()
        obj2 = MinimizeEnergyObjective()
        
        weighted = WeightedObjective(
            name="weighted",
            objectives=[obj1, obj2],
            weights=[0.6, 0.4]
        )
        
        solution = {'total_time': 100.0, 'total_energy': 200.0}
        value = weighted.evaluate(solution)
        
        # Both are minimize, so they get negated: -0.6*100 - 0.4*200 = -140
        assert value == -140.0


class TestPlannerBase:
    """Test base planner functionality."""
    
    def test_constraint_validation(self):
        """Test constraint validation in base planner."""
        
        # Create a simple test planner
        class TestPlanner(MissionPlanner):
            def define_decision_variables(self):
                return []
            
            def define_constraints(self):
                return [
                    NumericConstraint("test", "value", 0.0, 10.0, 'hard')
                ]
            
            def define_objectives(self):
                return [MinimizeTimeObjective()]
            
            def solve(self):
                return {'value': 5.0, 'total_time': 100.0}
        
        planner = TestPlanner("test_planner")
        planner.define_constraints()
        
        # Test valid solution
        valid_solution = {'value': 5.0}
        is_valid, violations = planner.validate_solution(valid_solution)
        assert is_valid == True
        assert len(violations) == 0
        
        # Test invalid solution
        invalid_solution = {'value': 15.0}
        is_valid, violations = planner.validate_solution(invalid_solution)
        assert is_valid == False
        assert len(violations) == 1
    
    def test_objective_computation(self):
        """Test objective value computation."""
        
        class TestPlanner(MissionPlanner):
            def define_decision_variables(self):
                return []
            
            def define_constraints(self):
                return []
            
            def define_objectives(self):
                return [MinimizeTimeObjective()]
            
            def solve(self):
                return {'total_time': 100.0}
        
        planner = TestPlanner("test_planner")
        planner.define_objectives()
        
        solution = {'total_time': 100.0}
        obj_value = planner.compute_objective_value(solution)
        
        # Minimize objectives are negated
        assert obj_value == -100.0


def run_tests():
    """Run all unit tests."""
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_tests()
