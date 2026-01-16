from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.circuit import CircuitTemplate
from app.schemas.circuit import CircuitTemplateResponse
from app.models.enums import CircuitType

router = APIRouter()

@router.get("", response_model=list[CircuitTemplateResponse])
async def list_circuits(
    circuit_type: CircuitType | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all circuit templates, optionally filtered by type."""
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
    """Get a specific circuit template."""
    circuit = await db.get(CircuitTemplate, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")
    return circuit
