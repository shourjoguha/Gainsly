import json
from pathlib import Path

# Mapping based on SkillLevel enum
SKILL_LEVEL_MAP = {
    1: "beginner",
    2: "intermediate",
    3: "advanced",
    4: "expert",
    5: "elite"
}

def fix_movements():
    file_path = Path("seed_data/movements.json")
    if not file_path.exists():
        print("File not found")
        return

    with open(file_path, "r") as f:
        data = json.load(f)

    movements = data.get("movements", [])
    updated_count = 0

    for m in movements:
        sl = m.get("skill_level")
        if isinstance(sl, int):
            if sl in SKILL_LEVEL_MAP:
                m["skill_level"] = SKILL_LEVEL_MAP[sl]
                updated_count += 1
            else:
                print(f"Unknown skill level {sl} for {m['name']}")

    data["movements"] = movements

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Updated {updated_count} movements")

if __name__ == "__main__":
    fix_movements()
