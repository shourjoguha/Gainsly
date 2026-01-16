
import asyncio
from enum import Enum
from typing import Dict, Any, List

class SplitTemplate(str, Enum):
    UPPER_LOWER = "upper_lower"
    PPL = "ppl"
    FULL_BODY = "full_body"
    HYBRID = "hybrid"

class ProgramService:
    def _generate_full_body_structure(self, days_per_week: int) -> Dict[str, Any]:
        print(f"Generating full body structure for {days_per_week} days (type: {type(days_per_week)})")
        focus_patterns = [
            ["squat", "horizontal_push", "horizontal_pull"],
            ["hinge", "vertical_push", "vertical_pull"],
            ["lunge", "horizontal_push", "vertical_pull"],
            ["squat", "vertical_push", "horizontal_pull"],
        ]
        
        structure = []
        training_day_count = 0
        
        if days_per_week == 2:
            structure = [{"day": 1, "type": "full_body"}] # simplified
            training_day_count = 2
        elif days_per_week == 3:
            structure = [{"day": 1, "type": "full_body"}] # simplified
            training_day_count = 3
        elif days_per_week == 4:
            structure = [{"day": 1, "type": "full_body"}] # simplified
            training_day_count = 4
        elif days_per_week == 5:
            structure = [
                {"day": 1, "type": "full_body", "focus": focus_patterns[0]},
                {"day": 2, "type": "full_body", "focus": focus_patterns[1]},
                {"day": 3, "type": "rest"},
                {"day": 4, "type": "full_body", "focus": focus_patterns[2]},
                {"day": 5, "type": "full_body", "focus": focus_patterns[3]},
                {"day": 6, "type": "rest"},
                {"day": 7, "type": "full_body", "focus": focus_patterns[0]},
            ]
            training_day_count = 5
        elif days_per_week == 6:
            structure = [{"day": 1, "type": "full_body"}] # simplified
            training_day_count = 6
        else:
            structure = [{"day": 1, "type": "full_body"}] # simplified
            training_day_count = 7
        
        return {
            "days_per_cycle": 7,
            "structure": structure,
            "training_days": training_day_count,
            "rest_days": 7 - training_day_count,
        }

    def _get_default_split_template(
        self, template: SplitTemplate, days_per_week: int
    ) -> Dict[str, Any]:
        print(f"Getting default split template for {template} with {days_per_week} days")
        defaults = {
            SplitTemplate.UPPER_LOWER: {
                "days_per_cycle": 7,
                "training_days": 4,
            },
            SplitTemplate.PPL: {
                "days_per_cycle": 7,
                "training_days": 6,
            },
            SplitTemplate.FULL_BODY: self._generate_full_body_structure(days_per_week),
            SplitTemplate.HYBRID: {
                "days_per_cycle": 7,
                "training_days": 3,
            },
        }
        return defaults.get(template, defaults[SplitTemplate.FULL_BODY])

async def main():
    service = ProgramService()
    
    # Test Case 1: Full Body, 5 days
    print("\n--- Test Case 1: Full Body, 5 days ---")
    result = service._get_default_split_template(SplitTemplate.FULL_BODY, 5)
    print(f"Training days: {result.get('training_days')}")
    print(f"Structure length: {len(result.get('structure', []))}")
    
    # Test Case 2: Full Body, 4 days
    print("\n--- Test Case 2: Full Body, 4 days ---")
    result = service._get_default_split_template(SplitTemplate.FULL_BODY, 4)
    print(f"Training days: {result.get('training_days')}")

    # Test Case 3: Upper Lower, 5 days (Should ignore days_per_week currently)
    print("\n--- Test Case 3: Upper Lower, 5 days ---")
    result = service._get_default_split_template(SplitTemplate.UPPER_LOWER, 5)
    print(f"Training days: {result.get('training_days')}")

if __name__ == "__main__":
    asyncio.run(main())
