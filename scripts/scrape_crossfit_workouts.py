import requests
from bs4 import BeautifulSoup
import re
import json
import os
import sys

# Add project root to path to import app modules if needed
sys.path.append(os.getcwd())

EXISTING_MOVEMENTS_FILE = os.path.join(os.getcwd(), 'seed_data', 'movements.json')
OUTPUT_CIRCUITS_FILE = os.path.join(os.getcwd(), 'seed_data', 'scraped_circuits.json')
OUTPUT_NEW_MOVEMENTS_FILE = os.path.join(os.getcwd(), 'seed_data', 'net_new_movements.json')

def load_existing_movements():
    """Load existing movements to check for duplicates."""
    if not os.path.exists(EXISTING_MOVEMENTS_FILE):
        print(f"Warning: {EXISTING_MOVEMENTS_FILE} not found.")
        return set()
    with open(EXISTING_MOVEMENTS_FILE, 'r') as f:
        data = json.load(f)
        # Handle both list and dict wrapper
        if isinstance(data, dict) and 'movements' in data:
            items = data['movements']
        elif isinstance(data, list):
            items = data
        else:
            items = []
            
        movements = set()
        for m in items:
            if isinstance(m, dict) and 'name' in m:
                movements.add(m['name'].lower())
    return movements

def normalize_text(text):
    """Normalize text for comparison."""
    return re.sub(r'[^a-z0-9\s]', '', text.lower()).strip()

def fetch_crossfit_workouts():
    """Fetch the CrossFit workout page."""
    url = "https://www.crossfit.com/workout"
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        })
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_movement_name(line):
    """Heuristic to extract movement name from a workout line."""
    # Remove leading numbers/x (e.g., "5 x ", "21 ")
    clean_line = re.sub(r'^\d+\s*[-x]?\s*', '', line)
    
    # Remove weights in parens or otherwise (e.g., "(275/185 lb)", "at 135 lbs")
    clean_line = re.sub(r'\(.*?\)', '', clean_line)
    clean_line = re.sub(r'\bat\s+\d+.*', '', clean_line) # "at 135 lbs"
    
    # Remove units and common numbers
    clean_line = re.sub(r'\b(meters|meter|m|cal|cals|calories|reps|rep|sec|seconds|min|minutes|kg|lb|lbs|ft)\b', '', clean_line, flags=re.IGNORECASE)
    
    # Remove trailing digits if they are just numbers (e.g. "Run 400")
    clean_line = re.sub(r'\s+\d+$', '', clean_line)
    
    return clean_line.strip()

def parse_workouts(html, existing_movements):
    """Parse HTML to extract workouts and identify new movements."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Regex for header: [Weekday] [YYMMDD] (e.g. "Monday 231023")
    date_regex = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{6}$", re.IGNORECASE)
    
    headers = soup.find_all(string=date_regex)
    
    circuits = []
    new_movement_candidates = set()
    
    print(f"Found {len(headers)} potential workout segments.")

    for header in headers:
        header_text = header.strip()
        
        # Find container (Article or div)
        container = header.parent
        while container and container.name not in ['article', 'section', 'div']:
             container = container.parent
        
        if not container:
            continue
            
        full_text = container.get_text(separator="\n")
        
        # Skip Rest Days
        if "Rest Day" in full_text[:100]:
            continue
            
        # Find "Stimulus and Strategy"
        # The user says: "workout text ends where there is a bold text called 'Stimulus and Strategy:'"
        # We look for the node to get accurate text extraction
        stimulus_node = container.find(lambda tag: tag.name in ['b', 'strong'] and "Stimulus and Strategy" in tag.get_text())
        
        stimulus_text = ""
        workout_text = ""
        
        if stimulus_node:
            # Extract Stimulus Text
            # "part after 'Stimulus and Strategy:' and before bolded 'Intermediate option:'"
            current = stimulus_node.next_element
            collecting = True
            while current and collecting:
                if current.name in ['b', 'strong'] and "Intermediate option" in current.get_text():
                    collecting = False
                    break
                
                if isinstance(current, str):
                    stimulus_text += current
                elif current.name == 'br':
                    stimulus_text += "\n"
                
                # Move to next, but be careful not to jump out of container
                # (Simple next_element might go too far, but usually OK for this structure)
                current = current.next_element
            
            # Extract Workout Text
            # It is the text before Stimulus and Strategy.
            # We can split the full text of the container by the header and the stimulus label.
            # This is a bit rough but works for text.
            try:
                # Get text between header and stimulus
                parts = full_text.split(header_text)
                if len(parts) > 1:
                    content_after_header = parts[1]
                    workout_text = content_after_header.split("Stimulus and Strategy")[0].strip()
            except Exception as e:
                print(f"Error parsing text for {header_text}: {e}")
        else:
            # Fallback if no stimulus section found (maybe older workouts?)
            # Just take text after header
            parts = full_text.split(header_text)
            if len(parts) > 1:
                workout_text = parts[1].strip()

        # Identify Circuit Type
        ctype = "rounds_for_time" # Default
        lower_w = workout_text.lower()
        if "rounds for time" in lower_w:
            ctype = "rounds_for_time"
        elif "amrap" in lower_w:
            ctype = "amrap"
        elif "emom" in lower_w:
            ctype = "emom"
        elif "ladder" in lower_w or re.search(r'\d+-\d+-\d+', lower_w): # 21-15-9
            ctype = "ladder"
        elif "tabata" in lower_w:
            ctype = "tabata"
        elif "chipper" in lower_w:
            ctype = "chipper"

        # Extract Movements
        lines = workout_text.split('\n')
        movements_in_circuit = []
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3: continue
            if line.lower().startswith("post "): continue 
            
            candidate_name = extract_movement_name(line)
            if len(candidate_name) < 3: continue
            if re.search(r'\d', candidate_name): continue # Still has numbers, probably not a name

            # Check if it exists
            norm_cand = normalize_text(candidate_name)
            is_new = True
            
            # Fuzzy check against existing
            for exist in existing_movements:
                norm_exist = normalize_text(exist)
                if norm_cand == norm_exist or norm_cand in norm_exist or norm_exist in norm_cand:
                    is_new = False
                    break
            
            if is_new:
                new_movement_candidates.add(candidate_name)
            
            movements_in_circuit.append({
                "original": line,
                "name": candidate_name,
                "is_new": is_new
            })

        circuits.append({
            "name": f"CrossFit {header_text}",
            "date_header": header_text,
            "circuit_type": ctype,
            "description": stimulus_text.strip(),
            "raw_workout": workout_text,
            "exercises": movements_in_circuit
        })

    return circuits, list(new_movement_candidates)

if __name__ == "__main__":
    print("Starting CrossFit Scraper...")
    existing = load_existing_movements()
    print(f"Loaded {len(existing)} existing movements.")
    
    html = fetch_crossfit_workouts()
    if html:
        circuits, new_movements = parse_workouts(html, existing)
        
        print(f"Found {len(circuits)} workouts.")
        print(f"Found {len(new_movements)} potential new movements.")
        
        # Save Circuits
        with open(OUTPUT_CIRCUITS_FILE, 'w') as f:
            json.dump(circuits, f, indent=2)
        print(f"Saved circuits to {OUTPUT_CIRCUITS_FILE}")
        
        # Save New Movements
        with open(OUTPUT_NEW_MOVEMENTS_FILE, 'w') as f:
            json.dump(sorted(new_movements), f, indent=2)
        print(f"Saved new movement candidates to {OUTPUT_NEW_MOVEMENTS_FILE}")