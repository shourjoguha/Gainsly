"""User and user configuration models."""
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enums import (
    ExperienceLevel,
    PersonaTone,
    PersonaAggression,
    MovementRuleType,
    RuleCadence,
    EnjoyableActivity,
    E1RMFormula,
)


class User(Base):
    """User profile."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    
    # Experience and defaults
    experience_level = Column(
        SQLEnum(ExperienceLevel),
        nullable=False,
        default=ExperienceLevel.INTERMEDIATE
    )
    
    # Global persona settings
    persona_tone = Column(
        SQLEnum(PersonaTone),
        nullable=False,
        default=PersonaTone.SUPPORTIVE
    )
    persona_aggression = Column(
        SQLEnum(PersonaAggression),
        nullable=False,
        default=PersonaAggression.BALANCED
    )
    
    # Relationships
    movement_rules = relationship("UserMovementRule", back_populates="user", cascade="all, delete-orphan")
    enjoyable_activities = relationship("UserEnjoyableActivity", back_populates="user", cascade="all, delete-orphan")
    programs = relationship("Program", back_populates="user", cascade="all, delete-orphan")
    workout_logs = relationship("WorkoutLog", back_populates="user", cascade="all, delete-orphan")
    soreness_logs = relationship("SorenessLog", back_populates="user", cascade="all, delete-orphan")
    recovery_signals = relationship("RecoverySignal", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    conversation_threads = relationship("ConversationThread", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}')>"


class UserMovementRule(Base):
    """User preferences for specific movements."""
    __tablename__ = "user_movement_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    movement_id = Column(Integer, ForeignKey("movements.id"), nullable=False, index=True)
    
    rule_type = Column(SQLEnum(MovementRuleType), nullable=False)
    cadence = Column(SQLEnum(RuleCadence), nullable=False, default=RuleCadence.PER_MICROCYCLE)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="movement_rules")
    movement = relationship("Movement", back_populates="user_rules")

    def __repr__(self):
        return f"<UserMovementRule(user_id={self.user_id}, movement_id={self.movement_id}, rule={self.rule_type})>"


class UserEnjoyableActivity(Base):
    """User's enjoyable activities for recommendations."""
    __tablename__ = "user_enjoyable_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    activity_type = Column(SQLEnum(EnjoyableActivity), nullable=False)
    custom_name = Column(String(100), nullable=True)  # For "other" activities
    recommend_every_days = Column(Integer, nullable=False, default=28)
    enabled = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="enjoyable_activities")

    def __repr__(self):
        return f"<UserEnjoyableActivity(user_id={self.user_id}, activity={self.activity_type})>"


class UserSettings(Base):
    """User-specific settings and preferences."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # e1RM calculation preference
    active_e1rm_formula = Column(
        SQLEnum(E1RMFormula),
        nullable=False,
        default=E1RMFormula.EPLEY
    )
    
    # Display preferences
    use_metric = Column(Boolean, default=True)  # True = kg, False = lbs
    
    # Relationships
    user = relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, formula={self.active_e1rm_formula})>"
