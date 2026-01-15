"""Pydantic schemas for program-related API endpoints."""
from datetime import date as DateType, datetime as DatetimeType
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import (
    Goal,
    SplitTemplate,
    ProgressionStyle,
    PersonaTone,
    PersonaAggression,
    MicrocycleStatus,
    SessionType,
)


# ============== Program Schemas ==============

class GoalWeight(BaseModel):
    """Single goal with its weight."""
    goal: Goal
    weight: int = Field(ge=0, le=10)


class DisciplineWeight(BaseModel):
    """Single discipline/training style with its weight."""
    discipline: str  # e.g., "bodybuilding", "powerlifting", "crossfit"
    weight: int = Field(ge=0, le=10)


class HybridDayDefinition(BaseModel):
    """Day definition for hybrid splits."""
    day: int = Field(ge=1, le=10)
    session_type: SessionType
    focus: list[str] | None = None  # Movement patterns to focus on
    notes: str | None = None


class HybridBlockComposition(BaseModel):
    """Block composition for hybrid splits."""
    blocks: list[str]  # e.g., ["ppl_block", "ppl_block", "cardio_block", "rest_block"]


class HybridDefinition(BaseModel):
    """Hybrid split definition - either day-by-day or block composition."""
    mode: str = Field(pattern="^(day_by_day|block_composition)$")
    days: list[HybridDayDefinition] | None = None
    composition: HybridBlockComposition | None = None
    
    @model_validator(mode="after")
    def validate_mode_data(self):
        if self.mode == "day_by_day" and not self.days:
            raise ValueError("days required for day_by_day mode")
        if self.mode == "block_composition" and not self.composition:
            raise ValueError("composition required for block_composition mode")
        return self


class MovementRuleCreate(BaseModel):
    """Movement rule for program creation."""
    movement_id: int
    rule_type: str = Field(pattern="^(hard_no|hard_yes|preferred)$")
    cadence: str = Field(default="per_microcycle", pattern="^(per_microcycle|weekly|biweekly)$")
    notes: str | None = None


class EnjoyableActivityCreate(BaseModel):
    """Enjoyable activity for program creation."""
    activity_type: str
    custom_name: str | None = None
    recommend_every_days: int = Field(default=28, ge=7, le=90)


class ProgramCreate(BaseModel):
    """Schema for creating a new program."""
    # Goals (1-3 required, weights must sum to 10)
    goals: list[GoalWeight] = Field(min_length=1, max_length=3)
    
    # Duration
    duration_weeks: int = Field(ge=8, le=12)
    program_start_date: DateType | None = None  # Defaults to today (renamed to avoid shadowing)
    
    # Structure
    split_template: SplitTemplate
    days_per_week: int = Field(ge=2, le=7)  # User's training frequency preference
    progression_style: ProgressionStyle
    hybrid_definition: HybridDefinition | None = None
    
    # Deload
    deload_every_n_microcycles: int = Field(default=4, ge=2, le=8)
    
    # Persona (optional - uses user defaults if not provided)
    persona_tone: PersonaTone | None = None
    persona_aggression: PersonaAggression | None = None
    
    # Disciplines/Training styles (optional - ten dollar method, weights sum to 10)
    disciplines: list[DisciplineWeight] | None = None
    
    # Movement rules (optional)
    movement_rules: list[MovementRuleCreate] | None = None
    
    # Enjoyable activities (optional)
    enjoyable_activities: list[EnjoyableActivityCreate] | None = None
    
    @field_validator("goals")
    @classmethod
    def validate_goals_sum(cls, v):
        total = sum(g.weight for g in v)
        if total != 10:
            raise ValueError(f"Goal weights must sum to 10, got {total}")
        # Check for unique goals
        goal_names = [g.goal for g in v]
        if len(goal_names) != len(set(goal_names)):
            raise ValueError("Goals must be unique")
        return v
    
    @model_validator(mode="after")
    def validate_hybrid(self):
        if self.split_template == SplitTemplate.HYBRID and not self.hybrid_definition:
            raise ValueError("hybrid_definition required for HYBRID split template")
        return self


class ProgramResponse(BaseModel):
    """Program response schema."""
    id: int
    user_id: int
    program_start_date: DateType | None = None  # Renamed to avoid shadowing
    duration_weeks: int
    goal_1: Goal
    goal_2: Goal
    goal_3: Goal
    goal_weight_1: int
    goal_weight_2: int
    goal_weight_3: int
    split_template: SplitTemplate
    progression_style: ProgressionStyle
    hybrid_definition: dict | None = None
    deload_every_n_microcycles: int
    persona_tone: PersonaTone | None = None
    persona_aggression: PersonaAggression | None = None
    is_active: bool = True
    created_at: DatetimeType | None = None
    
    class Config:
        from_attributes = True


# ============== Microcycle Schemas ==============

class MicrocycleResponse(BaseModel):
    """Microcycle response schema."""
    id: int
    program_id: int
    micro_start_date: DateType | None = None  # Renamed to avoid shadowing
    length_days: int
    sequence_number: int
    status: MicrocycleStatus
    is_deload: bool = False
    
    class Config:
        from_attributes = True


# ============== Session Schemas ==============

class ExerciseBlock(BaseModel):
    """Exercise within a session block."""
    movement: str
    movement_id: int | None = None
    sets: int | None = None  # Optional for cooldown/stretches that only have duration
    rep_range_min: int | None = None
    rep_range_max: int | None = None
    target_rpe: float | None = None
    target_rir: int | None = None
    duration_seconds: int | None = None
    rest_seconds: int | None = None
    superset_with: str | None = None
    notes: str | None = None


class FinisherBlock(BaseModel):
    """Finisher block schema."""
    type: str  # EMOM, AMRAP, circuit, etc.
    duration_minutes: int | None = None
    rounds: int | None = None
    duration_seconds: int | None = None
    rest_seconds: int | None = None
    exercises: list[ExerciseBlock] | None = None
    notes: str | None = None


class SessionResponse(BaseModel):
    """Session response schema."""
    id: int
    microcycle_id: int
    session_date: DateType | None = None  # Renamed to avoid shadowing
    day_number: int
    session_type: SessionType
    intent_tags: list[str] = []
    warmup: list[ExerciseBlock] | None = None
    main: list[ExerciseBlock] | None = None
    accessory: list[ExerciseBlock] | None = None
    finisher: FinisherBlock | None = None
    cooldown: list[ExerciseBlock] | None = None
    estimated_duration_minutes: int | None = None
    warmup_duration_minutes: int | None = None
    main_duration_minutes: int | None = None
    accessory_duration_minutes: int | None = None
    finisher_duration_minutes: int | None = None
    cooldown_duration_minutes: int | None = None
    coach_notes: str | None
    
    class Config:
        from_attributes = True


class ProgramWithMicrocycleResponse(BaseModel):
    """Program with active microcycle and sessions."""
    program: ProgramResponse
    active_microcycle: MicrocycleResponse | None
    upcoming_sessions: list[SessionResponse]
    
    class Config:
        from_attributes = True
