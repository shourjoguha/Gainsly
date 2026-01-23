"""API routes for user settings and configuration."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.config.settings import get_settings
from app.models import (
    User,
    UserProfile,
    UserSettings,
    UserMovementRule,
    UserEnjoyableActivity,
    Movement,
    MovementDiscipline,
    MovementEquipment,
    MovementMuscleMap,
    Muscle,
    Equipment,
    HeuristicConfig,
    MovementPattern,
)
from app.schemas.settings import (
    UserSettingsResponse,
    UserSettingsUpdate,
    UserProfileResponse,
    UserProfileUpdate,
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
from app.models.enums import MuscleRole

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


# User Profile
@router.get("/user/profile", response_model=UserProfileResponse)
async def get_user_profile(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get current user profile."""
    # Fetch User and UserProfile
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # UserProfile is a relationship, so it might be lazy loaded or we join it
    # But since we use async, we should probably eager load it or query it separately if lazy loading issues arise.
    # However, standard async access to relationships works if session is open.
    # Let's check if we need to explicitly query it.
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    
    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        experience_level=user.experience_level,
        persona_tone=user.persona_tone,
        persona_aggression=user.persona_aggression,
        date_of_birth=profile.date_of_birth if profile else None,
        sex=profile.sex if profile else None,
        height_cm=profile.height_cm if profile else None,
        discipline_preferences=profile.discipline_preferences if profile else None,
        discipline_experience=profile.discipline_experience if profile else None,
        scheduling_preferences=profile.scheduling_preferences if profile else None,
        long_term_goal_category=profile.long_term_goal_category if profile else None,
        long_term_goal_description=profile.long_term_goal_description if profile else None,
    )


