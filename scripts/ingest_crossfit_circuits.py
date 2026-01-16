import json
import os
import sys
import asyncio
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.getcwd())

from app.models.movement import Movement
from app.models.circuit import CircuitTemplate
from app.models.enums import (
    MovementPattern, PrimaryMuscle, PrimaryRegion, 
    MetricType, SkillLevel, CNSLoad, CircuitType
)
from app.config.settings import get_settings

CLEAN_MOVEMENTS_FILE = os.path.join(os.getcwd(), 'seed_data', 'clean_crossfit_movements.json')
CIRCUITS_FILE = os.path.join(os.getcwd(), 'seed_data', 'scraped_circuits.json')

NAMED_WORKOUTS = {"grace", "isabel", "hidalgo", "fran", "murph", "helen", "diane", "elizabeth"}

def normalize(name):
    return name.lower().strip()

def clean_name(name):
    n = name.strip()
    if n.lower().startswith("max- "):
        n = n[5:]
    if n.lower().startswith("second "):
        n = n[7:]
    return n

def guess_metadata(name):
    n = name.lower()
    meta = {
        "pattern": MovementPattern.CONDITIONING,
        "primary_muscle": PrimaryMuscle.FULL_BODY,
        "primary_region": PrimaryRegion.FULL_BODY,
        "metric_type": MetricType.REPS,
        "skill_level": SkillLevel.INTERMEDIATE,
        "cns_load": CNSLoad.MODERATE,
        "primary_discipline": "CrossFit"
    }
    
    if "squat" in n or "thruster" in n or "wall-ball" in n:
        meta["pattern"] = MovementPattern.SQUAT
        meta["primary_muscle"] = PrimaryMuscle.QUADRICEPS
        meta["primary_region"] = PrimaryRegion.LOWER_BODY
    elif "deadlift" in n or "clean" in n or "snatch" in n:
        meta["pattern"] = MovementPattern.HINGE
        meta["primary_muscle"] = PrimaryMuscle.HAMSTRINGS
        meta["primary_region"] = PrimaryRegion.POSTERIOR_LOWER
    elif "press" in n or "push-up" in n or "handstand" in n:
        meta["pattern"] = MovementPattern.VERTICAL_PUSH if "press" in n or "handstand" in n else MovementPattern.HORIZONTAL_PUSH
        meta["primary_muscle"] = PrimaryMuscle.SHOULDER if "vertical" in str(meta["pattern"]) else PrimaryMuscle.CHEST
        meta["primary_region"] = PrimaryRegion.UPPER_BODY
    elif "pull-up" in n or "row" in n:
        meta["pattern"] = MovementPattern.VERTICAL_PULL if "pull-up" in n else MovementPattern.HORIZONTAL_PULL
        meta["primary_muscle"] = PrimaryMuscle.LATS
        meta["primary_region"] = PrimaryRegion.UPPER_BODY
    elif "run" in n or "bike" in n or "row" in n or "double-under" in n or "burpee" in n:
        meta["pattern"] = MovementPattern.CARDIO if "run" in n or "bike" in n or "row" in n else MovementPattern.PLYOMETRIC
        meta["metric_type"] = MetricType.DISTANCE if "run" in n or "bike" in n or "row" in n else MetricType.REPS
    
    return meta

async def ingest():
    settings = get_settings()
    db_url = settings.database_url
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Ingest Movements
        print("Ingesting Movements...")
        with open(CLEAN_MOVEMENTS_FILE, 'r') as f:
            raw_movements = json.load(f)
            
        existing_stmt = select(Movement.name)
        existing_result = await session.execute(existing_stmt)
        existing_names = {n.lower() for n in existing_result.scalars().all()}
        
        movement_map = {} # name -> db_obj
        
        # Load all existing first to map
        stmt = select(Movement)
        res = await session.execute(stmt)
        for m in res.scalars().all():
            movement_map[m.name.lower()] = m

        for name in raw_movements:
            clean = clean_name(name)
            if clean.lower() in NAMED_WORKOUTS:
                continue
            if clean.lower() in existing_names:
                continue
            
            meta = guess_metadata(clean)
            print(f"DEBUG: meta keys: {meta.keys()}")
            # print(f"DEBUG: Movement columns: {Movement.__table__.columns.keys()}")
            
            new_mov = Movement(
                name=clean.title(), # Capitalize
                **meta
            )
            session.add(new_mov)
            print(f"Adding new movement: {clean.title()}")
            existing_names.add(clean.lower())
            
            # Flush to get ID and update map
            await session.flush()
            movement_map[clean.lower()] = new_mov

        await session.commit()
        
        # 2. Ingest Circuits
        print("\nIngesting Circuits...")
        with open(CIRCUITS_FILE, 'r') as f:
            circuits_data = json.load(f)
            
        for c_data in circuits_data:
            if not c_data['exercises']:
                print(f"Skipping empty circuit: {c_data['name']}")
                continue

            # Check duplicates by name
            stmt = select(CircuitTemplate).where(CircuitTemplate.name == c_data['name'])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if existing:
                # If existing has no exercises, delete it and replace
                if not existing.exercises_json:
                     print(f"Replacing empty existing circuit: {c_data['name']}")
                     await session.delete(existing)
                     await session.flush()
                else:
                    print(f"Skipping duplicate circuit: {c_data['name']}")
                    continue
                
            # Build exercises JSON
            exercises_list = []
            for ex in c_data['exercises']:
                # Try to find the movement in DB
                mov_name = clean_name(ex['name']).lower()
                
                # Fuzzy-ish match: check if mapped name is inside or vice versa
                matched_mov = None
                if mov_name in movement_map:
                    matched_mov = movement_map[mov_name]
                else:
                    # Fallback search
                    for k, v in movement_map.items():
                        if k in mov_name or mov_name in k:
                            matched_mov = v
                            break
                
                exercises_list.append({
                    "original_text": ex['original'],
                    "movement_id": matched_mov.id if matched_mov else None,
                    "movement_name": matched_mov.name if matched_mov else ex['name'],
                    "reps_or_scheme": ex['original'].replace(ex['name'], "").strip() # Very rough
                })
            
            # Map CircuitType string to Enum
            ctype_str = c_data.get('circuit_type', 'rounds_for_time').lower()
            try:
                ctype = CircuitType(ctype_str)
            except ValueError:
                ctype = CircuitType.ROUNDS_FOR_TIME
                
            new_circuit = CircuitTemplate(
                name=c_data['name'],
                description=c_data['description'],
                circuit_type=ctype,
                exercises_json=exercises_list,
                tags=["crossfit", "scraped"]
            )
            session.add(new_circuit)
            print(f"Adding circuit: {c_data['name']}")
            
        await session.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(ingest())
