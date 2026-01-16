import json
import re
import os

INPUT_FILE = os.path.join(os.getcwd(), 'seed_data', 'net_new_movements.json')
OUTPUT_FILE = os.path.join(os.getcwd(), 'seed_data', 'clean_crossfit_movements.json')

DENY_LIST = [
    "compare to",
    "crossfit.com",
    "for time",
    "rounds for",
    "rounds, each",
    "starting today",
    "the cap team",
    "to create a",
    "complete the",
    "of burpees",
    "of double-unders",
    "bodyweight barbell"
]

def is_valid_movement(name):
    name_lower = name.lower()
    
    # Check deny list
    for deny in DENY_LIST:
        if deny in name_lower:
            return False
            
    # Check length (too long is likely text, too short is likely noise)
    if len(name) < 3 or len(name) > 40:
        return False
        
    # Check for sentence-like structure (ending in period, starting with 'To')
    if name.strip().endswith('.'):
        return False
        
    return True

def clean_data():
    if not os.path.exists(INPUT_FILE):
        print(f"File not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r') as f:
        raw_movements = json.load(f)

    clean_movements = []
    for m in raw_movements:
        if is_valid_movement(m):
            clean_movements.append(m)
            
    print(f"Filtered {len(raw_movements)} -> {len(clean_movements)} movements.")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sorted(clean_movements), f, indent=2)
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_data()
