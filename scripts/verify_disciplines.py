import asyncio
import sys
import os
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append(os.getcwd())
from app.config.settings import get_settings
from app.models.movement import Movement

async def verify():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Count by discipline
        stmt = select(Movement.primary_discipline, func.count(Movement.id)).group_by(Movement.primary_discipline)
        result = await session.execute(stmt)
        for disc, count in result.all():
            print(f"{disc}: {count}")
            
        print("-" * 20)
        
        # Sample check
        samples = ["Thruster", "Bicep Curl", "Snatch", "Cat Cow", "Push-Up", "Burpee"]
        for name in samples:
            stmt = select(Movement).where(Movement.name.ilike(f"%{name}%")).limit(1)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if m:
                print(f"{m.name}: {m.primary_discipline} ({m.pattern})")
            else:
                print(f"{name}: Not found")

if __name__ == "__main__":
    asyncio.run(verify())
