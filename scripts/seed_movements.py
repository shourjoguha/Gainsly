import asyncio
import csv
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, or_

from app.models.movement import Movement
from app.models.enums import MovementPattern, PrimaryMuscle, PrimaryRegion, CNSLoad, SkillLevel

# CSV File Path
CSV_PATH = "/Users/shourjosmac/Downloads/movements-export-2026-01-10_19-55-08.csv"
DB_URL = "sqlite+aiosqlite:///workout_coach.db"

# Mappings
SKILL_MAP = {
    "1": "beginner",
    "2": "beginner", 
    "3": "intermediate",
    "4": "advanced",
    "5": "expert"
}

CNS_MAP = {
    "1": "very_low",
    "2": "low",
    "3": "moderate",
    "4": "high",
    "5": "very_high"
}

BODY_PART_MAP = {
    "legs": "quadriceps", # Default to Hammys for generic legs
    "anterior_legs": "quadriceps",
    "posterior_legs": "hamstrings",
    "calves": "calves",
    "chest": "chest",
    "back": "lats", # Default generic back to lats
    "lats": "lats",
    "shoulders": "front_delts", # Default shoulders
    "triceps": "triceps",
    "biceps": "biceps",
    "forearms": "forearms",
    "glutes": "glutes",
    "hamstrings": "hamstrings",
    "quads": "quadriceps",
    "core": "core",
    "abs": "core",
    "obliques": "obliques",
    "full_body": "full_body",
    "traps": "upper_back",
    "upper_back": "upper_back",
    "front_delts": "front_delts",
    "side_delts": "side_delts",
    "rear_delts": "rear_delts",
    "lower_back": "lower_back"
}

REGION_MAP = {
    "quadriceps": "anterior_lower",
    "hamstrings": "posterior_lower",
    "glutes": "posterior_lower",
    "calves": "posterior_lower",
    "chest": "anterior_upper",
    "lats": "posterior_upper",
    "upper_back": "posterior_upper",
    "front_delts": "anterior_upper",
    "side_delts": "shoulder",
    "rear_delts": "posterior_upper",
    "biceps": "anterior_upper",
    "triceps": "posterior_upper",
    "forearms": "anterior_upper",
    "core": "core",
    "obliques": "core",
    "lower_back": "posterior_lower",
    "full_body": "full_body"
}

async def seed_movements():
    print(f"Reading CSV from {CSV_PATH}...")
    
    engine = create_async_engine(DB_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    new_count = 0
    updated_count = 0
    
    async with async_session() as session:
        # Read existing movements to avoid duplicates
        existing_result = await session.execute(select(Movement))
        existing_movements = {m.name.lower(): m for m in existing_result.scalars().all()}
        
        with open(CSV_PATH, 'r') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row in reader:
                name = row['name'].strip()
                
                # Parse JSON fields
                try:
                    equipment = json.loads(row['equipment'].replace('""', '"')) if row['equipment'] else []
                    secondary = json.loads(row['secondary_body_parts'].replace('""', '"')) if row['secondary_body_parts'] else []
                except json.JSONDecodeError:
                    equipment = []
                    secondary = []
                
                # Determine tags
                discipline_tags = []
                if row.get('is_bodybuilding') == '1': discipline_tags.append('bodybuilding')
                if row.get('is_powerlifting') == '1': discipline_tags.append('powerlifting')
                if row.get('is_olympic_lifting') == '1': discipline_tags.append('olympic_lifting')
                if row.get('is_athletic_drills') == '1': 
                    discipline_tags.append('athletic_drills')
                    discipline_tags.append('crossfit') # Map to crossfit as well
                
                # Determine primary muscle/region
                csv_body_part = row['body_part'].lower()
                primary_muscle = BODY_PART_MAP.get(csv_body_part, "full_body")
                primary_region = REGION_MAP.get(primary_muscle, "full_body")
                
                # Map other fields
                pattern = row['pattern']
                # Clean up pattern (csv has 'push_horizontal', db might expect 'horizontal_push')
                if pattern == 'push_horizontal': pattern = 'horizontal_push'
                if pattern == 'push_vertical': pattern = 'vertical_push'
                if pattern == 'pull_horizontal': pattern = 'horizontal_pull'
                if pattern == 'pull_vertical': pattern = 'vertical_pull'
                
                movement_data = {
                    "name": name,
                    "pattern": pattern,
                    "primary_muscle": primary_muscle,
                    "primary_region": primary_region,
                    "secondary_muscles": secondary,
                    "cns_load": CNS_MAP.get(row['cns_load'], "moderate"),
                    "skill_level": SKILL_MAP.get(row['skill_level'], "intermediate"),
                    "compound": row['type'] in ['compound', 'olympic', 'carry'],
                    "metric_type": "time" if row['type'] in ['cardio', 'carry'] else "reps",
                    "discipline_tags": discipline_tags,
                    "equipment_tags": equipment,
                    "description": row['description']
                }
                
                if name.lower() in existing_movements:
                    # Update existing?
                    # For now, let's just update discipline tags if they are empty
                    mov = existing_movements[name.lower()]
                    if not mov.discipline_tags:
                        mov.discipline_tags = discipline_tags
                        updated_count += 1
                else:
                    # Insert new
                    new_movement = Movement(**movement_data)
                    session.add(new_movement)
                    new_count += 1
        
        await session.commit()
    
    print(f"Seeding complete!")
    print(f"Added {new_count} new movements")
    print(f"Updated {updated_count} existing movements")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_movements())
