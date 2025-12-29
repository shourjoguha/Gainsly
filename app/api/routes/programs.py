"""API routes for program management."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.config.settings import get_settings
from app.models import (
    Program,
    Microcycle,
    Session,
    User,
    UserMovementRule,
    UserEnjoyableActivity,
    MicrocycleStatus,
)
from app.schemas.program import (
    ProgramCreate,
    ProgramResponse,
    MicrocycleResponse,
    SessionResponse,
    ProgramWithMicrocycleResponse,
)
from app.services.program import program_service
from app.services.interference import interference_service
from app.services.time_estimation import time_estimation_service

router = APIRouter()
settings = get_settings()


def get_current_user_id() -> int:
    """Get current user ID (MVP: hardcoded default user)."""
    return settings.default_user_id


@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    program_data: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Create a new training program.
    
    Requires:
    - 3 goals with weights summing to 10
    - Duration of 8-12 weeks
    - Split template selection
    - Progression style selection
    
    Optional:
    - Persona overrides
    - Movement rules
    - Enjoyable activities
    """
    # Get user for persona defaults
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate goals before creation
    is_valid, warnings = await interference_service.validate_goals(
        db,
        program_data.goals[0].goal,
        program_data.goals[1].goal,
        program_data.goals[2].goal,
    )
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Goal validation failed: {', '.join(warnings)}"
        )
    
    try:
        # Use ProgramService to create program with microcycles and sessions
        program = await program_service.create_program(db, user_id, program_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create movement rules if provided (post-program creation)
    if program_data.movement_rules:
        for rule in program_data.movement_rules:
            user_rule = UserMovementRule(
                user_id=user_id,
                movement_id=rule.movement_id,
                rule_type=rule.rule_type,
                cadence=rule.cadence,
                notes=rule.notes,
            )
            db.add(user_rule)
    
    # Create enjoyable activities if provided
    if program_data.enjoyable_activities:
        for activity in program_data.enjoyable_activities:
            user_activity = UserEnjoyableActivity(
                user_id=user_id,
                activity_type=activity.activity_type,
                custom_name=activity.custom_name,
                recommend_every_days=activity.recommend_every_days,
                enabled=True,
            )
            db.add(user_activity)
    
    if program_data.movement_rules or program_data.enjoyable_activities:
        await db.commit()
    
    return program


@router.get("/{program_id}", response_model=ProgramWithMicrocycleResponse)
async def get_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get program with active microcycle and upcoming sessions."""
    program = await db.get(Program, program_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    if program.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this program")
    
    # Get active microcycle
    active_microcycle_result = await db.execute(
        select(Microcycle)
        .where(
            and_(
                Microcycle.program_id == program_id,
                Microcycle.status == MicrocycleStatus.ACTIVE
            )
        )
        .options(selectinload(Microcycle.sessions))
    )
    active_microcycle = active_microcycle_result.scalar_one_or_none()
    
    # Get upcoming sessions (next 7 days)
    upcoming_sessions = []
    if active_microcycle:
        today = date.today()
        sessions_result = await db.execute(
            select(Session)
            .where(
                and_(
                    Session.microcycle_id == active_microcycle.id,
                    Session.date >= today
                )
            )
            .order_by(Session.date)
            .limit(7)
        )
        upcoming_sessions = list(sessions_result.scalars().all())
    
    # Convert sessions to response format with duration estimates
    session_responses = []
    for session in upcoming_sessions:
        # Estimate duration if not already calculated
        if not session.estimated_duration_minutes:
            try:
                duration_estimate = await time_estimation_service.estimate_session_duration(
                    db, user_id, session.id
                )
                session.estimated_duration_minutes = duration_estimate["total_minutes"]
                session.warmup_duration_minutes = duration_estimate["breakdown"]["warmup_minutes"]
                session.main_duration_minutes = duration_estimate["breakdown"]["main_minutes"]
                session.cooldown_duration_minutes = duration_estimate["breakdown"]["cooldown_minutes"]
            except Exception:
                # If estimation fails, use existing values or defaults
                pass
        
        session_responses.append(SessionResponse(
            id=session.id,
            microcycle_id=session.microcycle_id,
            session_date=session.date,
            day_number=session.day_number,
            session_type=session.session_type,
            intent_tags=session.intent_tags or [],
            warmup=session.warmup_json,
            main=session.main_json,
            accessory=session.accessory_json,
            finisher=session.finisher_json,
            cooldown=session.cooldown_json,
            estimated_duration_minutes=session.estimated_duration_minutes,
            warmup_duration_minutes=session.warmup_duration_minutes,
            main_duration_minutes=session.main_duration_minutes,
            accessory_duration_minutes=session.accessory_duration_minutes,
            finisher_duration_minutes=session.finisher_duration_minutes,
            cooldown_duration_minutes=session.cooldown_duration_minutes,
            coach_notes=session.coach_notes,
        ))
    
    return ProgramWithMicrocycleResponse(
        program=program,
        active_microcycle=active_microcycle,
        upcoming_sessions=session_responses,
    )


@router.get("", response_model=list[ProgramResponse])
async def list_programs(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """List all programs for the current user."""
    query = select(Program).where(Program.user_id == user_id)
    
    if active_only:
        query = query.where(Program.is_active == True)
    
    query = query.order_by(Program.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{program_id}/microcycles/generate-next", response_model=MicrocycleResponse)
async def generate_next_microcycle(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Generate the next microcycle for a program.
    
    This will:
    1. Mark the current active microcycle as complete
    2. Create a new microcycle
    3. Generate sessions for the new microcycle using LLM
    """
    program = await db.get(Program, program_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    if program.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get current active microcycle
    active_result = await db.execute(
        select(Microcycle)
        .where(
            and_(
                Microcycle.program_id == program_id,
                Microcycle.status == MicrocycleStatus.ACTIVE
            )
        )
    )
    current_microcycle = active_result.scalar_one_or_none()
    
    # Determine sequence number and start date
    if current_microcycle:
        current_microcycle.status = MicrocycleStatus.COMPLETE
        next_seq = current_microcycle.sequence_number + 1
        next_start = current_microcycle.start_date
        # Add current microcycle length
        from datetime import timedelta
        next_start = next_start + timedelta(days=current_microcycle.length_days)
    else:
        next_seq = 1
        next_start = program.start_date
    
    # Determine if this is a deload week
    is_deload = (next_seq % program.deload_every_n_microcycles == 0)
    
    # Create new microcycle
    new_microcycle = Microcycle(
        program_id=program_id,
        start_date=next_start,
        length_days=7,  # Default to 7, can be adjusted
        sequence_number=next_seq,
        status=MicrocycleStatus.ACTIVE,
        is_deload=is_deload,
    )
    db.add(new_microcycle)
    
    # TODO: Generate sessions using LLM
    # For now, just create the microcycle structure
    # Session generation will be implemented in a service
    
    await db.commit()
    await db.refresh(new_microcycle)
    
    return new_microcycle


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Delete a program (soft delete by deactivating)."""
    program = await db.get(Program, program_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    if program.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    program.is_active = False
    await db.commit()


@router.patch("/{program_id}/activate", response_model=ProgramResponse)
async def activate_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Activate a program (deactivates any other active programs)."""
    program = await db.get(Program, program_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    if program.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Deactivate other programs
    other_active = await db.execute(
        select(Program).where(
            and_(
                Program.user_id == user_id,
                Program.is_active == True,
                Program.id != program_id
            )
        )
    )
    for prog in other_active.scalars():
        prog.is_active = False
    
    program.is_active = True
    await db.commit()
    await db.refresh(program)
    
    return program
