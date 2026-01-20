"""Movement repository models."""
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, Text, JSON, ForeignKey
from sqlalchemy import DateTime, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enums import (
    MovementPattern,
    PrimaryMuscle,
    PrimaryRegion,
    MetricType,
    SkillLevel,
    CNSLoad,
    RelationshipType,
    MuscleRole,
)


class MovementRelationship(Base):
    """Defines relationships between movements (progressions, variations, etc)."""
    __tablename__ = "movement_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_movement_id = Column(Integer, ForeignKey("movements.id"), nullable=False, index=True)
    target_movement_id = Column(Integer, ForeignKey("movements.id"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, index=True)  # Stores RelationshipType enum
    notes = Column(Text, nullable=True)

    # Relationships
    source_movement = relationship("Movement", foreign_keys=[source_movement_id], back_populates="outgoing_relationships")
    target_movement = relationship("Movement", foreign_keys=[target_movement_id], back_populates="incoming_relationships")


class Movement(Base):
    """Movement/exercise definition."""
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Null for system movements
    name = Column(String(200), nullable=False, unique=True, index=True)
    
    # Movement classification
    pattern = Column(String(50), nullable=False, index=True)  # Stores enum value
    primary_muscle = Column(String(50), nullable=False, index=True)  # Stores enum value
    primary_region = Column(String(50), nullable=False, index=True)  # Stores enum value
    secondary_muscles = Column(JSON, default=list)  # List of PrimaryMuscle values
    
    # Load and complexity
    cns_load = Column(String(50), nullable=False, default="moderate")  # Stores enum value
    skill_level = Column(String(50), nullable=False, default="intermediate")  # Stores enum value
    
    # Movement characteristics
    compound = Column(Boolean, default=True)
    is_complex_lift = Column(Boolean, default=False)  # Requires confirmation for safety
    is_unilateral = Column(Boolean, default=False)
    
    # Fitness Function Metrics (RL Reward Signals)
    fatigue_factor = Column(Float, nullable=False, default=1.0)  # Systemic fatigue cost (for SFR)
    stimulus_factor = Column(Float, nullable=False, default=1.0) # Raw hypertrophy/strength stimulus (for SFR)
    injury_risk_factor = Column(Float, nullable=False, default=1.0) # Base injury risk (for Biomechanical Match)
    min_recovery_hours = Column(Integer, nullable=False, default=24) # Estimated recovery time
    
    # Measurement
    metric_type = Column(String(50), nullable=False, default="reps")  # Stores enum value
    
    # Categorization
    primary_discipline = Column(String(50), nullable=False, default="All", server_default="All")
    discipline_tags = Column(JSON, default=list)  # e.g., ["powerlifting", "olympic", "calisthenics"]
    equipment_tags = Column(JSON, default=list)  # e.g., ["barbell", "dumbbell", "bodyweight"]
    tags = Column(JSON, default=list)  # General tags e.g. ["crossfit", "athletic", "mobility"]
    
    # Description and notes
    description = Column(Text, nullable=True)
    coaching_cues = Column(JSON, default=list)  # List of coaching cues
    
    # Substitution helpers
    substitution_group = Column(String(100), nullable=True, index=True)  # e.g., "single_arm_row"
    
    # Relationships
    user_rules = relationship("UserMovementRule", back_populates="movement")
    session_exercises = relationship("SessionExercise", back_populates="movement")
    top_set_logs = relationship("TopSetLog", back_populates="movement")

    # Movement Relationships
    outgoing_relationships = relationship(
        "MovementRelationship",
        foreign_keys=[MovementRelationship.source_movement_id],
        back_populates="source_movement",
        cascade="all, delete-orphan"
    )
    incoming_relationships = relationship(
        "MovementRelationship",
        foreign_keys=[MovementRelationship.target_movement_id],
        back_populates="target_movement",
        cascade="all, delete-orphan"
    )

    # Anatomy Bridge
    muscle_maps = relationship("MovementMuscleMap", back_populates="movement", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Movement(id={self.id}, name='{self.name}', pattern={self.pattern})>"


class Muscle(Base):
    __tablename__ = "muscles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    region = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MovementMuscleMap(Base):
    __tablename__ = "movement_muscle_map"

    id = Column(Integer, primary_key=True, autoincrement=True)
    movement_id = Column(Integer, ForeignKey("movements.id"), nullable=False, index=True)
    muscle_id = Column(Integer, ForeignKey("muscles.id"), nullable=False, index=True)
    role = Column(SQLEnum(MuscleRole), nullable=False, index=True)
    magnitude = Column(Float, nullable=False, default=1.0)
    
    movement = relationship("Movement", back_populates="muscle_maps")
    muscle = relationship("Muscle")
