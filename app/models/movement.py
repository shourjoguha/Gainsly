"""Movement repository models."""
from sqlalchemy import Boolean, Column, Integer, String, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enums import (
    MovementPattern,
    PrimaryMuscle,
    PrimaryRegion,
    MetricType,
    SkillLevel,
    CNSLoad,
)


class Movement(Base):
    """Movement/exercise definition."""
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    
    # Movement classification
    pattern = Column(SQLEnum(MovementPattern), nullable=False, index=True)
    primary_muscle = Column(SQLEnum(PrimaryMuscle), nullable=False, index=True)
    primary_region = Column(SQLEnum(PrimaryRegion), nullable=False, index=True)
    secondary_muscles = Column(JSON, default=list)  # List of PrimaryMuscle values
    
    # Load and complexity
    cns_load = Column(SQLEnum(CNSLoad), nullable=False, default=CNSLoad.MODERATE)
    skill_level = Column(SQLEnum(SkillLevel), nullable=False, default=SkillLevel.INTERMEDIATE)
    
    # Movement characteristics
    compound = Column(Boolean, default=True)
    is_complex_lift = Column(Boolean, default=False)  # Requires confirmation for safety
    is_unilateral = Column(Boolean, default=False)
    
    # Measurement
    metric_type = Column(SQLEnum(MetricType), nullable=False, default=MetricType.REPS)
    
    # Categorization
    discipline_tags = Column(JSON, default=list)  # e.g., ["powerlifting", "olympic", "calisthenics"]
    equipment_tags = Column(JSON, default=list)  # e.g., ["barbell", "dumbbell", "bodyweight"]
    
    # Description and notes
    description = Column(Text, nullable=True)
    coaching_cues = Column(JSON, default=list)  # List of coaching cues
    
    # Substitution helpers
    substitution_group = Column(String(100), nullable=True, index=True)  # e.g., "single_arm_row"
    
    # Relationships
    user_rules = relationship("UserMovementRule", back_populates="movement")
    session_exercises = relationship("SessionExercise", back_populates="movement")
    top_set_logs = relationship("TopSetLog", back_populates="movement")

    def __repr__(self):
        return f"<Movement(id={self.id}, name='{self.name}', pattern={self.pattern})>"
