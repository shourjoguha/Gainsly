"""
ProgramService - Generates workout programs with microcycle structure and goal distribution.

Responsible for:
- Creating 8-12 week programs from split template + goal mix
- Distributing goals across microcycles with weighting
- Generating microcycles with appropriate intensity profiles
- Creating session templates with optional sections (warmup, finisher, conditioning)
- Applying movement rule constraints and interference logic
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Program, Microcycle, Session, Goal,
    MovementPattern, SplitTemplate
)
from app.schemas.program import ProgramCreate
from app.models.enums import (
    Goal, SplitTemplate, SessionType, MicrocycleStatus
)
from app.services.interference import interference_service
from app.services.metrics import metrics_service


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
        goal_objs = [g.goal for g in goals]
        interference_check = await interference_service.detect_conflicts(db, user_id, goal_objs)
        if interference_check["has_conflicts"] and interference_check.get("severity") == "high":
            raise ValueError(f"High-severity goal conflicts detected: {interference_check['conflicts']}")
        
        # Create program
        from datetime import datetime as dt
        start_date = request.program_start_date or dt.now().date()
        
        program = Program(
            user_id=user_id,
            split_template=request.split_template,
            program_start_date=start_date,
            duration_weeks=request.duration_weeks,
            goal_1=goals[0].goal,
            goal_2=goals[1].goal,
            goal_3=goals[2].goal,
            goal_weight_1=goals[0].weight,
            goal_weight_2=goals[1].weight,
            goal_weight_3=goals[2].weight,
            progression_style=request.progression_style,
            deload_every_n_microcycles=request.deload_every_n_microcycles,
            persona_tone=request.persona_tone,
            persona_aggression=request.persona_aggression,
            is_active=True,
        )
        db.add(program)
        await db.flush()  # Get program.id
        
        # Distribute goals and generate microcycles
        weights = self._calculate_goal_weights(len(goals))
        microcycle_count = max(4, request.duration_weeks // 2)  # 2 weeks per microcycle
        
        from datetime import timedelta
        current_date = start_date
        for mc_idx in range(microcycle_count):
            microcycle = await self._create_microcycle(
                db,
                program_id=program.id,
                user_id=user_id,
                mc_index=mc_idx,
                total_microcycles=microcycle_count,
                start_date=current_date,
                split=split,
                goals=goals,
                goal_weights=weights,
            )
            current_date += timedelta(weeks=2)
        
        await db.commit()
        return program
    
    async def _create_microcycle(
        self,
        db: AsyncSession,
        program_id: int,
        user_id: int,
        mc_index: int,
        total_microcycles: int,
        start_date: datetime,
        split,
        goals: list,
        goal_weights: dict,
    ) -> Microcycle:
        """
        Create a 2-week microcycle with session templates.
        
        Args:
            db: Database session
            program_id: Parent program ID
            user_id: User ID
            mc_index: Microcycle index (0-based)
            total_microcycles: Total microcycles in program
            start_date: Microcycle start date
            split: SplitTemplate object
            goals: List of Goal objects
            goal_weights: Dict of goal_id -> weight
        
        Returns:
            Created Microcycle
        """
        # Determine microcycle type based on position (deload every 3-4 microcycles)
        # For now, all start as planned; deload logic handled separately
        mc_type = "deload" if (mc_index + 1) % 4 == 0 else "work"
        
        # Select primary goal for this microcycle (round-robin)
        primary_goal = goals[mc_index % len(goals)]
        
        # Determine intensity profile
        intensity = self._calculate_intensity(mc_type, mc_index, total_microcycles)
        
        microcycle = Microcycle(
            program_id=program_id,
            sequence_number=mc_index + 1,  # 1-indexed
            micro_start_date=start_date,
            length_days=14,  # 2 weeks
            status=MicrocycleStatus.PLANNED,
            is_deload=mc_type == "deload",
        )
        db.add(microcycle)
        await db.flush()  # Get microcycle.id
        
        # Create sessions from split template
        session_date = start_date
        for day_index, day_template in enumerate(split.days[:7]):  # Max 7 days/week
            # Determine session type (lift, conditioning, etc.)
            session_type = self._infer_session_type(day_template)
            
            session = Session(
                microcycle_id=microcycle.id,
                user_id=user_id,
                session_date=session_date,
                session_type=session_type,
                primary_goal_id=primary_goal.id,
                intensity_estimate=intensity,
                status="planned",
            )
            db.add(session)
            await db.flush()  # Get session.id
            
            # Add movement patterns from day template
            if hasattr(day_template, 'movements') and day_template.movements:
                for movement in day_template.movements:
                    pattern = MovementPattern(
                        session_id=session.id,
                        user_id=user_id,
                        movement=movement.get("name", ""),
                        pattern_type=movement.get("pattern_type", "compound"),
                        sets=movement.get("sets", 3),
                        reps=movement.get("reps", 8),
                        rpe=movement.get("rpe", 7),
                    )
                    db.add(pattern)
            
            session_date += timedelta(days=1)
        
        return microcycle
    
    def _calculate_goal_weights(self, num_goals: int) -> dict:
        """
        Distribute equal weight across goals.
        
        Args:
            num_goals: Number of goals
        
        Returns:
            Dict of weight per goal index
        """
        return {i: 1.0 / num_goals for i in range(num_goals)}
    
    def _calculate_intensity(
        self,
        mc_type: str,
        mc_index: int,
        total_microcycles: int,
    ) -> str:
        """
        Determine intensity profile for microcycle.
        
        Deload microcycles use low intensity.
        Early microcycles use moderate, later use high (wave loading).
        
        Args:
            mc_type: Microcycle type ("work" or "deload")
            mc_index: Index in program
            total_microcycles: Total count
        
        Returns:
            Intensity string
        """
        if mc_type == "deload":
            return "low"
        
        progress = mc_index / total_microcycles
        if progress < 0.33:
            return "moderate"
        elif progress < 0.66:
            return "high"
        else:
            return "moderate"  # Final wave moderate
    
    def _infer_session_type(self, day_template) -> SessionType:
        """
        Infer session type from day template attributes.
        
        Args:
            day_template: Day template object
        
        Returns:
            SessionType enum
        """
        # Check template attributes for hints
        if hasattr(day_template, 'focus'):
            focus = day_template.focus.lower() if day_template.focus else ""
            if "conditioning" in focus or "cardio" in focus:
                return SessionType.CONDITIONING
            elif "strength" in focus:
                return SessionType.STRENGTH
            elif "hypertrophy" in focus:
                return SessionType.HYPERTROPHY
        
        return SessionType.STRENGTH  # Default
    
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
