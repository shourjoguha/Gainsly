import asyncio
import json
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append(os.getcwd())
from app.config.settings import get_settings
from app.models.movement import Movement
from app.models.enums import MovementPattern

def clean_name(name):
    n = name.strip()
    if n.lower().startswith("max- "):
        n = n[5:]
    if n.lower().startswith("second "):
        n = n[7:]
    return n

async def enrich():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Load CrossFit movements
    cf_file = os.path.join(os.getcwd(), 'seed_data', 'clean_crossfit_movements.json')
    with open(cf_file, 'r') as f:
        raw_cf = json.load(f)
        
    # Create set of normalized names for fast lookup
    # Note: ingest script does clean_name(n).title() for DB name.
    # We will match m.name.lower() against clean_name(n).lower()
    cf_names = set()
    for n in raw_cf:
        c = clean_name(n)
        cf_names.add(c.lower()) 

    async with async_session() as session:
        result = await session.execute(select(Movement))
        movements = result.scalars().all()
        
        updated_count = 0
        for m in movements:
            old_disc = m.primary_discipline
            new_disc = "All"
            
            # Check CrossFit match
            # The DB name might be slightly different if manually edited, but assuming ingestion consistency:
            # We strip just in case
            m_name_clean = m.name.lower().strip()
            
            if m_name_clean in cf_names:
                new_disc = "CrossFit"
            # Use string comparison for safety if pattern is stored as string
            elif str(m.pattern) == str(MovementPattern.ISOLATION.value) or str(m.pattern) == "isolation":
                new_disc = "Bodybuilding"
            elif str(m.pattern) == str(MovementPattern.OLYMPIC.value) or str(m.pattern) == "olympic":
                new_disc = "Olympic Lifting"
            elif str(m.pattern) == str(MovementPattern.MOBILITY.value) or str(m.pattern) == "mobility":
                new_disc = "Mobility"
            else:
                new_disc = "All"
            
            if m.primary_discipline != new_disc:
                m.primary_discipline = new_disc
                updated_count += 1
                # print(f"Updated {m.name}: {old_disc} -> {new_disc}")
        
        await session.commit()
        print(f"Enrichment complete. Updated {updated_count} movements.")

if __name__ == "__main__":
    asyncio.run(enrich())
