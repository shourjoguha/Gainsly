"""Pydantic schemas for settings and configuration API endpoints."""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    E1RMFormula,
    ExperienceLevel,
    PersonaTone,
    PersonaAggression,
    MovementPattern,
    PrimaryRegion,
    PrimaryMuscle,
    SkillLevel,
    CNSLoad,
    MetricType,
)


# ============== User Settings Schemas ==============

class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    active_e1rm_formula: E1RMFormula | None = None
    e1rm_formula: str | None = None
    use_metric: bool | None = None  # True = kg, False = lbs
    preferred_units: str | None = None
    persona_coaching_style: str | None = None
    persona_strictness: int | None = Field(default=None, ge=1, le=10)
    persona_humor: int | None = Field(default=None, ge=1, le=10)
    persona_explanation_level: int | None = Field(default=None, ge=1, le=5)
    notification_preference: str | None = None
    default_session_duration_minutes: int | None = Field(default=None, ge=15, le=180)


class UserSettingsResponse(BaseModel):
    """User settings response."""
    id: int
    user_id: int | None = None
    active_e1rm_formula: E1RMFormula | None = None
    e1rm_formula: str | None = None
    use_metric: bool | None = None
    preferred_units: str | None = None
    persona_coaching_style: str | None = None
    persona_strictness: int | None = None
    persona_humor: int | None = None
    persona_explanation_level: int | None = None
    notification_preference: str | None = None
    default_session_duration_minutes: int | None = None
    
    class Config:
        from_attributes = True


# ============== User Profile Schemas ==============

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    name: str | None = None
    experience_level: ExperienceLevel | None = None
    persona_tone: PersonaTone | None = None
    persona_aggression: PersonaAggression | None = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: int
    name: str | None
    email: str | None
    experience_level: ExperienceLevel
    persona_tone: PersonaTone
    persona_aggression: PersonaAggression
    
    class Config:
        from_attributes = True


# ============== Movement Schemas ==============

class MovementResponse(BaseModel):
    """Movement response schema."""
    id: int
    name: str
    pattern: str | None = None
    primary_pattern: MovementPattern | None = None
    secondary_patterns: list[str] | None = None
    primary_muscle: str | None = None
    primary_muscles: list[str] | None = None
    secondary_muscles: list[str] | None = None
    primary_region: PrimaryRegion | str | None = None
    default_equipment: str | None = None
    complexity: str | None = None
    cns_load: str | None = None
    cns_demand: int | None = None
    skill_level: int | None = None
    compound: bool | None = None
    is_compound: bool | None = None
    is_complex_lift: bool | None = None
    is_unilateral: bool | None = None
    metric_type: str | None = None
    discipline_tags: list[str] | None = None
    equipment_tags: list[str] | None = None
    substitution_group: str | None = None
    description: str | None = None
    user_id: int | None = None  # Add user_id
    
    class Config:
        from_attributes = True


class MovementCreate(BaseModel):
    """Schema for creating a custom movement."""
    name: str
    pattern: MovementPattern
    primary_muscle: PrimaryMuscle | None = None
    primary_region: PrimaryRegion | None = None
    secondary_muscles: list[PrimaryMuscle] | None = None
    default_equipment: str | None = None
    skill_level: SkillLevel | None = SkillLevel.INTERMEDIATE
    cns_load: CNSLoad | None = CNSLoad.MODERATE
    metric_type: MetricType | None = MetricType.REPS
    compound: bool = True
    description: str | None = None


class MovementListResponse(BaseModel):
    """List of movements with filtering."""
    movements: list[MovementResponse]
    total: int
    limit: int | None = None
    offset: int | None = None
    filters_applied: dict[str, Any] | None = None


# ============== Heuristic Config Schemas ==============

class HeuristicConfigCreate(BaseModel):
    """Schema for creating a new heuristic config version."""
    name: str
    key: str | None = None
    category: str | None = None
    json_blob: dict[str, Any] | None = None
    value: dict[str, Any] | None = None
    description: str | None = None


class HeuristicConfigResponse(BaseModel):
    """Heuristic config response."""
    id: int
    name: str | None = None
    key: str | None = None
    category: str | None = None
    version: int | None = None
    json_blob: dict[str, Any] | None = None
    value: dict[str, Any] | None = None
    description: str | None = None
    active: bool | None = None
    created_at: datetime | None = None
    
    class Config:
        from_attributes = True


class HeuristicConfigListResponse(BaseModel):
    """List of heuristic configs."""
    configs: list[HeuristicConfigResponse]
    
    
class ActivateConfigRequest(BaseModel):
    """Request to activate a specific config version."""
    version: int | None = None  # If None, activates the latest version


# ============== Movement Rule Schemas ==============

class MovementRuleResponse(BaseModel):
    """Movement rule response."""
    id: int
    user_id: int | None = None
    movement_id: int
    movement_name: str | None = None
    rule_type: str
    substitute_movement_id: int | None = None
    substitute_movement_name: str | None = None
    cadence: str | None = None
    reason: str | None = None
    notes: str | None = None
    
    class Config:
        from_attributes = True


class MovementRuleCreate(BaseModel):
    """Create movement rule."""
    movement_id: int
    rule_type: str
    substitute_movement_id: int | None = None
    cadence: str | None = Field(default="per_microcycle")
    reason: str | None = None
    notes: str | None = None


class MovementRuleUpdate(BaseModel):
    """Update movement rule."""
    rule_type: str | None = None
    substitute_movement_id: int | None = None
    cadence: str | None = None
    reason: str | None = None
    notes: str | None = None


# ============== Enjoyable Activity Schemas ==============

class EnjoyableActivityResponse(BaseModel):
    """Enjoyable activity response."""
    id: int
    user_id: int | None = None
    activity_name: str | None = None
    activity_type: str | None = None
    category: str | None = None
    custom_name: str | None = None
    typical_duration_minutes: int | None = None
    recommend_every_days: int | None = None
    enabled: bool | None = None
    notes: str | None = None
    
    class Config:
        from_attributes = True


class EnjoyableActivityCreate(BaseModel):
    """Create enjoyable activity."""
    activity_name: str | None = None
    activity_type: str | None = None
    category: str | None = None
    custom_name: str | None = None
    typical_duration_minutes: int | None = None
    recommend_every_days: int | None = Field(default=28, ge=7, le=90)
    notes: str | None = None


class EnjoyableActivityUpdate(BaseModel):
    """Update enjoyable activity."""
    activity_name: str | None = None
    category: str | None = None
    typical_duration_minutes: int | None = None
    recommend_every_days: int | None = Field(default=None, ge=7, le=90)
    enabled: bool | None = None
    notes: str | None = None
