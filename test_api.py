import asyncio
import sys
from app.models import Program
from app.db.database import async_session_maker
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def test_programs_endpoint():
    async with async_session_maker() as session:
        try:
            query = select(Program).options(selectinload(Program.program_disciplines)).where(Program.user_id == 1)
            result = await session.execute(query)
            programs = list(result.scalars().unique().all())
            print(f"Found {len(programs)} programs for user_id=1:")
            for prog in programs[:5]:
                print(f"  id={prog.id}, name={prog.name}, is_active={prog.is_active}, created_at={prog.created_at}")
                print(f"    program_disciplines: {len(prog.program_disciplines)} items")
                for pd in prog.program_disciplines:
                    print(f"      - {pd.discipline_type}: {pd.weight}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

asyncio.run(test_programs_endpoint())