@router.patch("/user/profile", response_model=UserProfileResponse)
async def update_user_profile(
    update: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Update user profile."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    
    # Update User fields
    update_data = update.model_dump(exclude_unset=True)
    user_fields = {"name", "experience_level", "persona_tone", "persona_aggression"}
    profile_fields = {
        "date_of_birth", "sex", "height_cm", 
        "discipline_preferences", "discipline_experience", "scheduling_preferences",
        "long_term_goal_category", "long_term_goal_description"
    }
    
    for field, value in update_data.items():
        if field in user_fields:
            setattr(user, field, value)
        elif field in profile_fields:
            setattr(profile, field, value)
            
    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)
    
    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        experience_level=user.experience_level,
        persona_tone=user.persona_tone,
        persona_aggression=user.persona_aggression,
        date_of_birth=profile.date_of_birth,
        sex=profile.sex,
        height_cm=profile.height_cm,
        discipline_preferences=profile.discipline_preferences,
        discipline_experience=profile.discipline_experience,
        scheduling_preferences=profile.scheduling_preferences,
        long_term_goal_category=profile.long_term_goal_category,
        long_term_goal_description=profile.long_term_goal_description,
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
    query = select(Movement).options(
        selectinload(Movement.disciplines),
        selectinload(Movement.equipment).selectinload(MovementEquipment.equipment),
        selectinload(Movement.muscle_maps).selectinload(MovementMuscleMap.muscle)
    )
    
    # Filter by user (system movements + user's movements)
    query = query.where((Movement.user_id.is_(None)) | (Movement.user_id == user_id))
    
    if pattern:
        query = query.where(Movement.pattern == pattern)
    if search:
        query = query.where(Movement.name.ilike(f"%{search}%"))
    if equipment:
        query = query.join(Movement.equipment).join(MovementEquipment.equipment).where(Equipment.name == equipment)
    
    # Get total
    from sqlalchemy import func
    count_query = select(func.count(Movement.id)).where(
        (Movement.user_id.is_(None)) | (Movement.user_id == user_id)
    )
    if pattern:
        count_query = count_query.where(Movement.pattern == pattern)
    if search:
        count_query = count_query.where(Movement.name.ilike(f"%{search}%"))
    if equipment:
        count_query = count_query.join(Movement.equipment).join(MovementEquipment.equipment).where(Equipment.name == equipment)
    
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
                pattern=m.pattern.value,
                primary_pattern=m.pattern,
                primary_muscle=m.primary_muscle.value if m.primary_muscle else None,
                primary_muscles=[m.primary_muscle.value] if m.primary_muscle else [],
                secondary_muscles=[
                    mm.muscle.slug for mm in m.muscle_maps 
                    if mm.role in [MuscleRole.SECONDARY, MuscleRole.STABILIZER] and mm.muscle
                ] if m.muscle_maps else [],
                primary_region=m.primary_region,
                compound=m.compound,
                is_compound=m.compound,
                skill_level=m.skill_level,
                cns_load=m.cns_load.value,
                metric_type=m.metric_type.value,
                is_complex_lift=m.is_complex_lift,
                is_unilateral=m.is_unilateral,
                substitution_group=m.substitution_group,
                description=m.description,
                user_id=m.user_id,
                disciplines=[d.discipline.value for d in m.disciplines] if m.disciplines else [],
                equipment=[e.equipment.name for e in m.equipment if e.equipment] if m.equipment else [],
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

    patterns = sorted({m.pattern.value for m in movements if m.pattern})
    regions = sorted({m.primary_region for m in movements if m.primary_region})
    
    # Get distinct disciplines for visible movements
    disc_query = select(MovementDiscipline.discipline).join(Movement).where(
        (Movement.user_id.is_(None)) | (Movement.user_id == user_id)
    ).distinct()
    disc_result = await db.execute(disc_query)
    disciplines = sorted([d.value for d in disc_result.scalars().all() if d])

    # Get distinct equipment for visible movements
    eq_query = select(Equipment.name).join(MovementEquipment).join(Movement).where(
        (Movement.user_id.is_(None)) | (Movement.user_id == user_id)
    ).distinct()
    eq_result = await db.execute(eq_query)
    equipment = sorted([e for e in eq_result.scalars().all() if e])

    # Get distinct secondary muscles for visible movements
    mus_query = select(Muscle.slug).join(MovementMuscleMap).join(Movement).where(
        (Movement.user_id.is_(None)) | (Movement.user_id == user_id),
        MovementMuscleMap.role.in_([MuscleRole.SECONDARY, MuscleRole.STABILIZER])
    ).distinct()
    mus_result = await db.execute(mus_query)
    secondary_muscles = sorted([m for m in mus_result.scalars().all() if m])

    types = ["compound", "accessory"]

    return MovementFiltersResponse(
        patterns=patterns,
        regions=regions,
        equipment=equipment,
        primary_disciplines=disciplines,
        secondary_muscles=secondary_muscles,
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
        compound=movement.compound,
        description=movement.description,
        user_id=user_id,
        # Defaults
        cns_load=movement.cns_load or "moderate",
        skill_level=movement.skill_level or "intermediate",
        metric_type=movement.metric_type or "reps",
    )
    
    db.add(new_movement)
    await db.flush()

    # Handle Secondary Muscles
    if movement.secondary_muscles:
        for muscle_enum in movement.secondary_muscles:
            # Find muscle by slug (assuming enum value == slug)
            muscle_slug = muscle_enum.value if hasattr(muscle_enum, 'value') else muscle_enum
            muscle_res = await db.execute(select(Muscle).where(Muscle.slug == muscle_slug))
            muscle = muscle_res.scalar_one_or_none()
            if muscle:
                mm = MovementMuscleMap(
                    movement_id=new_movement.id, 
                    muscle_id=muscle.id, 
                    role=MuscleRole.SECONDARY
                )
                db.add(mm)
    
    # Handle Equipment
    if movement.default_equipment:
        # Find or create equipment
        eq_name = movement.default_equipment
        eq_result = await db.execute(select(Equipment).where(Equipment.name == eq_name))
        eq = eq_result.scalar_one_or_none()
        if not eq:
            eq = Equipment(name=eq_name)
            db.add(eq)
            await db.flush()
        
        # Link
        me = MovementEquipment(movement_id=new_movement.id, equipment_id=eq.id)
        db.add(me)
    
    await db.commit()
    await db.refresh(new_movement)
    
    # Refresh relations
    query = select(Movement).where(Movement.id == new_movement.id).options(
        selectinload(Movement.disciplines),
        selectinload(Movement.equipment).selectinload(MovementEquipment.equipment),
        selectinload(Movement.muscle_maps).selectinload(MovementMuscleMap.muscle)
    )
    result = await db.execute(query)
    new_movement = result.scalar_one()
    
    return MovementResponse(
        id=new_movement.id,
        name=new_movement.name,
        pattern=new_movement.pattern.value,
        primary_pattern=new_movement.pattern,
        primary_muscle=new_movement.primary_muscle.value,
        primary_muscles=[new_movement.primary_muscle.value],
        secondary_muscles=[
            mm.muscle.slug for mm in new_movement.muscle_maps 
            if mm.role in [MuscleRole.SECONDARY, MuscleRole.STABILIZER] and mm.muscle
        ] if new_movement.muscle_maps else [],
        primary_region=new_movement.primary_region,
        default_equipment=new_movement.equipment[0].equipment.name if new_movement.equipment else None,
        complexity=new_movement.skill_level,
        skill_level=new_movement.skill_level,
        is_compound=new_movement.compound,
        cns_load=new_movement.cns_load.value,
        metric_type=new_movement.metric_type.value,
        is_complex_lift=new_movement.is_complex_lift,
        is_unilateral=new_movement.is_unilateral,
        substitution_group=new_movement.substitution_group,
        description=new_movement.description,
        user_id=new_movement.user_id,
        disciplines=[d.discipline.value for d in new_movement.disciplines] if new_movement.disciplines else [],
        equipment=[e.equipment.name for e in new_movement.equipment if e.equipment] if new_movement.equipment else [],
    )


