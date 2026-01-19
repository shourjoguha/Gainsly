"""
SessionGeneratorService - Generates workout session content using LLM.

Uses Ollama with llama3.1:8b to create exercise blocks for sessions
based on program goals, session type, and movement library.
"""

import asyncio
import json
import logging
import time
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.llm import get_llm_provider, LLMConfig, Message
from app.llm.prompts import JEROME_SYSTEM_PROMPT, build_optimized_session_prompt
from app.llm.ollama_provider import SESSION_PLAN_SCHEMA
from app.models import Movement, Session, Program, Microcycle, User, UserMovementRule, UserProfile
from app.models.enums import SessionType, MovementRuleType

logger = logging.getLogger(__name__)
settings = get_settings()


class SessionGeneratorService:
    """
    Generates workout session content using LLM.
    
    Takes session shells (with type and intent_tags) and populates them
    with warmup, main, accessory, finisher, and cooldown exercise blocks.
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 2.0  # seconds
    RETRY_BACKOFF_MULTIPLIER = 2.0
    MAX_RETRY_DELAY = 10.0  # seconds
    
    async def _call_llm_with_retry(
        self,
        provider,
        messages: list,
        config,
        session_id: int | None = None,
        session_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Call LLM with exponential backoff retry logic.
        
        Args:
            provider: LLM provider instance
            messages: List of messages for the LLM
            config: LLM configuration
            session_id: Optional session ID for logging context
            session_type: Optional session type for logging context
            
        Returns:
            Parsed JSON response from LLM
            
        Raises:
            Exception: After all retries exhausted
        """
        last_exception = None
        delay = self.INITIAL_RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                start_time = time.time()
                response = await provider.chat(messages, config)
                elapsed = time.time() - start_time
                
                # Parse response
                if response.structured_data:
                    content = response.structured_data
                else:
                    content = json.loads(response.content)
                
                # Log success
                if attempt > 0:
                    logger.info(
                        f"LLM call succeeded on attempt {attempt + 1}/{self.MAX_RETRIES} "
                        f"after {elapsed:.1f}s (session_id={session_id}, type={session_type})"
                    )
                
                return content
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(
                    f"LLM request timed out on attempt {attempt + 1}/{self.MAX_RETRIES} "
                    f"(session_id={session_id}, type={session_type}). "
                    f"Retrying in {delay:.1f}s..."
                )
                
            except httpx.ConnectError as e:
                last_exception = e
                logger.warning(
                    f"Cannot connect to Ollama on attempt {attempt + 1}/{self.MAX_RETRIES} "
                    f"(session_id={session_id}, type={session_type}). "
                    f"Base URL: {provider.base_url}. Retrying in {delay:.1f}s..."
                )
                
            except json.JSONDecodeError as e:
                last_exception = e
                content_preview = getattr(response, 'content', 'N/A')[:200] if 'response' in locals() else 'N/A'
                logger.warning(
                    f"LLM returned invalid JSON on attempt {attempt + 1}/{self.MAX_RETRIES} "
                    f"(session_id={session_id}, type={session_type}). "
                    f"Content preview: {content_preview}. Retrying in {delay:.1f}s..."
                )
                
            except httpx.HTTPStatusError as e:
                # Don't retry on HTTP errors (4xx/5xx from Ollama)
                logger.error(
                    f"Ollama returned HTTP {e.response.status_code} "
                    f"(session_id={session_id}, type={session_type}): {e.response.text[:200]}"
                )
                raise
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Unexpected error on attempt {attempt + 1}/{self.MAX_RETRIES} "
                    f"(session_id={session_id}, type={session_type}): "
                    f"{type(e).__name__}: {str(e)[:200]}. Retrying in {delay:.1f}s..."
                )
            
            # Don't sleep after last attempt
            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(delay)
                delay = min(delay * self.RETRY_BACKOFF_MULTIPLIER, self.MAX_RETRY_DELAY)
        
        # All retries exhausted
        logger.error(
            f"LLM call failed after {self.MAX_RETRIES} attempts "
            f"(session_id={session_id}, type={session_type}). "
            f"Last error: {type(last_exception).__name__}: {last_exception}"
        )
        raise last_exception
    
    async def generate_session_exercises(
        self,
        db: AsyncSession,
        session: Session,
        program: Program,
        microcycle: Microcycle,
        used_movements: list[str] | None = None,
        used_movement_groups: dict[str, int] | None = None,
        used_accessory_movements: dict[int, list[str]] | None = None,
        fatigued_muscles: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate exercise content for a session.
        
        Args:
            db: Database session
            session: Session model with type and intent_tags set
            program: Parent program with goals and settings
            microcycle: Parent microcycle with deload status
            used_movements: List of movements already used in this microcycle
            used_movement_groups: Dict tracking usage count by substitution_group
            used_accessory_movements: Dict mapping day_number to accessory movements used
            fatigued_muscles: List of muscles fatigued from previous session
            
        Returns:
            Dict with warmup, main, accessory, finisher, cooldown blocks
        """
        # Skip generation for rest/recovery sessions
        if session.session_type == SessionType.RECOVERY:
            return self._get_recovery_session_content()
        
        # Load movement library grouped by pattern
        movements_by_pattern = await self._load_movements_by_pattern(db)
        
        # Load user's movement rules (avoid, must include, prefer)
        movement_rules = await self._load_user_movement_rules(db, program.user_id)
        
        # Load user profile for advanced preferences
        user_profile = await db.get(UserProfile, program.user_id)
        discipline_preferences = user_profile.discipline_preferences if user_profile else None
        scheduling_preferences = user_profile.scheduling_preferences if user_profile else None
        
        # Build program context dict
        program_dict = {
            "goal_1": program.goal_1.value,
            "goal_2": program.goal_2.value,
            "goal_3": program.goal_3.value,
            "goal_weight_1": program.goal_weight_1,
            "goal_weight_2": program.goal_weight_2,
            "goal_weight_3": program.goal_weight_3,
            "split_template": program.split_template.value,
            "days_per_week": program.days_per_week,
            "progression_style": program.progression_style.value,
            "duration_weeks": program.duration_weeks,
            "deload_every_n_microcycles": program.deload_every_n_microcycles,
            "disciplines": program.disciplines_json,  # User's training style preferences
        }
        
        # Build the user prompt using optimized version
        user_prompt = build_optimized_session_prompt(
            program=program_dict,
            session_type=session.session_type.value,
            intent_tags=session.intent_tags or [],
            day_number=session.day_number,
            is_deload=microcycle.is_deload,
            microcycle_number=microcycle.sequence_number,
            movements_by_pattern=movements_by_pattern,
            movement_rules=movement_rules,
            used_movements=used_movements,
            used_movement_groups=used_movement_groups,
            used_accessory_movements=used_accessory_movements,
            fatigued_muscles=fatigued_muscles,
            discipline_preferences=discipline_preferences,
            scheduling_preferences=scheduling_preferences,
        )
        
        # Use optimized model configuration
        from app.llm.optimization import ModelOptimizer
        optimized_model_config = ModelOptimizer.get_optimized_config("standard")
        
        # Call LLM with retry logic
        provider = get_llm_provider()
        config = LLMConfig(
            model=settings.ollama_model,
            temperature=optimized_model_config["temperature"],  # Optimized temperature
            max_tokens=optimized_model_config["max_tokens"],    # Reduced token limit
            json_schema=SESSION_PLAN_SCHEMA,
        )
        
        messages = [
            Message(role="system", content=JEROME_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]
        
        try:
            content = await self._call_llm_with_retry(
                provider,
                messages,
                config,
                session_id=session.id,
                session_type=session.session_type.value,
            )
            
            # Validate and complete the session content
            content = self._validate_and_complete_session(content, session.session_type)
            
            # OPTIMIZATION: Use pattern-based warmup/cooldown with flexibility
            from app.llm.optimization import PromptCache
            
            # Enhance warmup with pattern-based suggestions if LLM didn't provide good warmup
            if not content.get("warmup") or len(content.get("warmup", [])) < 2:
                content["warmup"] = PromptCache.get_pattern_based_warmup(
                    session.intent_tags or [], session.session_type
                )
            
            # Enhance cooldown with pattern-based suggestions if LLM didn't provide good cooldown
            if not content.get("cooldown") or len(content.get("cooldown", [])) < 2:
                content["cooldown"] = PromptCache.get_pattern_based_cooldown(
                    session.intent_tags or []
                )
            
            return content
                
        except Exception as e:
            # All retries exhausted or non-retryable error
            logger.error(
                f"LLM generation failed for session {session.id} ({session.session_type.value}). "
                f"Using smart fallback. Error: {type(e).__name__}: {e}"
            )
            return self._get_smart_fallback_session_content(
                session.session_type,
                session.intent_tags or [],
                movements_by_pattern,
                used_movements=used_movements,
            )
    
    async def populate_session_by_id(
        self,
        session_id: int,
        program_id: int,
        microcycle_id: int,
        used_movements: list[str] | None = None,
        used_movement_groups: dict[str, int] | None = None,
        used_accessory_movements: dict[int, list[str]] | None = None,
        previous_day_volume: dict[str, int] | None = None,
    ) -> dict[str, int]:
        """
        Generate and save exercise content to a session using IDs.
        
        Creates its own database session to avoid holding locks during LLM calls.
        
        Args:
            session_id: ID of session to populate
            program_id: ID of parent program
            microcycle_id: ID of parent microcycle
            used_movements: List of movements already used in this microcycle
            used_movement_groups: Dict tracking usage count by substitution_group
            used_accessory_movements: Dict mapping day_number to accessory movements used
            previous_day_volume: Volume dict from previous session (muscle -> volume)
            
        Returns:
            Dict of muscle volume generated in this session (muscle -> volume)
        """
        from app.db.database import async_session_maker
        
        # Create new DB session for this operation
        async with async_session_maker() as db:
            # Fetch objects
            session = await db.get(Session, session_id)
            program = await db.get(Program, program_id)
            microcycle = await db.get(Microcycle, microcycle_id)
            
            if not session or not program or not microcycle:
                return {}
            
            # Call the existing populate_session logic
            volume = await self.populate_session(
                db, session, program, microcycle,
                used_movements, used_movement_groups, used_accessory_movements, previous_day_volume
            )
            
            # Commit the changes
            await db.commit()
            
            return volume
    
    async def populate_session(
        self,
        db: AsyncSession,
        session: Session,
        program: Program,
        microcycle: Microcycle,
        used_movements: list[str] | None = None,
        used_movement_groups: dict[str, int] | None = None,
        used_accessory_movements: dict[int, list[str]] | None = None,
        previous_day_volume: dict[str, int] | None = None,
    ) -> dict[str, int]:
        """
        Generate and save exercise content to a session.
        
        Args:
            db: Database session
            session: Session to populate
            program: Parent program
            microcycle: Parent microcycle
            used_movements: List of movements already used in this microcycle
            used_movement_groups: Dict tracking usage count by substitution_group
            used_accessory_movements: Dict mapping day_number to accessory movements used
            previous_day_volume: Volume dict from previous session (muscle -> volume)
            
        Returns:
            Dict of muscle volume generated in this session (muscle -> volume)
        """
        # Determine fatigued muscles from previous day
        fatigued_muscles = []
        if previous_day_volume:
            # Threshold: > 2 units of volume (e.g. 1 main lift) causes interference
            fatigued_muscles = [m for m, v in previous_day_volume.items() if v > 2]
            
        content = await self.generate_session_exercises(
            db, session, program, microcycle, used_movements, used_movement_groups, used_accessory_movements, fatigued_muscles
        )
        
        if used_accessory_movements:
            current_day = session.day_number
            previous_days = [d for d in used_accessory_movements.keys() if d < current_day]
            if previous_days:
                last_day = max(previous_days)
                previous_accessories = used_accessory_movements.get(last_day) or []
                if previous_accessories:
                    content = self._remove_cross_session_accessory_duplicates(
                        content, set(previous_accessories), session.session_type
                    )
        
        # Update session fields
        session.warmup_json = content.get("warmup")
        session.main_json = content.get("main")
        session.accessory_json = content.get("accessory")
        session.finisher_json = content.get("finisher")
        session.cooldown_json = content.get("cooldown")
        session.estimated_duration_minutes = content.get("estimated_duration_minutes", 60)
        session.coach_notes = content.get("reasoning")
        db.add(session)
        await db.flush()
        
        # Calculate volume for this session to pass to next day
        current_session_volume = {}
        all_movements = []
        
        if session.main_json: all_movements.extend([(m["movement"], 3) for m in session.main_json if "movement" in m])
        if session.accessory_json: all_movements.extend([(m["movement"], 2) for m in session.accessory_json if "movement" in m])
        if session.finisher_json and session.finisher_json.get("exercises"):
            all_movements.extend([(m["movement"], 1) for m in session.finisher_json["exercises"] if "movement" in m])
            
        if all_movements:
            names = [m[0] for m in all_movements]
            # Resolve muscles
            result = await db.execute(select(Movement).where(Movement.name.in_(names)))
            found_movements = {m.name: m for m in result.scalars().all()}
            
            for name, weight in all_movements:
                mov = found_movements.get(name)
                if mov:
                    # Credit primary muscle
                    p_muscle = mov.primary_muscle
                    current_session_volume[p_muscle] = current_session_volume.get(p_muscle, 0) + weight
                    
                    # Credit secondary muscles (partial weight)
                    if mov.secondary_muscles:
                        # Handle JSON list
                        secs = mov.secondary_muscles if isinstance(mov.secondary_muscles, list) else []
                        for sec in secs:
                            current_session_volume[sec] = current_session_volume.get(sec, 0) + (weight // 2)
                            
        return current_session_volume
    
    async def _load_movements_by_pattern(
        self,
        db: AsyncSession,
    ) -> dict[str, list[str]]:
        """Load all movements grouped by their primary pattern."""
        result = await db.execute(select(Movement))
        movements = list(result.scalars().all())
        
        by_pattern: dict[str, list[str]] = {}
        for movement in movements:
            pattern = movement.pattern if movement.pattern else "other"
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(movement.name)
        
        return by_pattern
    
    async def _load_user_movement_rules(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> dict[str, list[str]]:
        """Load user's movement preferences (avoid, must, prefer)."""
        result = await db.execute(
            select(UserMovementRule, Movement)
            .join(Movement, UserMovementRule.movement_id == Movement.id)
            .where(UserMovementRule.user_id == user_id)
        )
        rules = result.all()
        
        by_rule_type: dict[str, list[str]] = {
            "avoid": [],
            "must_include": [],
            "prefer": [],
        }
        
        for rule, movement in rules:
            if rule.rule_type == MovementRuleType.HARD_NO:
                by_rule_type["avoid"].append(movement.name)
            elif rule.rule_type == MovementRuleType.HARD_YES:
                by_rule_type["must_include"].append(movement.name)
            elif rule.rule_type == MovementRuleType.PREFERRED:
                by_rule_type["prefer"].append(movement.name)
        
        return by_rule_type
    
    def _validate_and_complete_session(
        self, content: dict[str, Any], session_type: SessionType
    ) -> dict[str, Any]:
        """
        Validate LLM-generated session content and add missing required sections.
        
        For training sessions (non-RECOVERY, non-CARDIO), ensures:
        - warmup, main, cooldown exist
        - EITHER accessory OR finisher exists
        - NO duplicate movements within the session
        
        Args:
            content: LLM-generated session content
            session_type: Type of session
        
        Returns:
            Validated and completed session content
        """
        # Recovery sessions don't need validation (rest days)
        if session_type == SessionType.RECOVERY:
            return content
        
        # Check required sections for training sessions
        if not content.get("warmup") or len(content.get("warmup", [])) == 0:
            logger.warning(f"Missing warmup for {session_type} session, adding default")
            content["warmup"] = [
                {"movement": "Dynamic Stretching", "sets": 2, "reps": 10, "notes": "Full body prep"},
                {"movement": "Light Cardio", "duration_seconds": 300, "notes": "5 min warm-up"},
            ]
        
        if not content.get("main") or len(content.get("main", [])) == 0:
            logger.error(f"Missing main section for {session_type} session!")
            # Use fallback for main if completely missing
            fallback = self._get_fallback_session_content(session_type)
            content["main"] = fallback.get("main", [])
        
        if not content.get("cooldown") or len(content.get("cooldown", [])) == 0:
            logger.warning(f"Missing cooldown for {session_type} session, adding default")
            content["cooldown"] = [
                {"movement": "Static Stretching", "duration_seconds": 300, "notes": "Focus on trained muscles"},
                {"movement": "Foam Rolling", "duration_seconds": 180, "notes": "Target tight areas"},
            ]
        
        # For non-cardio sessions, ensure EITHER accessory OR finisher exists
        if session_type != SessionType.CARDIO and session_type != SessionType.MOBILITY:
            has_accessory = content.get("accessory") and len(content.get("accessory", [])) > 0
            has_finisher = content.get("finisher") and content.get("finisher") is not None
            
            if not has_accessory and not has_finisher:
                logger.warning(
                    f"Missing both accessory and finisher for {session_type} session. "
                    f"Adding default accessory work."
                )
                # Add default accessory work based on session type
                content["accessory"] = self._get_default_accessories(session_type)
        
        # CRITICAL: Remove duplicate movements within the session
        content = self._remove_intra_session_duplicates(content, session_type)
        
        return content
    
    def _remove_intra_session_duplicates(
        self, content: dict[str, Any], session_type: SessionType
    ) -> dict[str, Any]:
        """
        Remove duplicate movements within a single session across all sections.
        Intelligently replaces removed exercises to preserve muscle group coverage.
        
        Priority order: main > accessory > finisher > warmup > cooldown
        If a movement appears in multiple sections, keep it in the highest priority section
        and replace it in lower priority sections with similar muscle group exercises.
        
        Args:
            content: Session content dict
            session_type: Type of session
            
        Returns:
            Session content with duplicates removed and intelligent replacements
        """
        # Track all movements used in the session
        used_movements = set()
        removed_exercises = []  # Track what was removed for replacement
        
        # Priority order for sections (main work takes precedence)
        sections_priority = [
            ("main", content.get("main", [])),
            ("accessory", content.get("accessory", [])),
            ("finisher", self._extract_finisher_exercises(content.get("finisher"))),
            ("warmup", content.get("warmup", [])),
            ("cooldown", content.get("cooldown", [])),
        ]
        
        # Process each section in priority order
        for section_name, exercises in sections_priority:
            if not exercises:
                continue
                
            # Filter out duplicates from this section
            filtered_exercises = []
            for exercise in exercises:
                movement_name = exercise.get("movement", "").strip()
                if movement_name and movement_name not in used_movements:
                    filtered_exercises.append(exercise)
                    used_movements.add(movement_name)
                elif movement_name in used_movements:
                    logger.warning(
                        f"Removed duplicate movement '{movement_name}' from {section_name} section "
                        f"(already exists in higher priority section)"
                    )
                    # Track removed exercise for potential replacement
                    removed_exercises.append({
                        "section": section_name,
                        "exercise": exercise,
                        "original_movement": movement_name
                    })
            
            # Update the content with filtered exercises
            if section_name == "finisher":
                # Special handling for finisher structure
                if content.get("finisher"):
                    if filtered_exercises:
                        content["finisher"]["exercises"] = filtered_exercises
                    else:
                        # Don't remove finisher yet - we'll add replacements later
                        content["finisher"]["exercises"] = []
            else:
                content[section_name] = filtered_exercises
        
        # INTELLIGENT REPLACEMENT: Find alternatives for removed exercises
        if removed_exercises:
            content = self._replace_removed_exercises(
                content, removed_exercises, used_movements, session_type
            )
        
        # Clean up empty sections after replacement attempts
        if content.get("finisher") and not content["finisher"].get("exercises"):
            content["finisher"] = None
        
        # Validate that we still have required sections after deduplication
        if not content.get("main"):
            logger.error(f"All main exercises were duplicates! Adding fallback for {session_type}")
            fallback = self._get_fallback_session_content(session_type)
            content["main"] = fallback.get("main", [])
        
        return content
    
    def _replace_removed_exercises(
        self,
        content: dict[str, Any],
        removed_exercises: list[dict],
        used_movements: set[str],
        session_type: SessionType,
    ) -> dict[str, Any]:
        """
        Intelligently replace removed duplicate exercises to preserve muscle group coverage.
        
        Replacement hierarchy:
        1. Same primary muscle, different movement
        2. Same secondary muscle, different movement  
        3. Same movement pattern, different movement
        4. Complementary muscle (antagonist)
        5. Skip if no suitable replacement found
        
        Args:
            content: Session content dict
            removed_exercises: List of removed exercise info
            used_movements: Set of movements already used in session
            session_type: Type of session
            
        Returns:
            Session content with intelligent replacements added
        """
        # Define muscle group relationships for intelligent replacement
        muscle_alternatives = {
            # Rear delts alternatives (primary focus)
            "rear_delts": ["Face Pull", "Reverse Fly", "Band Pull-Apart", "Prone Y Raise", "Cable Reverse Fly"],
            # Chest alternatives
            "chest": ["Push-Up", "Dumbbell Fly", "Cable Fly", "Incline Push-Up", "Chest Dip"],
            # Back alternatives  
            "lats": ["Lat Pulldown", "Pull-Up", "Chin-Up", "Cable Row", "T-Bar Row"],
            "upper_back": ["Face Pull", "Shrug", "Upright Row", "High Pull", "Band Pull-Apart"],
            # Shoulder alternatives
            "front_delts": ["Front Raise", "Arnold Press", "Pike Push-Up", "Handstand Push-Up"],
            "side_delts": ["Lateral Raise", "Upright Row", "Cable Lateral Raise", "Dumbbell Lateral Raise"],
            # Arm alternatives
            "biceps": ["Bicep Curl", "Hammer Curl", "Cable Curl", "Chin-Up", "Preacher Curl"],
            "triceps": ["Tricep Extension", "Close-Grip Push-Up", "Tricep Dip", "Overhead Extension"],
            # Leg alternatives
            "quadriceps": ["Leg Extension", "Lunge", "Step-Up", "Wall Sit", "Jump Squat"],
            "hamstrings": ["Leg Curl", "Romanian Deadlift", "Good Morning", "Glute Ham Raise"],
            "glutes": ["Hip Thrust", "Glute Bridge", "Clamshell", "Monster Walk", "Bulgarian Split Squat"],
            "calves": ["Calf Raise", "Jump Rope", "Calf Press", "Single Leg Calf Raise"],
        }
        
        # Movement pattern alternatives
        pattern_alternatives = {
            "horizontal_push": ["Push-Up", "Dumbbell Fly", "Cable Fly"],
            "horizontal_pull": ["Cable Row", "Band Pull-Apart", "Inverted Row"],
            "vertical_push": ["Pike Push-Up", "Handstand Push-Up", "Arnold Press"],
            "vertical_pull": ["Pull-Up", "Lat Pulldown", "High Pull"],
        }
        
        # Process each removed exercise
        for removed_info in removed_exercises:
            section_name = removed_info["section"]
            original_exercise = removed_info["exercise"]
            original_movement = removed_info["original_movement"]
            
            # Skip if section no longer exists or is empty
            if section_name == "finisher":
                if not content.get("finisher"):
                    continue
                current_exercises = content["finisher"].get("exercises", [])
            else:
                current_exercises = content.get(section_name, [])
            
            # Find replacement movement
            replacement_movement = self._find_replacement_movement(
                original_movement, muscle_alternatives, pattern_alternatives, used_movements
            )
            
            if replacement_movement:
                # Create replacement exercise with similar parameters
                replacement_exercise = self._create_replacement_exercise(
                    original_exercise, replacement_movement, section_name
                )
                
                # Add replacement to appropriate section
                if section_name == "finisher":
                    if content.get("finisher"):
                        if "exercises" not in content["finisher"]:
                            content["finisher"]["exercises"] = []
                        content["finisher"]["exercises"].append(replacement_exercise)
                else:
                    if section_name not in content:
                        content[section_name] = []
                    content[section_name].append(replacement_exercise)
                
                # Track the new movement as used
                used_movements.add(replacement_movement)
                
                logger.info(
                    f"Replaced removed '{original_movement}' in {section_name} section "
                    f"with '{replacement_movement}' to preserve muscle group coverage"
                )
            else:
                logger.warning(
                    f"Could not find suitable replacement for '{original_movement}' "
                    f"in {section_name} section - muscle group coverage may be reduced"
                )
        
        return content
    
    def _find_replacement_movement(
        self,
        original_movement: str,
        muscle_alternatives: dict[str, list[str]],
        pattern_alternatives: dict[str, list[str]],
        used_movements: set[str],
    ) -> str | None:
        """
        Find the best replacement movement using hierarchy of muscle/pattern matching.
        
        Args:
            original_movement: Name of the removed movement
            muscle_alternatives: Dict mapping muscle groups to alternative exercises
            pattern_alternatives: Dict mapping movement patterns to alternatives
            used_movements: Set of movements already used in session
            
        Returns:
            Name of replacement movement or None if no suitable replacement found
        """
        # Simple muscle group mapping based on common exercise names
        # In a full implementation, this would query the Movement model
        movement_to_muscles = {
            "Face Pull": ["rear_delts", "upper_back"],
            "Lateral Raise": ["side_delts"],
            "Bicep Curl": ["biceps"],
            "Tricep Extension": ["triceps"],
            "Leg Extension": ["quadriceps"],
            "Leg Curl": ["hamstrings"],
            "Calf Raise": ["calves"],
            "Push-Up": ["chest", "front_delts", "triceps"],
            "Pull-Up": ["lats", "biceps"],
            "Barbell Row": ["lats", "upper_back", "rear_delts"],
            "Barbell Bench Press": ["chest", "front_delts", "triceps"],
        }
        
        # Get muscle groups for original movement
        original_muscles = movement_to_muscles.get(original_movement, [])
        
        # Try to find replacement by muscle group priority
        for muscle in original_muscles:
            if muscle in muscle_alternatives:
                for alternative in muscle_alternatives[muscle]:
                    if alternative not in used_movements and alternative != original_movement:
                        return alternative
        
        # Fallback: try pattern-based alternatives (simplified) - only if no muscle match found
        if not original_muscles:  # Only use pattern fallback if we couldn't identify muscles
            movement_to_pattern = {
                "Face Pull": "horizontal_pull",
                "Barbell Row": "horizontal_pull", 
                "Push-Up": "horizontal_push",
                "Barbell Bench Press": "horizontal_push",
                "Pull-Up": "vertical_pull",
                "Overhead Press": "vertical_push",
            }
            
            original_pattern = movement_to_pattern.get(original_movement)
            if original_pattern and original_pattern in pattern_alternatives:
                for alternative in pattern_alternatives[original_pattern]:
                    if alternative not in used_movements and alternative != original_movement:
                        return alternative
        
        return None
    
    def _remove_cross_session_accessory_duplicates(
        self,
        content: dict[str, Any],
        previous_accessories: set[str],
        session_type: SessionType,
    ) -> dict[str, Any]:
        used_movements_session: set[str] = set()
        
        for section_name in ["main", "accessory", "warmup", "cooldown"]:
            for ex in content.get(section_name) or []:
                name = (ex.get("movement") or "").strip()
                if name:
                    used_movements_session.add(name)
        
        finisher_struct = content.get("finisher")
        finisher_exercises = []
        if finisher_struct and isinstance(finisher_struct, dict):
            for ex in finisher_struct.get("exercises") or []:
                name = (ex.get("movement") or "").strip()
                if name:
                    used_movements_session.add(name)
                    finisher_exercises.append(ex)
        
        used_movements_session.update(previous_accessories)
        
        removed_exercises: list[dict] = []
        new_accessories: list[dict] = []
        
        for ex in content.get("accessory") or []:
            movement_name = (ex.get("movement") or "").strip()
            if movement_name and movement_name in previous_accessories:
                removed_exercises.append(
                    {
                        "section": "accessory",
                        "exercise": ex,
                        "original_movement": movement_name,
                    }
                )
            else:
                new_accessories.append(ex)
        
        content["accessory"] = new_accessories
        
        new_finisher_exercises: list[dict] = []
        for ex in finisher_exercises:
            movement_name = (ex.get("movement") or "").strip()
            if movement_name and movement_name in previous_accessories:
                removed_exercises.append(
                    {
                        "section": "finisher",
                        "exercise": ex,
                        "original_movement": movement_name,
                    }
                )
            else:
                new_finisher_exercises.append(ex)
        
        if finisher_struct and isinstance(finisher_struct, dict):
            finisher_struct["exercises"] = new_finisher_exercises
            content["finisher"] = finisher_struct
        
        if removed_exercises:
            content = self._replace_removed_exercises(
                content, removed_exercises, used_movements_session, session_type
            )
        
        return content
    
    def _create_replacement_exercise(
        self,
        original_exercise: dict,
        replacement_movement: str,
        section_name: str,
    ) -> dict:
        """
        Create a replacement exercise with appropriate parameters for the section.
        
        Args:
            original_exercise: Original exercise dict
            replacement_movement: Name of replacement movement
            section_name: Section where replacement will be added
            
        Returns:
            New exercise dict with replacement movement and appropriate parameters
        """
        # Base replacement exercise
        replacement = {
            "movement": replacement_movement,
            "notes": f"Replacement for duplicate exercise"
        }
        
        # Copy relevant parameters from original, with section-appropriate defaults
        if section_name in ["main"]:
            # Main exercises: higher intensity, longer rest
            replacement.update({
                "sets": original_exercise.get("sets", 4),
                "rep_range_min": original_exercise.get("rep_range_min", 6),
                "rep_range_max": original_exercise.get("rep_range_max", 8),
                "target_rpe": original_exercise.get("target_rpe", 7.5),
                "rest_seconds": original_exercise.get("rest_seconds", 120),
            })
        elif section_name in ["accessory"]:
            # Accessory exercises: moderate intensity, shorter rest
            replacement.update({
                "sets": original_exercise.get("sets", 3),
                "rep_range_min": original_exercise.get("rep_range_min", 10),
                "rep_range_max": original_exercise.get("rep_range_max", 15),
                "target_rpe": original_exercise.get("target_rpe", 7),
                "rest_seconds": original_exercise.get("rest_seconds", 60),
            })
        elif section_name in ["finisher"]:
            # Finisher exercises: higher reps, minimal rest
            replacement.update({
                "reps": original_exercise.get("reps", 15),
                "duration_seconds": original_exercise.get("duration_seconds"),
            })
        elif section_name in ["warmup", "cooldown"]:
            # Warmup/cooldown: time-based or light reps
            replacement.update({
                "sets": original_exercise.get("sets", 2),
                "reps": original_exercise.get("reps", 10),
                "duration_seconds": original_exercise.get("duration_seconds", 60),
            })
        
        return replacement
    
    def _extract_finisher_exercises(self, finisher: dict | None) -> list[dict]:
        """Extract exercises list from finisher structure."""
        if not finisher or not isinstance(finisher, dict):
            return []
        return finisher.get("exercises", [])
    
    def _get_default_accessories(self, session_type: SessionType) -> list[dict[str, Any]]:
        """
        Get default accessory exercises based on session type.
        
        Args:
            session_type: Type of session
            
        Returns:
            List of accessory exercises
        """
        # Default accessories by session type
        defaults = {
            SessionType.UPPER: [
                {"movement": "Lateral Raise", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, 
                 "target_rpe": 7, "rest_seconds": 60, "superset_with": "Face Pull"},
                {"movement": "Face Pull", "sets": 3, "rep_range_min": 15, "rep_range_max": 20, 
                 "target_rpe": 7, "rest_seconds": 60},
                {"movement": "Bicep Curl", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, 
                 "target_rpe": 7, "rest_seconds": 60, "superset_with": "Tricep Extension"},
                {"movement": "Tricep Extension", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, 
                 "target_rpe": 7, "rest_seconds": 60},
            ],
            SessionType.LOWER: [
                {"movement": "Leg Extension", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, 
                 "target_rpe": 7, "rest_seconds": 60, "superset_with": "Leg Curl"},
                {"movement": "Leg Curl", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, 
                 "target_rpe": 7, "rest_seconds": 60},
                {"movement": "Calf Raise", "sets": 4, "rep_range_min": 15, "rep_range_max": 20, 
                 "target_rpe": 8, "rest_seconds": 45},
            ],
            SessionType.PUSH: [
                {"movement": "Lateral Raise", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, 
                 "target_rpe": 7, "rest_seconds": 60},
                {"movement": "Tricep Extension", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, 
                 "target_rpe": 7, "rest_seconds": 60},
            ],
            SessionType.PULL: [
                {"movement": "Face Pull", "sets": 3, "rep_range_min": 15, "rep_range_max": 20, 
                 "target_rpe": 7, "rest_seconds": 60},
                {"movement": "Bicep Curl", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, 
                 "target_rpe": 7, "rest_seconds": 60, "superset_with": "Hammer Curl"},
                {"movement": "Hammer Curl", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, 
                 "target_rpe": 7, "rest_seconds": 60},
            ],
            SessionType.LEGS: [
                {"movement": "Leg Extension", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, 
                 "target_rpe": 7, "rest_seconds": 60, "superset_with": "Leg Curl"},
                {"movement": "Leg Curl", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, 
                 "target_rpe": 7, "rest_seconds": 60},
                {"movement": "Calf Raise", "sets": 4, "rep_range_min": 15, "rep_range_max": 20, 
                 "target_rpe": 8, "rest_seconds": 45},
            ],
            SessionType.FULL_BODY: [
                {"movement": "Lateral Raise", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, 
                 "target_rpe": 7, "rest_seconds": 60, "superset_with": "Face Pull"},
                {"movement": "Face Pull", "sets": 3, "rep_range_min": 15, "rep_range_max": 20, 
                 "target_rpe": 7, "rest_seconds": 60},
                {"movement": "Leg Curl", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, 
                 "target_rpe": 7, "rest_seconds": 60},
            ],
        }
        
        # Return session-specific defaults or generic upper body accessories
        return defaults.get(session_type, defaults[SessionType.UPPER])
    
    def _get_recovery_session_content(self) -> dict[str, Any]:
        """Return content for a rest/recovery day."""
        return {
            "warmup": None,
            "main": None,
            "accessory": None,
            "finisher": None,
            "cooldown": [
                {"movement": "Foam Rolling", "duration_seconds": 300, "notes": "Full body"},
                {"movement": "Light Stretching", "duration_seconds": 300, "notes": "Focus on tight areas"},
            ],
            "estimated_duration_minutes": 15,
            "reasoning": "Recovery day - focus on mobility and rest.",
        }
    
    def _get_smart_fallback_session_content(
        self,
        session_type: SessionType,
        intent_tags: list[str],
        movements_by_pattern: dict[str, list[str]],
        used_movements: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Return intelligent fallback content when LLM fails.
        
        Uses movement library and intent_tags to select real exercises
        instead of generic placeholders.
        
        Args:
            session_type: Type of session (FULL_BODY, UPPER, LOWER, etc.)
            intent_tags: Movement patterns for this session (e.g., ["squat", "horizontal_push"])
            movements_by_pattern: Dict mapping pattern names to available movements
            used_movements: List of movements to avoid (already used in microcycle)
        
        Returns:
            Session content dict with real movement names
        """
        # Preferred accessory movements by pattern
        preferred_accessories = {
            "squat": ["Leg Extension", "Leg Curl", "Calf Raise", "Walking Lunge"],
            "hinge": ["Leg Curl", "Leg Extension", "Hip Thrust", "Back Extension"],
            "lunge": ["Leg Extension", "Calf Raise", "Split Squat", "Step Up"],
            "horizontal_push": ["Lateral Raise", "Face Pull", "Tricep Pushdown", "Fly"],
            "horizontal_pull": ["Bicep Curl", "Face Pull", "Rear Delt Fly", "Hammer Curl"],
            "vertical_push": ["Lateral Raise", "Face Pull", "Tricep Extension", "Upright Row"],
            "vertical_pull": ["Bicep Curl", "Hammer Curl", "Preacher Curl", "Shrug"],
        }
        
        # Build main exercises from intent tags
        main_exercises = []
        # Initialize set with passed movements
        used_movements_set = set(used_movements) if used_movements else set()
        
        for tag in intent_tags[:3]:  # Max 3 main lifts
            if tag in movements_by_pattern and movements_by_pattern[tag]:
                # Find an unused movement for this pattern
                for movement_name in movements_by_pattern[tag]:
                    if movement_name not in used_movements_set:
                        main_exercises.append({
                            "movement": movement_name,
                            "sets": 4,
                            "rep_range_min": 6,
                            "rep_range_max": 10,
                            "target_rpe": 7,
                            "rest_seconds": 120,
                        })
                        used_movements_set.add(movement_name)
                        break
        
        # Build accessory exercises based on primary patterns
        accessory_exercises = []
        
        for tag in intent_tags[:2]:  # Accessories for first 2 patterns
            if tag in preferred_accessories:
                for acc_name in preferred_accessories[tag]:
                    if acc_name not in used_movements_set:
                        accessory_exercises.append({
                            "movement": acc_name,
                            "sets": 3,
                            "rep_range_min": 10,
                            "rep_range_max": 15,
                            "target_rpe": 7,
                            "rest_seconds": 60,
                        })
                        used_movements_set.add(acc_name)
                        break
        
        # If we couldn't build main exercises, fall back to hardcoded
        if not main_exercises:
            return self._get_fallback_session_content(session_type)
        
        # Build warmup based on session type
        warmup = [
            {"movement": "Dynamic Stretching", "sets": 1, "duration_seconds": 180, "notes": "Full body mobility"},
        ]
        
        # Add pattern-specific warmup
        if any(p in intent_tags for p in ["squat", "hinge", "lunge"]):
            warmup.append({"movement": "Goblet Squat", "sets": 2, "reps": 8, "notes": "Light weight warmup"})
        if any(p in intent_tags for p in ["horizontal_push", "vertical_push"]):
            warmup.append({"movement": "Push-Up", "sets": 2, "reps": 10, "notes": "Warmup sets"})
        if any(p in intent_tags for p in ["horizontal_pull", "vertical_pull"]):
            warmup.append({"movement": "Inverted Row", "sets": 2, "reps": 8, "notes": "Light warmup"})
        
        # Build cooldown
        cooldown = [
            {"movement": "Static Stretching", "duration_seconds": 300, "notes": "Focus on trained muscles"},
        ]
        
        # Estimate duration: warmup (10) + main (25-30) + accessory (10-15) + cooldown (5) = ~55 min
        estimated_duration = 10 + (len(main_exercises) * 10) + (len(accessory_exercises) * 5) + 5
        
        return {
            "warmup": warmup,
            "main": main_exercises,
            "accessory": accessory_exercises if accessory_exercises else None,
            "finisher": None,
            "cooldown": cooldown,
            "estimated_duration_minutes": estimated_duration,
            "reasoning": f"Smart fallback session - LLM unavailable. Selected exercises based on {', '.join(intent_tags)} patterns.",
        }
    
    def _get_fallback_session_content(self, session_type: SessionType) -> dict[str, Any]:
        """Return basic fallback content when smart fallback also fails."""
        # Basic fallback based on session type
        fallbacks = {
            SessionType.UPPER: {
                "warmup": [
                    {"movement": "Arm Circles", "sets": 2, "reps": 10},
                    {"movement": "Band Pull-Aparts", "sets": 2, "reps": 15},
                ],
                "main": [
                    {"movement": "Barbell Bench Press", "sets": 4, "rep_range_min": 6, "rep_range_max": 8, "target_rpe": 7.5, "rest_seconds": 120},
                    {"movement": "Barbell Row", "sets": 4, "rep_range_min": 6, "rep_range_max": 8, "target_rpe": 7.5, "rest_seconds": 120},
                    {"movement": "Overhead Press", "sets": 3, "rep_range_min": 8, "rep_range_max": 10, "target_rpe": 7, "rest_seconds": 90},
                ],
                "accessory": [
                    {"movement": "Lateral Raise", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, "target_rpe": 7, "rest_seconds": 60},
                    {"movement": "Bicep Curl", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, "target_rpe": 7, "rest_seconds": 60},
                ],
                "finisher": None,
                "cooldown": [
                    {"movement": "Static Stretching", "duration_seconds": 300},
                ],
                "estimated_duration_minutes": 55,
                "reasoning": "Fallback upper body session - LLM generation failed.",
            },
            SessionType.LOWER: {
                "warmup": [
                    {"movement": "Dynamic Stretching", "sets": 1, "duration_seconds": 180},
                    {"movement": "Goblet Squat", "sets": 2, "reps": 8},
                ],
                "main": [
                    {"movement": "Back Squat", "sets": 4, "rep_range_min": 6, "rep_range_max": 8, "target_rpe": 7.5, "rest_seconds": 150},
                    {"movement": "Romanian Deadlift", "sets": 4, "rep_range_min": 8, "rep_range_max": 10, "target_rpe": 7, "rest_seconds": 120},
                ],
                "accessory": [
                    {"movement": "Walking Lunge", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, "target_rpe": 7, "rest_seconds": 90},
                    {"movement": "Leg Curl", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, "target_rpe": 7, "rest_seconds": 60},
                ],
                "finisher": None,
                "cooldown": [
                    {"movement": "Hip Flexor Stretch", "duration_seconds": 120},
                    {"movement": "Static Stretching", "duration_seconds": 180},
                ],
                "estimated_duration_minutes": 55,
                "reasoning": "Fallback lower body session - LLM generation failed.",
            },
            SessionType.FULL_BODY: {
                "warmup": [
                    {"movement": "Dynamic Stretching", "sets": 1, "duration_seconds": 180},
                    {"movement": "Goblet Squat", "sets": 2, "reps": 8},
                ],
                "main": [
                    {"movement": "Back Squat", "sets": 4, "rep_range_min": 6, "rep_range_max": 8, "target_rpe": 7.5, "rest_seconds": 150},
                    {"movement": "Barbell Bench Press", "sets": 4, "rep_range_min": 6, "rep_range_max": 8, "target_rpe": 7.5, "rest_seconds": 120},
                    {"movement": "Barbell Row", "sets": 4, "rep_range_min": 6, "rep_range_max": 8, "target_rpe": 7.5, "rest_seconds": 120},
                ],
                "accessory": [
                    {"movement": "Lateral Raise", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, "target_rpe": 7, "rest_seconds": 60},
                    {"movement": "Leg Curl", "sets": 3, "rep_range_min": 10, "rep_range_max": 12, "target_rpe": 7, "rest_seconds": 60},
                ],
                "finisher": None,
                "cooldown": [
                    {"movement": "Static Stretching", "duration_seconds": 300},
                ],
                "estimated_duration_minutes": 60,
                "reasoning": "Fallback full body session - LLM generation failed.",
            },
        }
        
        # Default fallback for other session types (PPL, etc.)
        default = {
            "warmup": [
                {"movement": "Dynamic Stretching", "sets": 1, "duration_seconds": 180},
            ],
            "main": [
                {"movement": "Back Squat", "sets": 4, "rep_range_min": 8, "rep_range_max": 10, "target_rpe": 7, "rest_seconds": 120},
                {"movement": "Barbell Bench Press", "sets": 4, "rep_range_min": 8, "rep_range_max": 10, "target_rpe": 7, "rest_seconds": 120},
            ],
            "accessory": [
                {"movement": "Lateral Raise", "sets": 3, "rep_range_min": 12, "rep_range_max": 15, "target_rpe": 7, "rest_seconds": 60},
            ],
            "finisher": None,
            "cooldown": [
                {"movement": "Static Stretching", "duration_seconds": 300},
            ],
            "estimated_duration_minutes": 50,
            "reasoning": "Fallback session - LLM generation failed.",
        }
        
        return fallbacks.get(session_type, default)


# Singleton instance
session_generator = SessionGeneratorService()
