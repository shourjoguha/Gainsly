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
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Program, Microcycle, Session, HeuristicConfig, User
)
from app.schemas.program import ProgramCreate
from app.models.enums import (
    Goal, SplitTemplate, SessionType, MicrocycleStatus, PersonaTone, PersonaAggression
)
from app.services.interference import interference_service


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
        
        # Extract goals from request
        goals = request.goals  # List of GoalWeight objects
        if len(goals) != 3:
            raise ValueError("Exactly 3 goals required")
        
        # Check for goal interference
        is_valid, warnings = await interference_service.validate_goals(
            db, goals[0].goal, goals[1].goal, goals[2].goal
        )
        if not is_valid:
            raise ValueError(f"Goal validation failed: {warnings}")
        
        # Load split template configuration
        split_config = await self._load_split_template(db, request.split_template)
        
        # Get user for defaults
        user = await db.get(User, user_id)
        
        # Determine persona settings (from request or user defaults)
        persona_tone = request.persona_tone or (user.persona_tone if user else PersonaTone.SUPPORTIVE)
        persona_aggression = request.persona_aggression or (user.persona_aggression if user else PersonaAggression.BALANCED)
        
        # Create program
        start_date = request.program_start_date or date.today()
        
        program = Program(
            user_id=user_id,
            split_template=request.split_template,
            start_date=start_date,
            duration_weeks=request.duration_weeks,
            goal_1=goals[0].goal,
            goal_2=goals[1].goal,
            goal_3=goals[2].goal,
            goal_weight_1=goals[0].weight,
            goal_weight_2=goals[1].weight,
            goal_weight_3=goals[2].weight,
            progression_style=request.progression_style,
            deload_every_n_microcycles=request.deload_every_n_microcycles or 4,
            persona_tone=persona_tone,
            persona_aggression=persona_aggression,
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
            current_date += timedelta(days=days_per_cycle)
        
        await db.commit()
        await db.refresh(program)
        return program
    
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
    
    async def _load_split_template(self, db: AsyncSession, template: SplitTemplate) -> Dict[str, Any]:
        """
        Load split template configuration from heuristic configs.
        
        Args:
            db: Database session
            template: SplitTemplate enum value
        
        Returns:
            Split template configuration dict
        """
        # Query the split_templates heuristic config
        result = await db.execute(
            select(HeuristicConfig).where(
                HeuristicConfig.name == "split_templates",
                HeuristicConfig.active == True
            ).limit(1)
        )
        config = result.scalar_one_or_none()
        
        if config and config.json_blob:
            # Get the specific template (e.g., "upper_lower", "ppl", "full_body")
            template_key = template.value  # e.g., "upper_lower"
            template_config = config.json_blob.get(template_key)
            if template_config:
                return template_config
        
        # Return default structure if not found
        return self._get_default_split_template(template)
    
    def _get_default_split_template(self, template: SplitTemplate) -> Dict[str, Any]:
        """
        Return default split template structure when heuristics not available.
        """
        defaults = {
            SplitTemplate.UPPER_LOWER: {
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
            },
            SplitTemplate.PPL: {
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
            },
            SplitTemplate.FULL_BODY: {
                "days_per_cycle": 7,
                "structure": [
                    {"day": 1, "type": "full_body", "focus": ["squat", "horizontal_push", "horizontal_pull"]},
                    {"day": 2, "type": "rest"},
                    {"day": 3, "type": "full_body", "focus": ["hinge", "vertical_push", "vertical_pull"]},
                    {"day": 4, "type": "rest"},
                    {"day": 5, "type": "full_body", "focus": ["squat", "horizontal_push", "horizontal_pull"]},
                    {"day": 6, "type": "rest"},
                    {"day": 7, "type": "rest"},
                ],
                "training_days": 3,
                "rest_days": 4,
            },
            SplitTemplate.HYBRID: {
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
            },
        }
        return defaults.get(template, defaults[SplitTemplate.FULL_BODY])
    
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
