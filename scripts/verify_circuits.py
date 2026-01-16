import asyncio
import sys
import os
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append(os.getcwd())
from app.config.settings import get_settings
from app.models.circuit import CircuitTemplate

async def verify():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Filter strictly for non-null description and non-empty exercises
        # Note: SQLAlchemy checking JSON content can be tricky, so we fetch all and filter in python for this script
        stmt = select(CircuitTemplate)
        result = await session.execute(stmt)
        all_circuits = result.scalars().all()
        
        valid_circuits = [c for c in all_circuits if c.description and c.exercises_json and len(c.exercises_json) > 0]
        
        print(f"Total circuits: {len(all_circuits)}")
        print(f"Valid circuits (desc + exercises): {len(valid_circuits)}")
        
        # Check for duplicates
        name_counts = {}
        for c in all_circuits:
            name_counts[c.name] = name_counts.get(c.name, 0) + 1
            
        duplicates = {name: count for name, count in name_counts.items() if count > 1}
        
        if duplicates:
            print("\nWARNING: DUPLICATES FOUND:")
            for name, count in duplicates.items():
                print(f"  - {name}: {count} times")
        else:
            print("\nSUCCESS: No duplicate circuit names found.")
        
        for c in valid_circuits[:5]:
            print(f"ID: {c.id}")
            print(f"Name: {c.name}")
            print(f"Type: {c.circuit_type}")
            print(f"Description: {c.description[:100]}...")
            print("Exercises:")
            for ex in c.exercises_json:
                print(f"  - {ex['movement_name']} (ID: {ex['movement_id']})")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(verify())
