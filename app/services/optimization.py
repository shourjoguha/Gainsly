"""
Optimization Service using Google OR-Tools.
Implements a Constraint Satisfaction Problem (CSP) solver for workout generation.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ortools.sat.python import cp_model
from app.models import Movement, CNSLoad, MuscleRole
from app.models.enums import SkillLevel

@dataclass
class SolverMovement:
    """Simplified movement data for the solver (picklable)."""
    id: int
    name: str
    primary_muscle: str
    fatigue_factor: float
    stimulus_factor: float
    compound: bool
    is_complex_lift: bool

@dataclass
class OptimizationRequest:
    available_movements: List[SolverMovement]
    target_muscle_volumes: Dict[str, int]  # e.g., {"quadriceps": 4, "hamstrings": 3}
    max_fatigue: float
    min_stimulus: float
    user_skill_level: SkillLevel
    excluded_movement_ids: List[int]
    required_movement_ids: List[int]
    session_duration_minutes: int
    allow_complex_lifts: bool

@dataclass
class OptimizationResult:
    selected_movements: List[SolverMovement]
    total_fatigue: float
    total_stimulus: float
    estimated_duration: int
    status: str  # "OPTIMAL", "FEASIBLE", "INFEASIBLE"

class ConstraintSolver:
    def __init__(self):
        pass
        
    def solve_session(self, request: OptimizationRequest) -> OptimizationResult:
        """
        Solve for the optimal set of movements that satisfy volume targets
        while minimizing fatigue and maximizing stimulus.
        """
        # Create fresh model and solver for each request to avoid memory leaks
        # and performance degradation from accumulating variables
        model = cp_model.CpModel()
        solver = cp_model.CpSolver()

        # 1. Variables
        # x[i] is a boolean variable indicating if movement i is selected
        movement_vars = {}
        for m in request.available_movements:
            # Skip if explicitly excluded
            if m.id in request.excluded_movement_ids:
                continue
            
            # Skip if skill level mismatch (Hard Guardrail)
            # Simple hierarchy check would go here
            
            movement_vars[m.id] = model.NewBoolVar(f'movement_{m.id}')
            
        if not movement_vars:
            return OptimizationResult([], 0, 0, 0, "INFEASIBLE")

        # 2. Constraints
        
        # Set a time limit for the solver to prevent hanging
        solver.parameters.max_time_in_seconds = 10.0
        
        # A. Required Movements
        for m_id in request.required_movement_ids:
            if m_id in movement_vars:
                model.Add(movement_vars[m_id] == 1)
                
        # B. Volume Targets (Sets)
        # We assume 1 selection = 3 sets for simplicity in this V1
        # In V2, we would make sets an integer variable [3, 4, 5]
        SETS_PER_MOVEMENT = 3
        
        for muscle, target_sets in request.target_muscle_volumes.items():
            relevant_movements = []
            for m in request.available_movements:
                if m.id not in movement_vars:
                    continue
                # Check if movement hits this muscle (primary)
                # SolverMovement stores primary_muscle as string
                if m.primary_muscle == muscle:
                    relevant_movements.append(movement_vars[m.id])
            
            if relevant_movements:
                # Total sets >= Target
                # We assume each selected movement provides SETS_PER_MOVEMENT sets
                model.Add(sum(relevant_movements) * SETS_PER_MOVEMENT >= target_sets)

        # C. Max Fatigue Constraint
        fatigue_expr = sum(
            movement_vars[m.id] * int(m.fatigue_factor * 100) 
            for m in request.available_movements 
            if m.id in movement_vars
        )
        model.Add(fatigue_expr <= int(request.max_fatigue * 100))
        
        # D. Max Duration Constraint
        # Assume 1 set = 2 mins + 2 mins rest = 4 mins
        # 3 sets = 12 mins
        MINS_PER_EXERCISE = 12
        duration_expr = sum(
            movement_vars[m.id] * MINS_PER_EXERCISE
            for m in request.available_movements
            if m.id in movement_vars
        )
        model.Add(duration_expr <= request.session_duration_minutes)
        
        # 3. Objective Function
        # Maximize: (Stimulus * Weight) - (Fatigue * Penalty)
        # We want high stimulus for the "budget" of fatigue
        
        stimulus_expr = sum(
            movement_vars[m.id] * int(m.stimulus_factor * 100)
            for m in request.available_movements
            if m.id in movement_vars
        )
        
        # Maximize Stimulus
        model.Maximize(stimulus_expr)
        
        # 3. Solve
        solver.parameters.max_time_in_seconds = 10.0
        status = solver.Solve(model)
        
        # 4. Result
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            selected = []
            total_fatigue = 0.0
            total_stimulus = 0.0
            
            for m in request.available_movements:
                if m.id in movement_vars and solver.Value(movement_vars[m.id]):
                    selected.append(m)
                    total_fatigue += m.fatigue_factor
                    total_stimulus += m.stimulus_factor
            
            status_str = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
            return OptimizationResult(
                selected_movements=selected,
                total_fatigue=total_fatigue,
                total_stimulus=total_stimulus,
                estimated_duration=len(selected) * MINS_PER_EXERCISE,
                status=status_str
            )
            
        return OptimizationResult([], 0, 0, 0, "INFEASIBLE")