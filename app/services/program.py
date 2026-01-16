"""
ProgramService - Generates workout programs with microcycle structure and goal distribution.

Responsible for:
- Creating 8-12 week programs from split template + goal mix
- Distributing goals across microcycles with weighting
- Generating microcycles with appropriate intensity profiles
- Creating session templates with optional sections (warmup, finisher, conditioning)
- Applying movement rule constraints and interference logic
"""

from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Program, Microcycle, Session, HeuristicConfig, User, Movement
)
from app.schemas.program import ProgramCreate
from app.models.enums import (
    Goal, SplitTemplate, SessionType, MicrocycleStatus, PersonaTone, PersonaAggression,
    ProgressionStyle
)
from app.services.interference import interference_service
from app.services.session_generator import session_generator


logger = logging.getLogger(__name__)


class ProgramService:
    """
    Generates and manages workout programs.
    
    A Program spans 8-12 weeks and contains Microcycles (1-2 weeks each).
    Each Microcycle contains Sessions (workout days).
    
    Goals are distributed across microcycles with weighting to balance
    focus across the user's objectives.
    """
    
    async def create_program(
        self,
        db: AsyncSession,
        user_id: int,
        request: ProgramCreate,
    ) -> Program:
        """
        Create a new 8-12 week program.
        
        Args:
            db: Database session
            user_id: User ID
            request: Program creation request (goals, duration_weeks, split_template, progression_style)
        
        Returns:
            Created Program with microcycles and sessions
        
        Raises:
            ValueError: If split template not found, goals empty, week_count invalid, interference conflict detected
        """
        # Validate week count
        if not (8 <= request.duration_weeks <= 12):
            raise ValueError("Program must be 8-12 weeks")
        
        # Extract goals from request (1-3 goals allowed)
        goals = request.goals  # List of GoalWeight objects
        if not (1 <= len(goals) <= 3):
            raise ValueError("1-3 goals required")
        
        # Pad goals list to 3 items if needed (with dummy goal of 0 weight)
        while len(goals) < 3:
            # Find a goal not in use
            used_goals = {g.goal for g in goals}
            unused_goal = next(g for g in Goal if g not in used_goals)
            goals.append(type(goals[0])(goal=unused_goal, weight=0))
        
        # Check for goal interference (only for goals with weight > 0)
        active_goals = [g.goal for g in goals if g.weight > 0]
        if len(active_goals) >= 2:
            # Pad active_goals to 3 for validation if needed
            validation_goals = active_goals[:]
            while len(validation_goals) < 3:
                validation_goals.append(active_goals[0])  # Duplicate first goal for validation
            
            is_valid, warnings = await interference_service.validate_goals(
                db, validation_goals[0], validation_goals[1], validation_goals[2]
            )
            if not is_valid:
                raise ValueError(f"Goal validation failed: {warnings}")
        
        # Load split template configuration with user's day preference
        split_config = await self._load_split_template(
            db, request.split_template, request.days_per_week
        )
        
        # Get user for defaults
        user = await db.get(User, user_id)
        
        # Determine progression style if not provided
        progression_style = request.progression_style
        if not progression_style:
            # Default based on experience level
            if user and user.experience_level == "beginner":
                progression_style = ProgressionStyle.SINGLE_PROGRESSION
            elif user and user.experience_level in ["advanced", "expert"]:
                progression_style = ProgressionStyle.WAVE_LOADING
            else:
                # Intermediate defaults to Double Progression
                progression_style = ProgressionStyle.DOUBLE_PROGRESSION
        
        # Determine persona settings (from request or user defaults)
        persona_tone = request.persona_tone or (user.persona_tone if user else PersonaTone.SUPPORTIVE)
        persona_aggression = request.persona_aggression or (user.persona_aggression if user else PersonaAggression.BALANCED)
        
        # Create program
        start_date = request.program_start_date or date.today()
        
        # Prepare disciplines JSON
        disciplines_json = None
        if request.disciplines:
            disciplines_json = [{"discipline": d.discipline, "weight": d.weight} for d in request.disciplines]
        
        program = Program(
            user_id=user_id,
            split_template=request.split_template,
            days_per_week=request.days_per_week,
            start_date=start_date,
            duration_weeks=request.duration_weeks,
            goal_1=goals[0].goal,
            goal_2=goals[1].goal,
            goal_3=goals[2].goal,
            goal_weight_1=goals[0].weight,
            goal_weight_2=goals[1].weight,
            goal_weight_3=goals[2].weight,
            progression_style=progression_style,
            deload_every_n_microcycles=request.deload_every_n_microcycles or 4,
            persona_tone=persona_tone,
            persona_aggression=persona_aggression,
            disciplines_json=disciplines_json,
            is_active=True,
        )
        db.add(program)
        await db.flush()  # Get program.id
        
        # Calculate number of microcycles (each microcycle = days_per_cycle from split)
        days_per_cycle = split_config.get("days_per_cycle", 7)
        total_days = request.duration_weeks * 7
        microcycle_count = total_days // days_per_cycle
        
        # Generate microcycles with sessions
        current_date = start_date
        deload_frequency = request.deload_every_n_microcycles or 4
        
        # Track active microcycle for session generation
        active_microcycle = None
        
        for mc_idx in range(microcycle_count):
            is_deload = ((mc_idx + 1) % deload_frequency == 0)
            
            microcycle = await self._create_microcycle(
                db,
                program_id=program.id,
                mc_index=mc_idx,
                start_date=current_date,
                split_config=split_config,
                is_deload=is_deload,
            )
            
            # Keep reference to active (first) microcycle
            if mc_idx == 0:
                active_microcycle = microcycle
            
            current_date += timedelta(days=days_per_cycle)
        
        await db.commit()
        await db.refresh(program)
        return program
    
    async def generate_active_microcycle_sessions(
        self,
        program_id: int,
    ) -> None:
        from app.db.database import async_session_maker

        async with async_session_maker() as db:
            program = await db.get(Program, program_id)
            if not program:
                return

            result = await db.execute(
                select(Microcycle).where(
                    Microcycle.program_id == program_id,
                    Microcycle.status == MicrocycleStatus.ACTIVE,
                )
            )
            microcycle = result.scalar_one_or_none()
            if not microcycle:
                return

        await self._generate_session_content_async(program_id, microcycle.id)
    
    async def _generate_session_content_async(
        self,
        program_id: int,
        microcycle_id: int,
    ) -> None:
        """
        Generate exercise content for all non-rest sessions in a microcycle.
        
        This method creates its own database sessions to avoid holding locks
        during long-running LLM calls.
        
        Args:
            program_id: ID of the program
            microcycle_id: ID of the microcycle to generate content for
        """
        from app.db.database import async_session_maker
        
        # Create a new DB session for reading program and sessions
        async with async_session_maker() as db:
            # Fetch program and microcycle
            program = await db.get(Program, program_id)
            microcycle = await db.get(Microcycle, microcycle_id)
            
            if not program or not microcycle:
                return
            
            # Get all sessions for this microcycle
            sessions_result = await db.execute(
                select(Session).where(Session.microcycle_id == microcycle.id)
                .order_by(Session.day_number)
            )
            sessions = list(sessions_result.scalars().all())
        
        # Track used movements to ensure variety
        used_movements = set()
        used_movement_groups = {}  # Track usage count by substitution_group
        used_main_patterns = {}    # Track main lift patterns by day
        used_accessory_movements = {}  # Track accessory movements by day
        
        # Track previous day's muscle volume for interference logic
        previous_day_volume = {}
        
        # Generate content for each session independently
        for session in sessions:
            # Skip recovery/rest sessions - they get default content
            if session.session_type == SessionType.RECOVERY:
                previous_day_volume = {}  # Recovery clears fatigue
                continue
            
            try:
                # Apply inter-session interference rules for main lift patterns
                async with async_session_maker() as db:
                    session = await self._apply_pattern_interference_rules(
                        db, session, used_main_patterns, microcycle
                    )
            except Exception as e:
                logger.error(
                    "Failed to apply pattern interference rules for session %s: %s",
                    session.id,
                    e,
                )
            
            try:
                # Generate and populate session with exercises
                # Each call creates its own DB session
                current_volume = await session_generator.populate_session_by_id(
                    session.id,
                    program_id,
                    microcycle_id,
                    used_movements=list(used_movements),
                    used_movement_groups=dict(used_movement_groups),
                    used_accessory_movements=dict(used_accessory_movements),
                    previous_day_volume=previous_day_volume,
                )
            except Exception as e:
                logger.error(
                    "Failed to generate content for session %s: %s",
                    session.id,
                    e,
                )
                
                # Robust Fallback: Mark session as failed but "content present" so spinner stops
                try:
                    async with async_session_maker() as db:
                        failed_session = await db.get(Session, session.id)
                        if failed_session:
                            failed_session.coach_notes = f"Generation failed: {str(e)}. Please regenerate."
                            # Add placeholder content to satisfy frontend hasContent check
                            failed_session.main_json = [{
                                "movement": "Generation Error",
                                "sets": 0,
                                "reps": "0",
                                "rpe": "0",
                                "rest": "0", 
                                "notes": "An error occurred during generation."
                            }]
                            db.add(failed_session)
                            await db.commit()
                except Exception as fallback_error:
                    logger.error(f"Failed to apply fallback for session {session.id}: {fallback_error}")

                # Skip tracking for this session so others can still be generated
                previous_day_volume = {}
                continue
            
            # Update previous volume for next iteration
            previous_day_volume = current_volume
            
            # Track used movements and movement groups
            if current_volume:
                # Re-fetch session to get updated content
                async with async_session_maker() as db:
                    updated_session = await db.get(Session, session.id)
                    if updated_session:
                        # Track individual movements
                        session_movements = []
                        main_patterns_used = []
                        accessory_movements_used = []
                        
                        if updated_session.main_json:
                            for ex in updated_session.main_json:
                                if ex.get("movement"):
                                    session_movements.append(ex["movement"])
                        if updated_session.accessory_json:
                            for ex in updated_session.accessory_json:
                                if ex.get("movement"):
                                    session_movements.append(ex["movement"])
                                    accessory_movements_used.append(ex["movement"])
                        if updated_session.finisher_json:
                            if updated_session.finisher_json.get("exercises"):
                                for ex in updated_session.finisher_json["exercises"]:
                                    if ex.get("movement"):
                                        session_movements.append(ex["movement"])
                                        # Treat finisher as accessory for interference
                                        accessory_movements_used.append(ex["movement"])
                        
                        # Update tracking sets
                        for movement_name in session_movements:
                            used_movements.add(movement_name)
                        
                        # Track main lift patterns for this session
                        if updated_session.intent_tags:
                            main_patterns_used = updated_session.intent_tags[:2]
                            used_main_patterns[session.day_number] = main_patterns_used
                        
                        # Track accessory movements for this session
                        used_accessory_movements[session.day_number] = accessory_movements_used
                        
                        # Update movement group usage counts
                        await self._update_movement_group_usage(
                            db, session_movements, used_movement_groups
                        )
    
    async def _apply_pattern_interference_rules(
        self,
        db: AsyncSession,
        session: Session,
        used_main_patterns: dict[int, list[str]],
        microcycle: Microcycle,
    ) -> Session:
        """
        Apply inter-session interference rules for main lift patterns.
        
        Rules:
        1. No same main pattern on consecutive days (even with rest day between)
        2. No same main pattern on back-to-back training days
        3. Prioritize pattern diversity: squat -> hinge -> lunge rotation for lower body
        4. Enforce minimum 2-day gap for same main pattern
        
        Args:
            db: Database session
            session: Session to apply rules to
            used_main_patterns: Dict mapping day_number to list of main patterns used
            microcycle: Parent microcycle
            
        Returns:
            Session with updated intent_tags based on interference rules
        """
        if session.session_type == SessionType.RECOVERY:
            return session
        
        current_day = session.day_number
        current_patterns = session.intent_tags or []
        
        # Get all training days in this microcycle for context
        training_days = sorted([day for day, patterns in used_main_patterns.items() if patterns])
        
        # Define pattern alternatives for intelligent substitution
        pattern_alternatives = {
            # Lower body pattern rotation
            "squat": ["hinge", "lunge"],
            "hinge": ["squat", "lunge"], 
            "lunge": ["squat", "hinge"],
            
            # Upper body pattern rotation
            "horizontal_push": ["vertical_push"],
            "vertical_push": ["horizontal_push"],
            "horizontal_pull": ["vertical_pull"],
            "vertical_pull": ["horizontal_pull"],
        }
        
        # Check for pattern conflicts and resolve them
        conflicting_patterns = []
        for pattern in current_patterns[:2]:  # Only check main patterns (first 2)
            if self._has_pattern_conflict(pattern, current_day, used_main_patterns):
                conflicting_patterns.append(pattern)
        
        # Replace conflicting patterns with alternatives
        if conflicting_patterns:
            new_patterns = current_patterns.copy()
            
            for i, pattern in enumerate(current_patterns[:2]):
                if pattern in conflicting_patterns:
                    # Find alternative pattern
                    alternative = self._find_alternative_pattern(
                        pattern, current_day, used_main_patterns, pattern_alternatives
                    )
                    if alternative:
                        new_patterns[i] = alternative
                        logger.info(
                            f"Day {current_day}: Replaced conflicting pattern '{pattern}' "
                            f"with '{alternative}' due to interference rules"
                        )
            
            # Update session intent_tags
            session.intent_tags = new_patterns
            db.add(session)
            await db.flush()
        
        return session
    
    def _has_pattern_conflict(
        self,
        pattern: str,
        current_day: int,
        used_main_patterns: dict[int, list[str]],
    ) -> bool:
        """
        Check if a pattern conflicts with interference rules.
        
        Args:
            pattern: Pattern to check (e.g., "squat")
            current_day: Current day number
            used_main_patterns: Dict of day -> patterns used
            
        Returns:
            True if pattern conflicts with interference rules
        """
        # Rule 1: No same pattern on consecutive training days
        prev_day = current_day - 1
        if prev_day in used_main_patterns:
            prev_patterns = used_main_patterns[prev_day][:2]  # Main patterns only
            if pattern in prev_patterns:
                return True
        
        # Rule 2: No same pattern within 2 days (even with rest day between)
        for check_day in range(max(1, current_day - 2), current_day):
            if check_day in used_main_patterns:
                check_patterns = used_main_patterns[check_day][:2]
                if pattern in check_patterns:
                    return True
        
        # Rule 3: Limit pattern usage to max 2 times per week (7 days)
        pattern_count = 0
        week_start = max(1, current_day - 6)
        for check_day in range(week_start, current_day + 1):
            if check_day in used_main_patterns:
                check_patterns = used_main_patterns[check_day][:2]
                if pattern in check_patterns:
                    pattern_count += 1
        
        if pattern_count >= 2:  # Already used twice this week
            return True
        
        return False
    
    def _find_alternative_pattern(
        self,
        original_pattern: str,
        current_day: int,
        used_main_patterns: dict[int, list[str]],
        pattern_alternatives: dict[str, list[str]],
    ) -> str | None:
        """
        Find an alternative pattern that doesn't conflict with interference rules.
        
        Args:
            original_pattern: Pattern that conflicts
            current_day: Current day number
            used_main_patterns: Dict of day -> patterns used
            pattern_alternatives: Dict of pattern -> list of alternatives
            
        Returns:
            Alternative pattern or None if no suitable alternative found
        """
        alternatives = pattern_alternatives.get(original_pattern, [])
        
        for alternative in alternatives:
            if not self._has_pattern_conflict(alternative, current_day, used_main_patterns):
                return alternative
        
        # Fallback: try all lower body patterns if original was lower body
        lower_body_patterns = ["squat", "hinge", "lunge"]
        upper_body_patterns = ["horizontal_push", "vertical_push", "horizontal_pull", "vertical_pull"]
        
        if original_pattern in lower_body_patterns:
            for pattern in lower_body_patterns:
                if pattern != original_pattern and not self._has_pattern_conflict(
                    pattern, current_day, used_main_patterns
                ):
                    return pattern
        elif original_pattern in upper_body_patterns:
            for pattern in upper_body_patterns:
                if pattern != original_pattern and not self._has_pattern_conflict(
                    pattern, current_day, used_main_patterns
                ):
                    return pattern
        
        return None
    
    async def _update_movement_group_usage(
        self,
        db: AsyncSession,
        session_movements: list[str],
        used_movement_groups: dict[str, int],
    ) -> None:
        """
        Update movement group usage counts for variety tracking.
        
        Args:
            db: Database session
            session_movements: List of movement names used in this session
            used_movement_groups: Dict tracking usage count by substitution_group
        """
        if not session_movements:
            return
        
        # Get movement objects to access substitution_group
        movements_result = await db.execute(
            select(Movement).where(Movement.name.in_(session_movements))
        )
        movements = {m.name: m for m in movements_result.scalars().all()}
        
        # Update group usage counts
        for movement_name in session_movements:
            movement = movements.get(movement_name)
            if movement and movement.substitution_group:
                group = movement.substitution_group
                used_movement_groups[group] = used_movement_groups.get(group, 0) + 1
    
    async def _create_microcycle(
        self,
        db: AsyncSession,
        program_id: int,
        mc_index: int,
        start_date: date,
        split_config: Dict[str, Any],
        is_deload: bool = False,
    ) -> Microcycle:
        """
        Create a microcycle with sessions based on split template.
        
        Args:
            db: Database session
            program_id: Parent program ID
            mc_index: Microcycle index (0-based)
            start_date: Microcycle start date
            split_config: Split template configuration from heuristics
            is_deload: Whether this is a deload microcycle
        
        Returns:
            Created Microcycle
        """
        days_per_cycle = split_config.get("days_per_cycle", 7)
        structure = split_config.get("structure", [])
        
        # First microcycle is active, others are planned
        status = MicrocycleStatus.ACTIVE if mc_index == 0 else MicrocycleStatus.PLANNED
        
        microcycle = Microcycle(
            program_id=program_id,
            sequence_number=mc_index + 1,  # 1-indexed
            start_date=start_date,
            length_days=days_per_cycle,
            status=status,
            is_deload=is_deload,
        )
        db.add(microcycle)
        await db.flush()  # Get microcycle.id
        
        # Create sessions from split template structure
        for day_def in structure:
            day_num = day_def.get("day", 1)
            day_type = day_def.get("type", "rest")
            focus_patterns = day_def.get("focus", [])
            
            # Calculate session date
            session_date = start_date + timedelta(days=day_num - 1)
            
            # Map day type to SessionType enum
            session_type = self._map_day_type_to_session_type(day_type)
            
            # Create session (even for rest days - they can have recovery activities)
            session = Session(
                microcycle_id=microcycle.id,
                date=session_date,
                day_number=day_num,
                session_type=session_type,
                intent_tags=focus_patterns,
            )
            db.add(session)
        
        return microcycle
    
    async def _load_split_template(
        self, db: AsyncSession, template: SplitTemplate, days_per_week: int
    ) -> Dict[str, Any]:
        """
        Load split template configuration from heuristic configs.
        
        Args:
            db: Database session
            template: SplitTemplate enum value
            days_per_week: User's training frequency preference (2-7)
        
        Returns:
            Split template configuration dict
        """
        # ALWAYS use dynamic generation for user-specified days_per_week
        # This ensures user preferences override any heuristic configs
        return self._get_default_split_template(template, days_per_week)
    
    def _get_default_split_template(
        self, template: SplitTemplate, days_per_week: int
    ) -> Dict[str, Any]:
        """
        Return default split template structure adapted to user's training frequency.
        
        Args:
            template: Split template type
            days_per_week: User's requested training days (2-7)
        
        Returns:
            Split configuration with structure adapted to days_per_week
        """
        if template == SplitTemplate.FULL_BODY:
            return self._generate_full_body_structure(days_per_week)
            
        elif template == SplitTemplate.UPPER_LOWER:
            # Default 4-day Upper/Lower
            return {
                "days_per_cycle": 7,
                "structure": [
                    {"day": 1, "type": "upper", "focus": ["horizontal_push", "horizontal_pull"]},
                    {"day": 2, "type": "lower", "focus": ["squat", "hinge"]},
                    {"day": 3, "type": "rest"},
                    {"day": 4, "type": "upper", "focus": ["vertical_push", "vertical_pull"]},
                    {"day": 5, "type": "lower", "focus": ["squat", "hinge"]},
                    {"day": 6, "type": "rest"},
                    {"day": 7, "type": "rest"},
                ],
                "training_days": 4,
                "rest_days": 3,
            }
            
        elif template == SplitTemplate.PPL:
            # Default 6-day PPL
            return {
                "days_per_cycle": 7,
                "structure": [
                    {"day": 1, "type": "push", "focus": ["horizontal_push", "vertical_push"]},
                    {"day": 2, "type": "pull", "focus": ["horizontal_pull", "vertical_pull"]},
                    {"day": 3, "type": "legs", "focus": ["squat", "hinge"]},
                    {"day": 4, "type": "rest"},
                    {"day": 5, "type": "push", "focus": ["horizontal_push", "vertical_push"]},
                    {"day": 6, "type": "pull", "focus": ["horizontal_pull", "vertical_pull"]},
                    {"day": 7, "type": "legs", "focus": ["squat", "hinge"]},
                ],
                "training_days": 6,
                "rest_days": 1,
            }
            
        elif template == SplitTemplate.HYBRID:
            return {
                "days_per_cycle": 7,
                "structure": [
                    {"day": 1, "type": "full_body", "focus": ["squat", "horizontal_push"]},
                    {"day": 2, "type": "rest"},
                    {"day": 3, "type": "full_body", "focus": ["hinge", "vertical_pull"]},
                    {"day": 4, "type": "rest"},
                    {"day": 5, "type": "full_body", "focus": ["lunge", "horizontal_pull"]},
                    {"day": 6, "type": "rest"},
                    {"day": 7, "type": "rest"},
                ],
                "training_days": 3,
                "rest_days": 4,
            }
            
        # Fallback to Full Body if unknown
        return self._generate_full_body_structure(days_per_week)
    
    def _generate_full_body_structure(self, days_per_week: int) -> Dict[str, Any]:
        """
        Generate full body split structure adapted to user's training frequency.
        
        Args:
            days_per_week: Requested training days (2-7)
        
        Returns:
            Split configuration dict with structure for the week
        """
        # Pattern rotation for variety
        focus_patterns = [
            ["squat", "horizontal_push", "horizontal_pull"],
            ["hinge", "vertical_push", "vertical_pull"],
            ["lunge", "horizontal_push", "vertical_pull"],
            ["hinge", "vertical_push", "horizontal_pull"],
        ]
        
        # Generate structure based on days_per_week
        structure = []
        training_day_count = 0
        
        if days_per_week == 2:
            # Days 1, 4 training, rest between
            structure = [
                {"day": 1, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 2, "type": "rest"},
                {"day": 3, "type": "rest"},
                {"day": 4, "type": "full_body", "focus": focus_patterns[1]},
                {"day": 5, "type": "rest"},
                {"day": 6, "type": "rest"},
                {"day": 7, "type": "rest"},
            ]
            training_day_count = 2
        elif days_per_week == 3:
            # Days 1, 3, 5 training
            structure = [
                {"day": 1, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 2, "type": "rest"},
                {"day": 3, "type": "full_body", "focus": focus_patterns[1]},
                {"day": 4, "type": "rest"},
                {"day": 5, "type": "full_body", "focus": focus_patterns[2]},
                {"day": 6, "type": "rest"},
                {"day": 7, "type": "rest"},
            ]
            training_day_count = 3
        elif days_per_week == 4:
            # Days 1, 3, 5, 6 training
            structure = [
                {"day": 1, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 2, "type": "rest"},
                {"day": 3, "type": "full_body", "focus": focus_patterns[1]},
                {"day": 4, "type": "rest"},
                {"day": 5, "type": "full_body", "focus": focus_patterns[2]},
                {"day": 6, "type": "full_body", "focus": focus_patterns[3]},
                {"day": 7, "type": "rest"},
            ]
            training_day_count = 4
        elif days_per_week == 5:
            # Days 1, 2, 4, 5, 7 training
            structure = [
                {"day": 1, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 2, "type": "full_body", "focus": focus_patterns[1]},
                {"day": 3, "type": "rest"},
                {"day": 4, "type": "full_body", "focus": focus_patterns[2]},
                {"day": 5, "type": "full_body", "focus": focus_patterns[3]},
                {"day": 6, "type": "rest"},
                {"day": 7, "type": "full_body", "focus": focus_patterns[2]},
            ]
            training_day_count = 5
        elif days_per_week == 6:
            # All days except day 4
            structure = [
                {"day": 1, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 2, "type": "full_body", "focus": focus_patterns[1]},
                {"day": 3, "type": "full_body", "focus": focus_patterns[2]},
                {"day": 4, "type": "rest"},
                {"day": 5, "type": "full_body", "focus": focus_patterns[3]},
                {"day": 6, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 7, "type": "full_body", "focus": focus_patterns[1]},
            ]
            training_day_count = 6
        else:  # days_per_week == 7
            # All days training
            structure = [
                {"day": 1, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 2, "type": "full_body", "focus": focus_patterns[1]},
                {"day": 3, "type": "full_body", "focus": focus_patterns[2]},
                {"day": 4, "type": "full_body", "focus": focus_patterns[3]},
                {"day": 5, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 6, "type": "full_body", "focus": focus_patterns[1]},
                {"day": 7, "type": "full_body", "focus": focus_patterns[2]},
            ]
            training_day_count = 7
        
        return {
            "days_per_cycle": 7,
            "structure": structure,
            "training_days": training_day_count,
            "rest_days": 7 - training_day_count,
        }
    
    def _map_day_type_to_session_type(self, day_type: str) -> SessionType:
        """
        Map split template day type to SessionType enum.
        """
        mapping = {
            "upper": SessionType.UPPER,
            "lower": SessionType.LOWER,
            "push": SessionType.PUSH,
            "pull": SessionType.PULL,
            "legs": SessionType.LEGS,
            "full_body": SessionType.FULL_BODY,
            "cardio": SessionType.CARDIO,
            "mobility": SessionType.MOBILITY,
            "rest": SessionType.RECOVERY,
            "recovery": SessionType.RECOVERY,
        }
        return mapping.get(day_type.lower(), SessionType.CUSTOM)
    
    async def get_program(
        self,
        db: AsyncSession,
        program_id: int,
        user_id: int,
    ) -> Optional[Program]:
        """
        Retrieve a program with all microcycles and sessions.
        
        Args:
            db: Database session
            program_id: Program ID
            user_id: User ID
        
        Returns:
            Program object or None if not found
        """
        result = await db.execute(
            select(Program).where(
                and_(
                    Program.id == program_id,
                    Program.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_programs(
        self,
        db: AsyncSession,
        user_id: int,
        status: Optional[str] = None,
    ) -> list:
        """
        List all programs for user, optionally filtered by status.
        
        Args:
            db: Database session
            user_id: User ID
            status: Optional ProgramStatus filter
        
        Returns:
            List of Program objects
        """
        query = select(Program).where(Program.user_id == user_id)
        if status:
            query = query.where(Program.status == status)
        
        result = await db.execute(query.order_by(Program.created_at.desc()))
        return list(result.scalars().all())


# Singleton instance
program_service = ProgramService()
