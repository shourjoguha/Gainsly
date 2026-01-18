from pathlib import Path
import json

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.circuit import CircuitTemplate
from app.schemas.circuit import (
    CircuitTemplateResponse,
    CircuitTemplateUpdate,
    CircuitTemplateAdminDetail,
)
from app.models.enums import CircuitType
from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()


async def require_admin(x_admin_token: str | None = Header(default=None)) -> bool:
    if settings.admin_api_token:
        if x_admin_token != settings.admin_api_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    else:
        if not settings.debug:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin features disabled")
    return True


def load_raw_workout_for_circuit(name: str) -> str | None:
    path = Path("seed_data") / "scraped_circuits.json"
    try:
        with path.open() as f:
            circuits_data = json.load(f)
    except FileNotFoundError:
        return None
    for item in circuits_data:
        if item.get("name") == name:
            return item.get("raw_workout") or item.get("description")
    return None


@router.get("", response_model=list[CircuitTemplateResponse])
async def list_circuits(
    circuit_type: CircuitType | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(CircuitTemplate)
    if circuit_type:
        query = query.where(CircuitTemplate.circuit_type == circuit_type)
    query = query.order_by(CircuitTemplate.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{circuit_id}", response_model=CircuitTemplateResponse)
async def get_circuit(
    circuit_id: int,
    db: AsyncSession = Depends(get_db),
):
    circuit = await db.get(CircuitTemplate, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")
    return circuit


@router.get("/admin/{circuit_id}", response_model=CircuitTemplateAdminDetail)
async def get_circuit_admin(
    circuit_id: int,
    db: AsyncSession = Depends(get_db),
    admin: bool = Depends(require_admin),
):
    circuit = await db.get(CircuitTemplate, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")
    raw_workout = load_raw_workout_for_circuit(circuit.name)
    return CircuitTemplateAdminDetail(
        id=circuit.id,
        name=circuit.name,
        description=circuit.description,
        circuit_type=circuit.circuit_type,
        exercises_json=circuit.exercises_json or [],
        default_rounds=circuit.default_rounds,
        default_duration_seconds=circuit.default_duration_seconds,
        tags=circuit.tags or [],
        difficulty_tier=circuit.difficulty_tier,
        raw_workout=raw_workout,
    )


@router.put("/admin/{circuit_id}", response_model=CircuitTemplateResponse)
async def update_circuit_admin(
    circuit_id: int,
    payload: CircuitTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    admin: bool = Depends(require_admin),
):
    circuit = await db.get(CircuitTemplate, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")
    circuit.exercises_json = payload.exercises_json
    await db.commit()
    await db.refresh(circuit)
    return circuit
