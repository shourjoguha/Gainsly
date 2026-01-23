import asyncio
import sys
from datetime import date
from app.db.database import async_session_maker
from app.services.program import program_service
from app.schemas.program import ProgramCreate, GoalWeight
from app.models.enums import SplitTemplate, ProgressionStyle, Goal

async def test_create_program():
    """Test program creation with minimal valid data."""
    async with async_session_maker() as session:
        try:
            print("Creating test program...")
            
            request = ProgramCreate(
                name="Test Program",
                duration_weeks=8,
                split_template=SplitTemplate.FULL_BODY,
                progression_style=ProgressionStyle.SINGLE_PROGRESSION,
                days_per_week=5,
                goals=[
                    GoalWeight(goal=Goal.STRENGTH, weight=5),
                    GoalWeight(goal=Goal.HYPERTROPHY, weight=5),
                ],
            )
            
            print(f"Request: {request}")
            
            program = await program_service.create_program(
                db=session,
                user_id=1,
                request=request,
            )
            
            print(f"SUCCESS: Created program ID={program.id}, name={program.name}")
            
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_create_program())
