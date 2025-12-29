"""API routes for daily planning and adaptation with SSE streaming."""
import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.config.settings import get_settings
from app.models import (
    Program,
    Microcycle,
    Session,
    ConversationThread,
    ConversationTurn,
    SorenessLog,
    RecoverySignal,
    MicrocycleStatus,
    RecoverySource,
)
from app.schemas.daily import (
    DailyPlanResponse,
    AdaptationRequest,
    AdaptationResponse,
    AcceptPlanRequest,
    AcceptPlanResponse,
    AdaptedSessionPlan,
)
from app.schemas.program import SessionResponse
from app.llm import get_llm_provider, LLMConfig, Message, PromptBuilder

router = APIRouter()
settings = get_settings()


def get_current_user_id() -> int:
    """Get current user ID (MVP: hardcoded default user)."""
    return settings.default_user_id


@router.get("/{target_date}/plan", response_model=DailyPlanResponse)
async def get_daily_plan(
    target_date: date,
    program_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Get the planned session for a specific date.
    
    Returns the session from the active microcycle, or indicates if it's a rest day.
    """
    # Verify program belongs to user
    program = await db.get(Program, program_id)
    if not program or program.user_id != user_id:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Get active microcycle
    microcycle_result = await db.execute(
        select(Microcycle).where(
            and_(
                Microcycle.program_id == program_id,
                Microcycle.status == MicrocycleStatus.ACTIVE
            )
        )
    )
    microcycle = microcycle_result.scalar_one_or_none()
    
    if not microcycle:
        raise HTTPException(status_code=404, detail="No active microcycle found")
    
    # Get session for the date
    session_result = await db.execute(
        select(Session).where(
            and_(
                Session.microcycle_id == microcycle.id,
                Session.date == target_date
            )
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        # It's a rest day or no session planned
        return DailyPlanResponse(
            plan_date=target_date,
            session=None,
            is_rest_day=True,
            coach_message="Rest day - take it easy and recover!",
        )
    
    # Convert to response
    session_response = SessionResponse(
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
        coach_notes=session.coach_notes,
    )
    
    return DailyPlanResponse(
        plan_date=target_date,
        session=session_response,
        is_rest_day=False,
    )


@router.post("/{target_date}/adapt", response_model=AdaptationResponse)
async def adapt_session(
    target_date: date,
    request: AdaptationRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Adapt a session based on constraints and recovery status.
    
    Creates or continues a conversation thread for iterative refinement.
    """
    # Verify program belongs to user
    program = await db.get(Program, program_id=request.program_id)
    if not program or program.user_id != user_id:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Get or create conversation thread
    if request.thread_id:
        thread = await db.get(ConversationThread, request.thread_id)
        if not thread or thread.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        thread = ConversationThread(
            user_id=user_id,
            context_type="daily_adaptation",
            context_date=datetime.combine(target_date, datetime.min.time()),
            is_active=True,
        )
        db.add(thread)
        await db.flush()
    
    # Get current session if exists
    microcycle_result = await db.execute(
        select(Microcycle).where(
            and_(
                Microcycle.program_id == request.program_id,
                Microcycle.status == MicrocycleStatus.ACTIVE
            )
        )
    )
    microcycle = microcycle_result.scalar_one_or_none()
    
    original_session = None
    if microcycle:
        session_result = await db.execute(
            select(Session).where(
                and_(
                    Session.microcycle_id == microcycle.id,
                    Session.date == target_date
                )
            )
        )
        original_session = session_result.scalar_one_or_none()
    
    # Get recent soreness logs
    soreness_result = await db.execute(
        select(SorenessLog).where(
            and_(
                SorenessLog.user_id == user_id,
                SorenessLog.date >= target_date
            )
        ).order_by(SorenessLog.date.desc()).limit(5)
    )
    recent_soreness = list(soreness_result.scalars().all())
    
    # Get recent recovery signals
    recovery_result = await db.execute(
        select(RecoverySignal).where(
            and_(
                RecoverySignal.user_id == user_id,
                RecoverySignal.date == target_date
            )
        ).order_by(RecoverySignal.created_at.desc()).limit(1)
    )
    recovery_signal = recovery_result.scalar_one_or_none()
    
    # Build prompt for LLM
    prompt_builder = PromptBuilder()
    
    # Add program context
    prompt_builder.add_program_context({
        "goal_1": program.goal_1.value,
        "goal_2": program.goal_2.value,
        "goal_3": program.goal_3.value,
        "goal_weight_1": program.goal_weight_1,
        "goal_weight_2": program.goal_weight_2,
        "goal_weight_3": program.goal_weight_3,
        "split_template": program.split_template.value,
        "progression_style": program.progression_style.value,
        "duration_weeks": program.duration_weeks,
        "deload_every_n_microcycles": program.deload_every_n_microcycles,
    })
    
    # Add constraints
    constraints = {}
    if request.excluded_movements:
        constraints["excluded_movements"] = request.excluded_movements
    if request.excluded_patterns:
        constraints["excluded_patterns"] = request.excluded_patterns
    if request.focus_for_today:
        constraints["focus"] = request.focus_for_today
    if request.preference:
        constraints["preference"] = request.preference
    if request.time_available_minutes:
        constraints["time_available_minutes"] = request.time_available_minutes
    
    if constraints:
        prompt_builder.add_constraints(constraints)
    
    # Add recovery context
    soreness_data = [{"body_part": s.body_part, "soreness_1_5": s.soreness_1_5} for s in recent_soreness]
    recovery_data = None
    if recovery_signal:
        recovery_data = {
            "sleep_score": recovery_signal.sleep_score,
            "readiness": recovery_signal.readiness,
            "hrv": recovery_signal.hrv,
        }
    prompt_builder.add_recovery_context(soreness_data, recovery_data)
    
    # Build system prompt
    system_prompt = prompt_builder.build()
    
    # Build user message
    user_message = request.user_message or f"Adapt my session for {target_date}."
    if request.adherence_vs_optimality != "balanced":
        user_message += f" I prefer {request.adherence_vs_optimality} today."
    
    # Get conversation history
    turns_result = await db.execute(
        select(ConversationTurn)
        .where(ConversationTurn.thread_id == thread.id)
        .order_by(ConversationTurn.turn_number)
    )
    existing_turns = list(turns_result.scalars().all())
    
    # Build messages for LLM
    messages = [Message(role="system", content=system_prompt)]
    for turn in existing_turns:
        messages.append(Message(role=turn.role, content=turn.content))
    messages.append(Message(role="user", content=user_message))
    
    # Store user turn
    user_turn = ConversationTurn(
        thread_id=thread.id,
        turn_number=len(existing_turns) + 1,
        role="user",
        content=user_message,
    )
    db.add(user_turn)
    
    # Call LLM
    from app.llm.ollama_provider import ADAPTATION_RESPONSE_SCHEMA
    
    provider = get_llm_provider()
    config = LLMConfig(
        model=settings.ollama_model,
        temperature=0.7,
        json_schema=ADAPTATION_RESPONSE_SCHEMA,
    )
    
    try:
        response = await provider.chat(messages, config)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {str(e)}")
    
    # Parse response
    if response.structured_data:
        llm_response = response.structured_data
    else:
        # Try to parse from content
        try:
            llm_response = json.loads(response.content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse LLM response")
    
    # Store assistant turn
    assistant_turn = ConversationTurn(
        thread_id=thread.id,
        turn_number=len(existing_turns) + 2,
        role="assistant",
        content=response.content,
        structured_response_json=llm_response,
    )
    db.add(assistant_turn)
    
    await db.commit()
    
    # Build response
    adapted_plan = llm_response.get("adapted_plan", {})
    
    return AdaptationResponse(
        plan_date=target_date,
        original_session_type=original_session.session_type if original_session else None,
        adapted_plan=AdaptedSessionPlan(
            warmup=adapted_plan.get("warmup"),
            main=adapted_plan.get("main"),
            accessory=adapted_plan.get("accessory"),
            finisher=adapted_plan.get("finisher"),
            cooldown=adapted_plan.get("cooldown"),
            estimated_duration_minutes=adapted_plan.get("estimated_duration_minutes", 60),
            reasoning=adapted_plan.get("reasoning", ""),
            trade_offs=adapted_plan.get("trade_offs"),
        ),
        changes_made=llm_response.get("changes_made", []),
        reasoning=llm_response.get("reasoning", ""),
        trade_offs=llm_response.get("trade_offs"),
        alternative_suggestion=llm_response.get("alternative_suggestion"),
        follow_up_question=llm_response.get("follow_up_question"),
        thread_id=thread.id,
    )


@router.post("/{target_date}/adapt/stream")
async def adapt_session_stream(
    target_date: date,
    request: AdaptationRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Adapt a session with SSE streaming response.
    
    Returns a Server-Sent Events stream with incremental LLM output.
    """
    # Similar setup as adapt_session, but with streaming
    
    async def generate_sse():
        """Generate SSE events from LLM stream."""
        # Verify program
        program = await db.get(Program, request.program_id)
        if not program or program.user_id != user_id:
            yield f"data: {json.dumps({'error': 'Program not found'})}\n\n"
            return
        
        # Create conversation thread
        thread = ConversationThread(
            user_id=user_id,
            context_type="daily_adaptation",
            context_date=datetime.combine(target_date, datetime.min.time()),
            is_active=True,
        )
        db.add(thread)
        await db.flush()
        
        # Build prompt (simplified for streaming)
        prompt_builder = PromptBuilder()
        prompt_builder.add_program_context({
            "goal_1": program.goal_1.value,
            "goal_2": program.goal_2.value,
            "goal_3": program.goal_3.value,
            "goal_weight_1": program.goal_weight_1,
            "goal_weight_2": program.goal_weight_2,
            "goal_weight_3": program.goal_weight_3,
            "split_template": program.split_template.value,
            "progression_style": program.progression_style.value,
            "duration_weeks": program.duration_weeks,
            "deload_every_n_microcycles": program.deload_every_n_microcycles,
        })
        
        system_prompt = prompt_builder.build()
        user_message = request.user_message or f"Adapt my session for {target_date}."
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_message),
        ]
        
        # Stream from LLM
        provider = get_llm_provider()
        config = LLMConfig(
            model=settings.ollama_model,
            temperature=0.7,
            stream=True,
        )
        
        # Send thread_id first
        yield f"data: {json.dumps({'thread_id': thread.id})}\n\n"
        
        full_content = ""
        try:
            async for chunk in provider.chat_stream(messages, config):
                full_content += chunk.content
                yield f"data: {json.dumps({'content': chunk.content, 'done': chunk.done})}\n\n"
                
                if chunk.done:
                    # Store the conversation
                    user_turn = ConversationTurn(
                        thread_id=thread.id,
                        turn_number=1,
                        role="user",
                        content=user_message,
                    )
                    assistant_turn = ConversationTurn(
                        thread_id=thread.id,
                        turn_number=2,
                        role="assistant",
                        content=full_content,
                    )
                    db.add(user_turn)
                    db.add(assistant_turn)
                    await db.commit()
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/accept-plan", response_model=AcceptPlanResponse)
async def accept_plan(
    request: AcceptPlanRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Accept a plan from an adaptation conversation.
    
    This finalizes the conversation and optionally updates the session.
    """
    thread = await db.get(ConversationThread, request.thread_id)
    
    if not thread:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if thread.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if thread.final_plan_accepted:
        raise HTTPException(status_code=400, detail="Plan already accepted")
    
    # Get the last assistant turn with structured response
    turns_result = await db.execute(
        select(ConversationTurn)
        .where(
            and_(
                ConversationTurn.thread_id == thread.id,
                ConversationTurn.role == "assistant"
            )
        )
        .order_by(ConversationTurn.turn_number.desc())
        .limit(1)
    )
    last_turn = turns_result.scalar_one_or_none()
    
    if not last_turn or not last_turn.structured_response_json:
        raise HTTPException(status_code=400, detail="No plan to accept")
    
    # Mark thread as accepted
    thread.final_plan_accepted = True
    thread.is_active = False
    thread.accepted_plan_json = last_turn.structured_response_json.get("adapted_plan")
    
    await db.commit()
    
    return AcceptPlanResponse(
        success=True,
        message="Plan accepted successfully",
    )
