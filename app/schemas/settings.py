"""Pydantic schemas for settings and configuration API endpoints."""
from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, computed_field, model_validator

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
    Sex,
    MuscleRole,
)


# ============== User Settings Schemas ==============

class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    active_e1rm_formula: E1RMFormula | None = None
    use_metric: bool | None = None  # True = kg, False = lbs


class UserSettingsResponse(BaseModel):
    """User settings response."""
    id: int
    user_id: int | None = None
    active_e1rm_formula: E1RMFormula | None = None
    use_metric: bool | None = None
    
    class Config:
        from_attributes = True


# ============== User Profile Schemas ==============

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    name: str | None = None
    experience_level: ExperienceLevel | None = None
    persona_tone: PersonaTone | None = None
    persona_aggression: PersonaAggression | None = None
    # UserProfile fields
    date_of_birth: date | None = None
    sex: Sex | None = None
    height_cm: int | None = None
    # Advanced Preferences
    discipline_preferences: dict[str, Any] | None = None
    discipline_experience: dict[str, Any] | None = None
    scheduling_preferences: dict[str, Any] | None = None
    # Long Term Goals
    long_term_goal_category: str | None = None
    long_term_goal_description: str | None = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: int
    name: str | None
    email: str | None
    experience_level: ExperienceLevel
    persona_tone: PersonaTone
    persona_aggression: PersonaAggression
    # UserProfile fields
    date_of_birth: date | None = None
    sex: Sex | None = None
    height_cm: int | None = None
    # Advanced Preferences
    discipline_preferences: dict[str, Any] | None = None
    discipline_experience: dict[str, Any] | None = None
    scheduling_preferences: dict[str, Any] | None = None
    # Long Term Goals
    long_term_goal_category: str | None = None
    long_term_goal_description: str | None = None
    
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
    complexity: str | int | None = None
    cns_load: str | None = None
    cns_demand: int | None = None
    skill_level: SkillLevel | str | None = None
    compound: bool | None = None
    is_compound: bool | None = None
    is_complex_lift: bool | None = None
    is_unilateral: bool | None = None
    metric_type: str | None = None
    disciplines: list[str] | None = None
    equipment: list[str] | None = None
    substitution_group: str | None = None
    description: str | None = None
    user_id: int | None = None  # Add user_id
    
    @model_validator(mode='before')
    @classmethod
    def populate_lists(cls, data: Any) -> Any:
        """Populate list fields from relationships/scalars."""
        if hasattr(data, "__dict__"):
            # It's an ORM object
            
            # 1. Primary Muscles (Scalar -> List)
            if hasattr(data, "primary_muscle") and data.primary_muscle:
                # Ensure we handle both Enum and raw value
                val = data.primary_muscle.value if hasattr(data.primary_muscle, "value") else data.primary_muscle
                setattr(data, "primary_muscles", [val])
            
            # 2. Secondary Muscles (Relationship -> List)
            if hasattr(data, "muscle_maps") and data.muscle_maps:
                # Filter for SECONDARY or STABILIZER
                secondary = []
                for mm in data.muscle_maps:
                    # Check role
                    role_name = mm.role.name if hasattr(mm.role, "name") else str(mm.role)
                    if role_name in ["SECONDARY", "STABILIZER"]:
                        if mm.muscle:
                            secondary.append(mm.muscle.slug)
                setattr(data, "secondary_muscles", secondary)
            
            # 3. Disciplines (Relationship -> List)
            if hasattr(data, "disciplines") and data.disciplines:
                discs = []
                for d in data.disciplines:
                    val = d.discipline.value if hasattr(d.discipline, "value") else d.discipline
                    discs.append(val)
                setattr(data, "disciplines", discs)
                
            # 4. Equipment (Relationship -> List)
            if hasattr(data, "equipment") and data.equipment:
                eqs = []
                for e in data.equipment:
                    if e.equipment:
                        eqs.append(e.equipment.name)
                setattr(data, "equipment", eqs)
                if eqs:
                    setattr(data, "default_equipment", eqs[0])

            # 5. Pattern (Enum -> String/Enum)
            if hasattr(data, "pattern") and data.pattern:
                 setattr(data, "primary_pattern", data.pattern)

        return data

    @computed_field
    def discipline_tags(self) -> list[str] | None:
        """Backward compatibility for discipline_tags."""
        return self.disciplines

    @computed_field
    def equipment_tags(self) -> list[str] | None:
        """Backward compatibility for equipment_tags."""
        return self.equipment

    @computed_field
    def primary_discipline(self) -> str | None:
        """Backward compatibility for primary_discipline."""
        return self.disciplines[0] if self.disciplines else None

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


class MovementFiltersResponse(BaseModel):
    """Distinct movement filters available in the repository."""
    patterns: list[str]
    regions: list[str]
    equipment: list[str]
    primary_disciplines: list[str]
    secondary_muscles: list[str] | None = None
    types: list[str] | None = None


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
    activity_type: str | None = None
    custom_name: str | None = None
    recommend_every_days: int | None = None
    enabled: bool | None = None
    notes: str | None = None
    
    class Config:
        from_attributes = True


class EnjoyableActivityCreate(BaseModel):
    """Create enjoyable activity."""
    activity_type: str
    custom_name: str | None = None
    recommend_every_days: int | None = Field(default=28, ge=7, le=90)
    notes: str | None = None


class EnjoyableActivityUpdate(BaseModel):
    """Update enjoyable activity."""
    recommend_every_days: int | None = Field(default=None, ge=7, le=90)
    enabled: bool | None = None
    notes: str | None = None
