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
    MovementCreate,
    MovementFiltersResponse,
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
        user_id=user_settings.user_id,
        active_e1rm_formula=user_settings.active_e1rm_formula,
        use_metric=user_settings.use_metric,
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
        user_id=user_settings.user_id,
        active_e1rm_formula=user_settings.active_e1rm_formula,
        use_metric=user_settings.use_metric,
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
        
        responses.append(MovementRuleResponse(
            id=rule.id,
            movement_id=rule.movement_id,
            movement_name=movement.name if movement else "Unknown",
            rule_type=rule.rule_type.value if rule.rule_type else None,
            cadence=rule.cadence.value if rule.cadence else None,
            notes=rule.notes,
        ))
    
    return responses


@router.post("/movement-rules", response_model=MovementRuleResponse)
async def create_movement_rule(
    rule: MovementRuleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Create a new movement rule (exclude, substitute, prefer)."""
    from app.models.enums import MovementRuleType, RuleCadence
    
    # Verify movement exists
    movement = await db.get(Movement, rule.movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    
    # Parse rule_type enum
    try:
        rule_type_enum = MovementRuleType[rule.rule_type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid rule_type: {rule.rule_type}")
    
    # Parse cadence enum if provided
    cadence_enum = RuleCadence.PER_MICROCYCLE
    if rule.cadence:
        try:
            cadence_enum = RuleCadence[rule.cadence.upper()]
        except KeyError:
            pass  # Use default
    
    movement_rule = UserMovementRule(
        user_id=user_id,
        movement_id=rule.movement_id,
        rule_type=rule_type_enum,
        cadence=cadence_enum,
        notes=rule.notes,
    )
    db.add(movement_rule)
    await db.commit()
    
    return MovementRuleResponse(
        id=movement_rule.id,
        movement_id=movement_rule.movement_id,
        movement_name=movement.name,
        rule_type=movement_rule.rule_type.value,
        cadence=movement_rule.cadence.value if movement_rule.cadence else None,
        notes=movement_rule.notes,
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
            user_id=act.user_id,
            activity_type=act.activity_type.value if act.activity_type else None,
            custom_name=act.custom_name,
            recommend_every_days=act.recommend_every_days,
            enabled=act.enabled,
            notes=act.notes,
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
    from app.models.enums import EnjoyableActivity as EnjoyableActivityEnum

    try:
        activity_type = EnjoyableActivityEnum(activity.activity_type)
    except ValueError:
        try:
            activity_type = EnjoyableActivityEnum[activity.activity_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid activity_type: {activity.activity_type}")

    new_activity = UserEnjoyableActivity(
        user_id=user_id,
        activity_type=activity_type,
        custom_name=activity.custom_name,
        recommend_every_days=activity.recommend_every_days,
        enabled=True,
        notes=activity.notes,
    )
    db.add(new_activity)
    await db.commit()
    
    return EnjoyableActivityResponse(
        id=new_activity.id,
        user_id=new_activity.user_id,
        activity_type=new_activity.activity_type.value if new_activity.activity_type else None,
        custom_name=new_activity.custom_name,
        recommend_every_days=new_activity.recommend_every_days,
        enabled=new_activity.enabled,
        notes=new_activity.notes,
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
    limit: int = Query(default=1000, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List available movements from the repository."""
    query = select(Movement)
    
    # Filter by user (system movements + user's movements)
    query = query.where((Movement.user_id.is_(None)) | (Movement.user_id == user_id))
    
    if pattern:
        query = query.where(Movement.pattern == pattern)
    if search:
        query = query.where(Movement.name.ilike(f"%{search}%"))
    
    # Get total
    from sqlalchemy import func
    count_query = select(func.count(Movement.id)).where(
        (Movement.user_id.is_(None)) | (Movement.user_id == user_id)
    )
    if pattern:
        count_query = count_query.where(Movement.pattern == pattern)
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
                primary_pattern=m.pattern,
                secondary_patterns=m.secondary_muscles,
                primary_muscles=[m.primary_muscle],
                secondary_muscles=m.secondary_muscles,
                primary_region=m.primary_region,
                default_equipment=m.equipment_tags[0] if m.equipment_tags else None,
                complexity=m.skill_level,
                is_compound=m.compound,
                cns_load=m.cns_load,
                user_id=m.user_id,
            )
            for m in movements
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/movements/filters", response_model=MovementFiltersResponse)
async def get_movement_filters(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Return distinct movement filters available to the current user.

    This endpoint is designed for frontend filter UIs so they always
    reflect whatever values exist in the movements table, while still
    respecting access control (system movements + this user's movements).
    """
    # Reuse the same visibility rules as list_movements
    query = select(Movement).where((Movement.user_id.is_(None)) | (Movement.user_id == user_id))
    result = await db.execute(query)
    movements = list(result.scalars().all())

    patterns = sorted({m.pattern for m in movements if m.pattern})
    regions = sorted({m.primary_region for m in movements if m.primary_region})
    disciplines = sorted({getattr(m, "primary_discipline", None) for m in movements if getattr(m, "primary_discipline", None)})

    equipment_set: set[str] = set()
    for m in movements:
        tags = getattr(m, "equipment_tags", None) or []
        for tag in tags:
            if tag:
                equipment_set.add(tag)

    types = ["compound", "accessory"]

    return MovementFiltersResponse(
        patterns=patterns,
        regions=regions,
        equipment=sorted(equipment_set),
        primary_disciplines=disciplines,
        types=types,
    )


@router.post("/movements", response_model=MovementResponse)
async def create_movement(
    movement: MovementCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Create a custom movement."""
    # Check if movement with same name exists
    existing = await db.execute(select(Movement).where(Movement.name.ilike(movement.name)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Movement with this name already exists")
    
    new_movement = Movement(
        name=movement.name,
        pattern=movement.pattern,
        primary_muscle=movement.primary_muscle or "other",
        primary_region=movement.primary_region or "full_body",
        secondary_muscles=movement.secondary_muscles or [],
        compound=movement.compound,
        description=movement.description,
        user_id=user_id,
        # Defaults
        cns_load=movement.cns_load or "moderate",
        skill_level=movement.skill_level or "intermediate",
        metric_type=movement.metric_type or "reps",
        equipment_tags=[movement.default_equipment] if movement.default_equipment else [],
    )
    
    db.add(new_movement)
    await db.commit()
    await db.refresh(new_movement)
    
    return MovementResponse(
        id=new_movement.id,
        name=new_movement.name,
        primary_pattern=new_movement.pattern,
        primary_muscles=[new_movement.primary_muscle],
        secondary_muscles=new_movement.secondary_muscles,
        primary_region=new_movement.primary_region,
        default_equipment=new_movement.equipment_tags[0] if new_movement.equipment_tags else None,
        complexity=new_movement.skill_level,
        is_compound=new_movement.compound,
        cns_load=new_movement.cns_load,
        metric_type=new_movement.metric_type,
        user_id=new_movement.user_id,
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
        primary_pattern=movement.pattern,
        secondary_patterns=movement.secondary_muscles,
        primary_muscles=[movement.primary_muscle],
        secondary_muscles=movement.secondary_muscles,
        primary_region=movement.primary_region,
        default_equipment=movement.equipment_tags[0] if movement.equipment_tags else None,
        complexity=movement.skill_level,
        is_compound=movement.compound,
        cns_load=movement.cns_load,
    )
