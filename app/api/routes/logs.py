"""API routes for workout logging."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.config.settings import get_settings
from app.models import (
    WorkoutLog,
    TopSetLog,
    SorenessLog,
    RecoverySignal,
    PatternExposure,
    Session,
    Movement,
    RecoverySource,
)
from app.schemas.logging import (
    WorkoutLogCreate,
    WorkoutLogResponse,
    TopSetCreate,
    TopSetResponse,
    SorenessLogCreate,
    SorenessLogResponse,
    RecoverySignalCreate,
    RecoverySignalResponse,
    PatternExposureResponse,
    WorkoutLogListResponse,
)
from app.services.metrics import calculate_e1rm, E1RM_FORMULAS

router = APIRouter()
settings = get_settings()


def get_current_user_id() -> int:
    """Get current user ID (MVP: hardcoded default user)."""
    return settings.default_user_id


@router.post("/workouts", response_model=WorkoutLogResponse)
async def create_workout_log(
    log: WorkoutLogCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Log a completed workout with top sets and exercises.
    
    Calculates e1RM for each top set and records pattern exposure.
    """
    # Verify session exists and belongs to user's program
    session = await db.get(Session, log.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create workout log
    workout_log = WorkoutLog(
        user_id=user_id,
        session_id=log.session_id,
        date=log.log_date,
        started_at=log.started_at,
        ended_at=log.ended_at,
        perceived_exertion=log.perceived_exertion,
        energy_level=log.energy_level,
        adherence_percentage=log.adherence_percentage,
        coach_feedback_request=log.coach_feedback_request,
        exercises_completed_json=log.exercises_completed,
        notes=log.notes,
        enjoyment_rating=log.enjoyment_rating,
        feedback_tags=log.feedback_tags,
    )
    db.add(workout_log)
    await db.flush()
    
    # Process top sets
    top_sets_response = []
    for top_set in log.top_sets or []:
        # Get movement for e1RM calculation
        movement = await db.get(Movement, top_set.movement_id)
        if not movement:
            continue
        
        # Calculate e1RM using preferred formula
        e1rm = calculate_e1rm(
            weight=top_set.weight,
            reps=top_set.reps,
            formula=E1RM_FORMULAS.get(settings.default_e1rm_formula, "brzycki"),
        )
        
        top_set_log = TopSetLog(
            workout_log_id=workout_log.id,
            movement_id=top_set.movement_id,
            weight=top_set.weight,
            reps=top_set.reps,
            rpe=top_set.rpe,
            e1rm=e1rm,
            is_pr=False,  # Will be calculated separately
        )
        db.add(top_set_log)
        await db.flush()
        
        # Check if PR
        previous_best = await db.execute(
            select(func.max(TopSetLog.e1rm))
            .join(WorkoutLog)
            .where(
                and_(
                    WorkoutLog.user_id == user_id,
                    TopSetLog.movement_id == top_set.movement_id,
                    TopSetLog.id != top_set_log.id,
                )
            )
        )
        prev_max = previous_best.scalar()
        if prev_max is None or e1rm > prev_max:
            top_set_log.is_pr = True
        
        top_sets_response.append(TopSetResponse(
            id=top_set_log.id,
            movement_id=top_set.movement_id,
            movement_name=movement.name,
            weight=top_set.weight,
            reps=top_set.reps,
            rpe=top_set.rpe,
            e1rm=e1rm,
            is_pr=top_set_log.is_pr,
        ))
    
    # Record pattern exposure
    if log.exercises_completed:
        pattern_counts = {}
        for exercise in log.exercises_completed:
            movement_id = exercise.get("movement_id")
            if movement_id:
                movement = await db.get(Movement, movement_id)
                if movement:
                    pattern = movement.primary_pattern.value
                    if pattern not in pattern_counts:
                        pattern_counts[pattern] = {"sets": 0, "reps": 0}
                    pattern_counts[pattern]["sets"] += exercise.get("sets_completed", 0)
                    pattern_counts[pattern]["reps"] += exercise.get("reps_completed", 0)
        
        for pattern, counts in pattern_counts.items():
            exposure = PatternExposure(
                user_id=user_id,
                date=log.date,
                pattern=pattern,
                sets=counts["sets"],
                reps=counts["reps"],
                workout_log_id=workout_log.id,
            )
            db.add(exposure)
    
    await db.commit()
    
    return WorkoutLogResponse(
        id=workout_log.id,
        session_id=workout_log.session_id,
        log_date=workout_log.date,
        started_at=workout_log.started_at,
        ended_at=workout_log.ended_at,
        perceived_exertion=workout_log.perceived_exertion,
        energy_level=workout_log.energy_level,
        adherence_percentage=workout_log.adherence_percentage,
        coach_feedback_request=workout_log.coach_feedback_request,
        exercises_completed=workout_log.exercises_completed_json,
        notes=workout_log.notes,
        enjoyment_rating=workout_log.enjoyment_rating,
        feedback_tags=workout_log.feedback_tags,
        top_sets=top_sets_response,
    )


@router.get("/workouts", response_model=WorkoutLogListResponse)
async def list_workout_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    program_id: Optional[int] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List workout logs with optional filtering."""
    query = select(WorkoutLog).where(WorkoutLog.user_id == user_id)
    
    if start_date:
        query = query.where(WorkoutLog.date >= start_date)
    if end_date:
        query = query.where(WorkoutLog.date <= end_date)
    
    query = query.order_by(WorkoutLog.date.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = list(result.scalars().all())
    
    # Get total count
    count_query = select(func.count(WorkoutLog.id)).where(WorkoutLog.user_id == user_id)
    if start_date:
        count_query = count_query.where(WorkoutLog.date >= start_date)
    if end_date:
        count_query = count_query.where(WorkoutLog.date <= end_date)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Build responses
    log_responses = []
    for log in logs:
        # Get top sets for this log
        top_sets_result = await db.execute(
            select(TopSetLog).where(TopSetLog.workout_log_id == log.id)
        )
        top_sets = list(top_sets_result.scalars().all())
        
        top_set_responses = []
        for ts in top_sets:
            movement = await db.get(Movement, ts.movement_id)
            top_set_responses.append(TopSetResponse(
                id=ts.id,
                movement_id=ts.movement_id,
                movement_name=movement.name if movement else "Unknown",
                weight=ts.weight,
                reps=ts.reps,
                rpe=ts.rpe,
                e1rm=ts.e1rm,
                is_pr=ts.is_pr,
            ))
        
        log_responses.append(WorkoutLogResponse(
            id=log.id,
            session_id=log.session_id,
            log_date=log.date,
            started_at=log.started_at,
            ended_at=log.ended_at,
            perceived_exertion=log.perceived_exertion,
            energy_level=log.energy_level,
            adherence_percentage=log.adherence_percentage,
            coach_feedback_request=log.coach_feedback_request,
            exercises_completed=log.exercises_completed_json,
            notes=log.notes,
            enjoyment_rating=log.enjoyment_rating,
            feedback_tags=log.feedback_tags,
            top_sets=top_set_responses,
        ))
    
    return WorkoutLogListResponse(
        logs=log_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/workouts/{log_id}", response_model=WorkoutLogResponse)
async def get_workout_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get a specific workout log by ID."""
    log = await db.get(WorkoutLog, log_id)
    
    if not log or log.user_id != user_id:
        raise HTTPException(status_code=404, detail="Workout log not found")
    
    # Get top sets
    top_sets_result = await db.execute(
        select(TopSetLog).where(TopSetLog.workout_log_id == log.id)
    )
    top_sets = list(top_sets_result.scalars().all())
    
    top_set_responses = []
    for ts in top_sets:
        movement = await db.get(Movement, ts.movement_id)
        top_set_responses.append(TopSetResponse(
            id=ts.id,
            movement_id=ts.movement_id,
            movement_name=movement.name if movement else "Unknown",
            weight=ts.weight,
            reps=ts.reps,
            rpe=ts.rpe,
            e1rm=ts.e1rm,
            is_pr=ts.is_pr,
        ))
    
    return WorkoutLogResponse(
        id=log.id,
        session_id=log.session_id,
        log_date=log.date,
        started_at=log.started_at,
        ended_at=log.ended_at,
        perceived_exertion=log.perceived_exertion,
        energy_level=log.energy_level,
        adherence_percentage=log.adherence_percentage,
        coach_feedback_request=log.coach_feedback_request,
        exercises_completed=log.exercises_completed_json,
        notes=log.notes,
        enjoyment_rating=log.enjoyment_rating,
        feedback_tags=log.feedback_tags,
        top_sets=top_set_responses,
    )


# Soreness logging
@router.post("/soreness", response_model=SorenessLogResponse)
async def create_soreness_log(
    log: SorenessLogCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Log muscle soreness for a body part."""
    soreness = SorenessLog(
        user_id=user_id,
        date=log.log_date,
        body_part=log.body_part,
        soreness_1_5=log.soreness_1_5,
        notes=log.notes,
    )
    db.add(soreness)
    await db.commit()
    
    return SorenessLogResponse(
        id=soreness.id,
        log_date=soreness.date,
        body_part=soreness.body_part,
        soreness_1_5=soreness.soreness_1_5,
        notes=soreness.notes,
    )


@router.get("/soreness", response_model=List[SorenessLogResponse])
async def list_soreness_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    body_part: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List soreness logs with optional filtering."""
    query = select(SorenessLog).where(SorenessLog.user_id == user_id)
    
    if start_date:
        query = query.where(SorenessLog.date >= start_date)
    if end_date:
        query = query.where(SorenessLog.date <= end_date)
    if body_part:
        query = query.where(SorenessLog.body_part == body_part)
    
    query = query.order_by(SorenessLog.date.desc()).limit(limit)
    
    result = await db.execute(query)
    logs = list(result.scalars().all())
    
    return [
        SorenessLogResponse(
            id=log.id,
            log_date=log.date,
            body_part=log.body_part,
            soreness_1_5=log.soreness_1_5,
            notes=log.notes,
        )
        for log in logs
    ]


# Recovery signals
@router.post("/recovery", response_model=RecoverySignalResponse)
async def create_recovery_signal(
    signal: RecoverySignalCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Log recovery signal from wearable or manual input."""
    recovery = RecoverySignal(
        user_id=user_id,
        date=signal.log_date,
        source=signal.source,
        sleep_score=signal.sleep_score,
        readiness=signal.readiness,
        hrv=signal.hrv,
        resting_hr=signal.resting_hr,
        raw_payload_json=signal.raw_payload,
    )
    db.add(recovery)
    await db.commit()
    
    return RecoverySignalResponse(
        id=recovery.id,
        log_date=recovery.date,
        source=recovery.source,
        sleep_score=recovery.sleep_score,
        readiness=recovery.readiness,
        hrv=recovery.hrv,
        resting_hr=recovery.resting_hr,
    )


@router.get("/recovery", response_model=List[RecoverySignalResponse])
async def list_recovery_signals(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    source: Optional[RecoverySource] = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List recovery signals with optional filtering."""
    query = select(RecoverySignal).where(RecoverySignal.user_id == user_id)
    
    if start_date:
        query = query.where(RecoverySignal.date >= start_date)
    if end_date:
        query = query.where(RecoverySignal.date <= end_date)
    if source:
        query = query.where(RecoverySignal.source == source)
    
    query = query.order_by(RecoverySignal.date.desc()).limit(limit)
    
    result = await db.execute(query)
    signals = list(result.scalars().all())
    
    return [
        RecoverySignalResponse(
            id=sig.id,
            log_date=sig.date,
            source=sig.source,
            sleep_score=sig.sleep_score,
            readiness=sig.readiness,
            hrv=sig.hrv,
            resting_hr=sig.resting_hr,
        )
        for sig in signals
    ]


@router.get("/recovery/latest", response_model=RecoverySignalResponse)
async def get_latest_recovery(
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get the latest recovery signal, optionally for a specific date."""
    query = select(RecoverySignal).where(RecoverySignal.user_id == user_id)
    
    if target_date:
        query = query.where(RecoverySignal.date == target_date)
    
    query = query.order_by(RecoverySignal.created_at.desc()).limit(1)
    
    result = await db.execute(query)
    signal = result.scalar_one_or_none()
    
    if not signal:
        raise HTTPException(status_code=404, detail="No recovery signal found")
    
    return RecoverySignalResponse(
        id=signal.id,
        log_date=signal.date,
        source=signal.source,
        sleep_score=signal.sleep_score,
        readiness=signal.readiness,
        hrv=signal.hrv,
        resting_hr=signal.resting_hr,
    )


# Dashboard stats
@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Get aggregated stats for the dashboard.
    
    Returns workout count, streak, heaviest lift, total volume, etc.
    """
    from datetime import timedelta
    from sqlalchemy import desc
    
    today = date.today()
    month_start = today.replace(day=1)
    
    # Total workouts
    total_workouts_result = await db.execute(
        select(func.count(WorkoutLog.id)).where(WorkoutLog.user_id == user_id)
    )
    total_workouts = total_workouts_result.scalar() or 0
    
    # Workouts this month
    month_workouts_result = await db.execute(
        select(func.count(WorkoutLog.id)).where(
            and_(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date >= month_start
            )
        )
    )
    workouts_this_month = month_workouts_result.scalar() or 0
    
    # Calculate week streak (consecutive weeks with at least one workout)
    # Get all workout dates
    dates_result = await db.execute(
        select(WorkoutLog.date)
        .where(WorkoutLog.user_id == user_id)
        .order_by(desc(WorkoutLog.date))
    )
    workout_dates = [row[0] for row in dates_result.fetchall()]
    
    week_streak = 0
    if workout_dates:
        # Get current week's Monday
        current_week_monday = today - timedelta(days=today.weekday())
        checking_week = current_week_monday
        
        while True:
            week_end = checking_week + timedelta(days=6)
            has_workout = any(
                checking_week <= d <= week_end for d in workout_dates
            )
            if has_workout:
                week_streak += 1
                checking_week -= timedelta(days=7)
            else:
                break
    
    # Heaviest lift (by e1RM)
    heaviest_result = await db.execute(
        select(TopSetLog, Movement)
        .join(WorkoutLog)
        .join(Movement, TopSetLog.movement_id == Movement.id)
        .where(WorkoutLog.user_id == user_id)
        .order_by(desc(TopSetLog.e1rm_value))
        .limit(1)
    )
    heaviest_row = heaviest_result.first()
    heaviest_lift = None
    if heaviest_row:
        top_set, movement = heaviest_row
        heaviest_lift = {
            "weight": top_set.weight,
            "movement": movement.name,
            "e1rm": top_set.e1rm_value,
        }
    
    # Longest workout (by duration)
    longest_result = await db.execute(
        select(WorkoutLog)
        .where(
            and_(
                WorkoutLog.user_id == user_id,
                WorkoutLog.actual_duration_minutes.isnot(None),
            )
        )
        .order_by(
            desc(WorkoutLog.actual_duration_minutes)
        )
        .limit(1)
    )
    longest_workout = longest_result.scalar_one_or_none()
    longest_duration = None
    if longest_workout and longest_workout.actual_duration_minutes:
        longest_duration = {
            "minutes": longest_workout.actual_duration_minutes,
            "date": longest_workout.date.isoformat() if longest_workout.date else None,
        }
    
    # Total volume this month (sum of weight * reps for all top sets)
    volume_result = await db.execute(
        select(func.sum(TopSetLog.weight * TopSetLog.reps))
        .join(WorkoutLog)
        .where(
            and_(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date >= month_start
            )
        )
    )
    total_volume = volume_result.scalar() or 0
    
    # Note: adherence_percentage field doesn't exist in WorkoutLog model yet
    # TODO: Add adherence tracking when workout logging is implemented
    
    return {
        "total_workouts": total_workouts,
        "workouts_this_month": workouts_this_month,
        "week_streak": week_streak,
        "heaviest_lift": heaviest_lift,
        "longest_workout": longest_duration,
        "total_volume_this_month": round(total_volume, 1),
        "average_adherence": None,  # Not tracked yet
    }


# Pattern exposure
@router.get("/pattern-exposure", response_model=List[PatternExposureResponse])
async def list_pattern_exposure(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    pattern: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get pattern exposure history for tracking volume by movement pattern."""
    query = select(PatternExposure).where(PatternExposure.user_id == user_id)
    
    if start_date:
        query = query.where(PatternExposure.date >= start_date)
    if end_date:
        query = query.where(PatternExposure.date <= end_date)
    if pattern:
        query = query.where(PatternExposure.pattern == pattern)
    
    query = query.order_by(PatternExposure.date.desc())
    
    result = await db.execute(query)
    exposures = list(result.scalars().all())
    
    return [
        PatternExposureResponse(
            id=exp.id,
            log_date=exp.date,
            pattern=exp.pattern,
            sets=exp.sets,
            reps=exp.reps,
        )
        for exp in exposures
    ]
