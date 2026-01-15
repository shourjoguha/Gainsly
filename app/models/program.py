"""Program planning models."""
from datetime import date, datetime
from sqlalchemy import (
    Boolean, Column, Integer, String, Date, DateTime, 
    ForeignKey, Text, JSON, Enum as SQLEnum, Float,
    CheckConstraint
)
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enums import (
    Goal,
    SplitTemplate,
    ProgressionStyle,
    PersonaTone,
    PersonaAggression,
    MicrocycleStatus,
    SessionType,
    ExerciseRole,
)


class Program(Base):
    """Training program (8-12 weeks)."""
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Program duration
    start_date = Column(Date, nullable=False)
    duration_weeks = Column(Integer, nullable=False)  # 8-12
    
    # Goals with ten-dollar method weights (must sum to 10)
    goal_1 = Column(SQLEnum(Goal), nullable=False)
    goal_2 = Column(SQLEnum(Goal), nullable=False)
    goal_3 = Column(SQLEnum(Goal), nullable=False)
    goal_weight_1 = Column(Integer, nullable=False)
    goal_weight_2 = Column(Integer, nullable=False)
    goal_weight_3 = Column(Integer, nullable=False)
    
    # Program structure
    split_template = Column(SQLEnum(SplitTemplate), nullable=False)
    days_per_week = Column(Integer, nullable=False)  # User's training frequency (2-7)
    progression_style = Column(SQLEnum(ProgressionStyle), nullable=False)
    
    # Hybrid split definition (for SplitTemplate.HYBRID)
    # Stores the custom day-by-day structure or block composition
    hybrid_definition = Column(JSON, nullable=True)
    
    # Disciplines/Training styles snapshot (ten-dollar method weights)
    # Format: [{"discipline": "powerlifting", "weight": 5}, {"discipline": "crossfit", "weight": 5}]
    disciplines_json = Column(JSON, nullable=True)
    
    # Deload configuration
    deload_every_n_microcycles = Column(Integer, nullable=False, default=4)
    
    # Persona snapshot (copied from user at program creation)
    persona_tone = Column(SQLEnum(PersonaTone), nullable=False)
    persona_aggression = Column(SQLEnum(PersonaAggression), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('duration_weeks >= 8 AND duration_weeks <= 12', name='valid_duration'),
        CheckConstraint('goal_weight_1 + goal_weight_2 + goal_weight_3 = 10', name='goals_sum_to_ten'),
        CheckConstraint('goal_weight_1 >= 0 AND goal_weight_2 >= 0 AND goal_weight_3 >= 0', name='positive_weights'),
    )
    
    # Relationships
    user = relationship("User", back_populates="programs")
    microcycles = relationship("Microcycle", back_populates="program", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Program(id={self.id}, user_id={self.user_id}, split={self.split_template})>"


class Microcycle(Base):
    """Training microcycle (7-10 days)."""
    __tablename__ = "microcycles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    
    # Timing
    start_date = Column(Date, nullable=False)
    length_days = Column(Integer, nullable=False)  # 7-10
    sequence_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    
    # Status
    status = Column(SQLEnum(MicrocycleStatus), nullable=False, default=MicrocycleStatus.PLANNED)
    is_deload = Column(Boolean, default=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length_days >= 7 AND length_days <= 10', name='valid_length'),
    )
    
    # Relationships
    program = relationship("Program", back_populates="microcycles")
    sessions = relationship("Session", back_populates="microcycle", cascade="all, delete-orphan")
    pattern_exposures = relationship("PatternExposure", back_populates="microcycle", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Microcycle(id={self.id}, program_id={self.program_id}, seq={self.sequence_number})>"


class Session(Base):
    """
    Training session within a microcycle.
    
    Sessions are flexible and may not include all sections. For example:
    - A cardio session might only have: warmup, main, cooldown
    - A strength day would have: warmup, main, accessory, cooldown
    - A mobility session might only have: warmup, main
    
    Each section (warmup, main, accessory, finisher, cooldown) is optional.
    Sections are stored as JSON arrays of exercise objects.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    microcycle_id = Column(Integer, ForeignKey("microcycles.id"), nullable=False, index=True)
    
    # Scheduling
    date = Column(Date, nullable=False, index=True)
    day_number = Column(Integer, nullable=False)  # Day within microcycle (1-10)
    
    # Session type and intent
    session_type = Column(SQLEnum(SessionType), nullable=False)
    intent_tags = Column(JSON, default=list)  # e.g., ["strength", "hypertrophy"]
    
    # Session content (JSON blocks) - ALL OPTIONAL
    # Each section can be None if not needed for this session type
    warmup_json = Column(JSON, nullable=True)  # Optional: general preparation
    main_json = Column(JSON, nullable=True)  # Optional: primary work
    accessory_json = Column(JSON, nullable=True)  # Optional: supporting work
    finisher_json = Column(JSON, nullable=True)  # Optional: brief high-effort completion
    cooldown_json = Column(JSON, nullable=True)  # Optional: active recovery
    
    # Time estimation
    estimated_duration_minutes = Column(Integer, nullable=True)
    warmup_duration_minutes = Column(Integer, nullable=True)
    main_duration_minutes = Column(Integer, nullable=True)
    accessory_duration_minutes = Column(Integer, nullable=True)
    finisher_duration_minutes = Column(Integer, nullable=True)
    cooldown_duration_minutes = Column(Integer, nullable=True)
    
    # Coach reasoning
    coach_notes = Column(Text, nullable=True)
    
    # Relationships
    microcycle = relationship("Microcycle", back_populates="sessions")
    exercises = relationship("SessionExercise", back_populates="session", cascade="all, delete-orphan")
    workout_logs = relationship("WorkoutLog", back_populates="session")

    def __repr__(self):
        return f"<Session(id={self.id}, date={self.date}, type={self.session_type})>"


class SessionExercise(Base):
    """Individual exercise within a session."""
    __tablename__ = "session_exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    movement_id = Column(Integer, ForeignKey("movements.id"), nullable=False, index=True)
    
    # Exercise role and order
    role = Column(SQLEnum(ExerciseRole), nullable=False)
    order_in_session = Column(Integer, nullable=False)
    superset_group = Column(Integer, nullable=True)  # Exercises with same number are supersetted
    
    # Prescription
    target_sets = Column(Integer, nullable=False)
    target_rep_range_min = Column(Integer, nullable=True)
    target_rep_range_max = Column(Integer, nullable=True)
    target_rpe = Column(Float, nullable=True)  # 6-10 scale
    target_rir = Column(Integer, nullable=True)  # Reps in reserve (alternative to RPE)
    target_duration_seconds = Column(Integer, nullable=True)  # For time-based exercises
    
    # Rest
    default_rest_seconds = Column(Integer, nullable=True)
    
    # Substitution info
    is_complex_lift = Column(Boolean, default=False)
    substitution_allowed = Column(Boolean, default=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="exercises")
    movement = relationship("Movement", back_populates="session_exercises")

    def __repr__(self):
        return f"<SessionExercise(id={self.id}, session_id={self.session_id}, movement_id={self.movement_id})>"
