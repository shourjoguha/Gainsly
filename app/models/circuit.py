from sqlalchemy import Column, Integer, String, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enums import CircuitType


class CircuitTemplate(Base):
    __tablename__ = "circuit_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    circuit_type = Column(SQLEnum(CircuitType), nullable=False)
    exercises_json = Column(JSON, nullable=False, default=list)
    default_rounds = Column(Integer, nullable=True)
    default_duration_seconds = Column(Integer, nullable=True)
    bucket_stress = Column(JSON, nullable=False, default=dict)
    tags = Column(JSON, default=list)
    difficulty_tier = Column(Integer, default=1)

    def __repr__(self):
        return f"<CircuitTemplate(id={self.id}, name='{self.name}', type={self.circuit_type})>"

