"""API routes for user settings and configuration."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.config.settings import get_settings
from app.models import (
    User,
    UserSettings,
    UserMovementRule,
    UserEnjoyableActivity,
    Movement,
    HeuristicConfig,
    MovementPattern,
)
from app.schemas.settings import (
    UserSettingsResponse,
    UserSettingsUpdate,
    MovementRuleCreate,
    MovementRuleResponse,
    EnjoyableActivityCreate,
    EnjoyableActivityResponse,
    HeuristicConfigResponse,
    MovementResponse,
    MovementListResponse,
)

router = APIRouter()
settings = get_settings()


def get_current_user_id() -> int:
    """Get current user ID (MVP: hardcoded default user)."""
    return settings.default_user_id


# User settings
@router.get("/user", response_model=UserSettingsResponse)
async def get_user_settings(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get current user settings."""
    user_settings = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    user_settings = user_settings.scalar_one_or_none()
    
    if not user_settings:
        # Create default settings
        user_settings = UserSettings(user_id=user_id)
        db.add(user_settings)
        await db.commit()
        await db.refresh(user_settings)
    
    return UserSettingsResponse(
        id=user_settings.id,
        persona_coaching_style=user_settings.persona_coaching_style,
        persona_strictness=user_settings.persona_strictness,
        persona_humor=user_settings.persona_humor,
        persona_explanation_level=user_settings.persona_explanation_level,
        notification_preference=user_settings.notification_preference,
        preferred_units=user_settings.preferred_units,
        default_session_duration_minutes=user_settings.default_session_duration_minutes,
        e1rm_formula=user_settings.e1rm_formula,
    )


