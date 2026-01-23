"""
Script to check what circuits exist in the ID range 158-184.
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import CircuitTemplate
from app.config.settings import get_settings

async def check_circuit_templates():
    """Check circuits in the ID range 158-184."""
    settings = get_settings()
    
    engine = create_async_engine(settings.database_url)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as db:
        print("=" * 80)
        print("CHECKING CIRCUIT TEMPLATES (IDs 158-184)")
        print("=" * 80)
        print()
        
        target_ids = list(range(158, 185))
        
        circuits = await db.execute(
            select(CircuitTemplate).where(CircuitTemplate.id.in_(target_ids))
        )
        circuits = circuits.scalars().all()
        
        if not circuits:
            print("No circuits found in the ID range 158-184.")
        else:
            print(f"Found {len(circuits)} circuits in the ID range 158-184:")
            print()
            for c in circuits:
                print(f"  ID: {c.id}")
                print(f"  Name: '{c.name}'")
                print(f"  Type: {c.circuit_type}")
                print(f"  Description: {c.description[:50] + '...' if c.description and len(c.description) > 50 else c.description}")
                print(f"  Tags: {c.tags}")
                print("-" * 80)
        
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_circuit_templates())