@router.get("/movements/{movement_id}", response_model=MovementResponse)
async def get_movement(
    movement_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get details for a specific movement."""
    query = select(Movement).where(Movement.id == movement_id).options(
        selectinload(Movement.disciplines),
        selectinload(Movement.equipment).selectinload(MovementEquipment.equipment),
        selectinload(Movement.muscle_maps).selectinload(MovementMuscleMap.muscle)
    )
    result = await db.execute(query)
    movement = result.scalar_one_or_none()
    
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    
    return MovementResponse(
        id=movement.id,
        name=movement.name,
        pattern=movement.pattern.value if movement.pattern else None,
        primary_pattern=movement.pattern,
        primary_muscle=movement.primary_muscle.value if movement.primary_muscle else None,
        primary_muscles=[movement.primary_muscle.value] if movement.primary_muscle else [],
        secondary_muscles=[
            mm.muscle.slug for mm in movement.muscle_maps 
            if mm.role in [MuscleRole.SECONDARY, MuscleRole.STABILIZER] and mm.muscle
        ] if movement.muscle_maps else [],
        primary_region=movement.primary_region,
        default_equipment=movement.equipment[0].equipment.name if movement.equipment else None,
        complexity=movement.skill_level,
        skill_level=movement.skill_level,
        is_compound=movement.compound,
        cns_load=movement.cns_load.value if movement.cns_load else None,
        metric_type=movement.metric_type.value if movement.metric_type else None,
        is_complex_lift=movement.is_complex_lift,
        is_unilateral=movement.is_unilateral,
        substitution_group=movement.substitution_group,
        description=movement.description,
        user_id=movement.user_id,
        disciplines=[d.discipline.value for d in movement.disciplines] if movement.disciplines else [],
        equipment=[e.equipment.name for e in movement.equipment if e.equipment] if movement.equipment else [],
    )