@router.patch("/user", response_model=UserSettingsResponse)
async def update_user_settings(
    update: UserSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Update user settings."""
    user_settings = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    user_settings = user_settings.scalar_one_or_none()
    
    if not user_settings:
        user_settings = UserSettings(user_id=user_id)
        db.add(user_settings)
    
    # Update fields that are provided
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user_settings, field, value)
    
    await db.commit()
    await db.refresh(user_settings)
    
    return UserSettingsResponse(
        id=user_settings.id,
        persona_coaching_style=user_settings.persona_coaching_style,
        persona_strictness=user_settings.persona_strictness,
        persona_humor=user_settings.persona_humor,
        persona_explanation_level=user_settings.persona_explanation_level,
        notification_preference=user_settings.notification_preference,
        preferred_units=user_settings.preferred_units,
        default_session_duration_minutes=user_settings.default_session_duration_minutes,
        e1rm_formula=user_settings.e1rm_formula,
    )


# Movement rules
@router.get("/movement-rules", response_model=List[MovementRuleResponse])
async def list_movement_rules(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List all user movement rules (exclusions, substitutions, etc.)."""
    result = await db.execute(
        select(UserMovementRule).where(UserMovementRule.user_id == user_id)
    )
    rules = list(result.scalars().all())
    
    responses = []
    for rule in rules:
        movement = await db.get(Movement, rule.movement_id)
        substitute = None
        if rule.substitute_movement_id:
            substitute = await db.get(Movement, rule.substitute_movement_id)
        
        responses.append(MovementRuleResponse(
            id=rule.id,
            movement_id=rule.movement_id,
            movement_name=movement.name if movement else "Unknown",
            rule_type=rule.rule_type,
            substitute_movement_id=rule.substitute_movement_id,
            substitute_movement_name=substitute.name if substitute else None,
            reason=rule.reason,
        ))
    
    return responses


@router.post("/movement-rules", response_model=MovementRuleResponse)
async def create_movement_rule(
    rule: MovementRuleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Create a new movement rule (exclude, substitute, prefer)."""
    # Verify movement exists
    movement = await db.get(Movement, rule.movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    
    # Verify substitute if provided
    substitute = None
    if rule.substitute_movement_id:
        substitute = await db.get(Movement, rule.substitute_movement_id)
        if not substitute:
            raise HTTPException(status_code=404, detail="Substitute movement not found")
    
    movement_rule = UserMovementRule(
        user_id=user_id,
        movement_id=rule.movement_id,
        rule_type=rule.rule_type,
        substitute_movement_id=rule.substitute_movement_id,
        reason=rule.reason,
    )
    db.add(movement_rule)
    await db.commit()
    
    return MovementRuleResponse(
        id=movement_rule.id,
        movement_id=movement_rule.movement_id,
        movement_name=movement.name,
        rule_type=movement_rule.rule_type,
        substitute_movement_id=movement_rule.substitute_movement_id,
        substitute_movement_name=substitute.name if substitute else None,
        reason=movement_rule.reason,
    )


@router.delete("/movement-rules/{rule_id}")
async def delete_movement_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Delete a movement rule."""
    rule = await db.get(UserMovementRule, rule_id)
    
    if not rule or rule.user_id != user_id:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    
    return {"detail": "Rule deleted"}


# Enjoyable activities
@router.get("/enjoyable-activities", response_model=List[EnjoyableActivityResponse])
async def list_enjoyable_activities(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List user's enjoyable activities for active recovery suggestions."""
    result = await db.execute(
        select(UserEnjoyableActivity).where(UserEnjoyableActivity.user_id == user_id)
    )
    activities = list(result.scalars().all())
    
    return [
        EnjoyableActivityResponse(
            id=act.id,
            activity_name=act.activity_name,
            category=act.category,
            typical_duration_minutes=act.typical_duration_minutes,
        )
        for act in activities
    ]


@router.post("/enjoyable-activities", response_model=EnjoyableActivityResponse)
async def create_enjoyable_activity(
    activity: EnjoyableActivityCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Add an enjoyable activity."""
    new_activity = UserEnjoyableActivity(
        user_id=user_id,
        activity_name=activity.activity_name,
        category=activity.category,
        typical_duration_minutes=activity.typical_duration_minutes,
    )
    db.add(new_activity)
    await db.commit()
    
    return EnjoyableActivityResponse(
        id=new_activity.id,
        activity_name=new_activity.activity_name,
        category=new_activity.category,
        typical_duration_minutes=new_activity.typical_duration_minutes,
    )


@router.delete("/enjoyable-activities/{activity_id}")
async def delete_enjoyable_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Delete an enjoyable activity."""
    activity = await db.get(UserEnjoyableActivity, activity_id)
    
    if not activity or activity.user_id != user_id:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    await db.delete(activity)
    await db.commit()
    
    return {"detail": "Activity deleted"}


# Heuristic configs (read-only for MVP)
@router.get("/heuristics", response_model=List[HeuristicConfigResponse])
async def list_heuristic_configs(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all heuristic configurations."""
    query = select(HeuristicConfig)
    
    if category:
        query = query.where(HeuristicConfig.category == category)
    
    result = await db.execute(query)
    configs = list(result.scalars().all())
    
    return [
        HeuristicConfigResponse(
            id=cfg.id,
            key=cfg.key,
            category=cfg.category,
            value=cfg.value_json,
            description=cfg.description,
        )
        for cfg in configs
    ]


@router.get("/heuristics/{key}", response_model=HeuristicConfigResponse)
async def get_heuristic_config(
    key: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific heuristic configuration by key."""
    result = await db.execute(
        select(HeuristicConfig).where(HeuristicConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return HeuristicConfigResponse(
        id=config.id,
        key=config.key,
        category=config.category,
        value=config.value_json,
        description=config.description,
    )


# Movements repository
@router.get("/movements", response_model=MovementListResponse)
async def list_movements(
    pattern: Optional[MovementPattern] = None,
    equipment: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List available movements from the repository."""
    query = select(Movement)
    
    if pattern:
        query = query.where(Movement.primary_pattern == pattern)
    if equipment:
        query = query.where(Movement.default_equipment == equipment)
    if search:
        query = query.where(Movement.name.ilike(f"%{search}%"))
    
    # Get total
    from sqlalchemy import func
    count_query = select(func.count(Movement.id))
    if pattern:
        count_query = count_query.where(Movement.primary_pattern == pattern)
    if equipment:
        count_query = count_query.where(Movement.default_equipment == equipment)
    if search:
        count_query = count_query.where(Movement.name.ilike(f"%{search}%"))
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    query = query.order_by(Movement.name).limit(limit).offset(offset)
    
    result = await db.execute(query)
    movements = list(result.scalars().all())
    
    return MovementListResponse(
        movements=[
            MovementResponse(
                id=m.id,
                name=m.name,
                primary_pattern=m.primary_pattern,
                secondary_patterns=m.secondary_patterns_json,
                primary_muscles=m.primary_muscles_json,
                secondary_muscles=m.secondary_muscles_json,
                primary_region=m.primary_region,
                default_equipment=m.default_equipment,
                complexity=m.complexity,
                is_compound=m.is_compound,
                cns_demand=m.cns_demand,
            )
            for m in movements
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/movements/{movement_id}", response_model=MovementResponse)
async def get_movement(
    movement_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get details for a specific movement."""
    movement = await db.get(Movement, movement_id)
    
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    
    return MovementResponse(
        id=movement.id,
        name=movement.name,
        primary_pattern=movement.primary_pattern,
        secondary_patterns=movement.secondary_patterns_json,
        primary_muscles=movement.primary_muscles_json,
        secondary_muscles=movement.secondary_muscles_json,
        primary_region=movement.primary_region,
        default_equipment=movement.default_equipment,
        complexity=movement.complexity,
        is_compound=movement.is_compound,
        cns_demand=movement.cns_demand,
    )
