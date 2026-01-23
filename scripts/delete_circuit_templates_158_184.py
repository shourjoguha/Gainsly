"""
Script to safely delete circuit templates with IDs 158-184
where name starts with "Imported Finisher Section".

Handles dependencies by first clearing references in sessions table.
"""
import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Session, CircuitTemplate
from app.config.settings import get_settings

async def delete_circuit_templates():
    """Delete circuit templates with IDs 158-184 safely."""
    settings = get_settings()
    
    engine = create_async_engine(settings.database_url)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as db:
        print("=" * 80)
        print("CIRCUIT TEMPLATE DELETION SCRIPT")
        print("=" * 80)
        print()
        
        target_ids = list(range(158, 185))
        
        # Step 1: Identify circuits matching criteria
        print("Step 1: Finding circuits with IDs 158-184 starting with 'Imported Finisher'...")
        circuits_to_delete = await db.execute(
            select(CircuitTemplate).where(
                CircuitTemplate.id.in_(target_ids),
                CircuitTemplate.name.like("Imported Finisher%")
            )
        )
        circuits = circuits_to_delete.scalars().all()
        
        if not circuits:
            print("  No circuits found matching the criteria.")
            print()
            await db.close()
            return
        
        circuit_ids_to_delete = [c.id for c in circuits]
        print(f"  Found {len(circuits)} circuits to delete:")
        for c in circuits:
            print(f"    - ID: {c.id}, Name: '{c.name}', Type: {c.circuit_type}")
        print()
        
        # Step 2: Check for dependencies in sessions
        print("Step 2: Checking for sessions that reference these circuits...")
        sessions_with_main = await db.execute(
            select(Session).where(Session.main_circuit_id.in_(circuit_ids_to_delete))
        )
        sessions_main = sessions_with_main.scalars().all()
        
        sessions_with_finisher = await db.execute(
            select(Session).where(Session.finisher_circuit_id.in_(circuit_ids_to_delete))
        )
        sessions_finisher = sessions_with_finisher.scalars().all()
        
        all_referencing_sessions = set(sessions_main + sessions_finisher)
        
        if all_referencing_sessions:
            print(f"  Found {len(all_referencing_sessions)} sessions referencing these circuits:")
            for s in all_referencing_sessions:
                refs = []
                if s.main_circuit_id in circuit_ids_to_delete:
                    refs.append(f"main_circuit_id={s.main_circuit_id}")
                if s.finisher_circuit_id in circuit_ids_to_delete:
                    refs.append(f"finisher_circuit_id={s.finisher_circuit_id}")
                print(f"    - Session ID: {s.id}, Date: {s.date}, Refs: {', '.join(refs)}")
        else:
            print("  No sessions reference these circuits.")
        print()
        
        # Step 3: Clear dependencies in sessions
        if all_referencing_sessions:
            print("Step 3: Clearing circuit references in sessions...")
            for session in sessions_main:
                if session.main_circuit_id in circuit_ids_to_delete:
                    session.main_circuit_id = None
                    print(f"    - Cleared main_circuit_id for session {session.id}")
            
            for session in sessions_finisher:
                if session.finisher_circuit_id in circuit_ids_to_delete:
                    session.finisher_circuit_id = None
                    print(f"    - Cleared finisher_circuit_id for session {session.id}")
            
            await db.commit()
            print("  Dependencies cleared successfully.")
            print()
        else:
            print("Step 3: No dependencies to clear.")
            print()
        
        # Step 4: Delete circuits
        print("Step 4: Deleting circuit templates...")
        for circuit in circuits:
            await db.delete(circuit)
            print(f"    - Deleted circuit ID {c.id}: '{c.name}'")
        
        await db.commit()
        print()
        print("=" * 80)
        print(f"SUCCESS: Deleted {len(circuits)} circuit templates")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  - Circuits deleted: {len(circuits)}")
        print(f"  - Sessions with references cleared: {len(all_referencing_sessions)}")
        print(f"  - Circuit IDs removed: {circuit_ids_to_delete}")
        print()
        
        await db.close()

if __name__ == "__main__":
    asyncio.run(delete_circuit_templates())
