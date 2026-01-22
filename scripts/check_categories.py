
import asyncio
from sqlalchemy import select
from app.db.database import get_db
from app.models.program import ActivityDefinition

async def check_categories():
    print("Checking activity categories...")
    async for db in get_db():
        result = await db.execute(select(ActivityDefinition))
        activities = result.scalars().all()
        for a in activities:
            print(f"ID: {a.id}, Name: {a.name}, Category: {a.category}")
        break

if __name__ == "__main__":
    asyncio.run(check_categories())
