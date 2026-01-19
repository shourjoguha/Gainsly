I will update the `CrossFitParser` in `app/parsing/crossfit.py` and the scraper in `scripts/scrape_crossfit_workouts.py` to correctly identify workout types (AMRAP, EMOM, RFT), extract circuit-level metrics (time caps, rounds), and fix the number parsing issue.

### 1. Circuit Metadata Extraction

I will add a `parse_circuit_metadata(raw_text)` method to the parser that analyzes the text between the header and the workout body to extract:

* **Circuit Type**: `AMRAP`, `EMOM`, `Rounds For Time`, `For Time`, etc.

* **Time Cap / Duration**: Extract "in 10 minutes", "20 minute time cap", "On a 90-second clock".

* **Rounds**: Extract "3 rounds", "5 rounds for time".

### 2. EMOM/Interval Structure Support

I will enhance the parsing logic to detect "On a \[time] clock" or "Every \[time]" patterns to:

* Identify these as `Interval` or `EMOM` blocks.

* Capture the **Work/Rest** intervals (e.g., "90 seconds work, 90 seconds rest").

* Correctly grouping exercises under these blocks is complex with a flat list, so I will add a `circuit_instructions` field to the output JSON to store the structured interval details (e.g., `{"type": "EMOM", "interval": "90s", "rounds": 3}`).

### 3. Fix Number Parsing ("50-")

* The current regex likely treats the hyphen in "50-foot" or "50-" as a separator but might be leaving it or misinterpreting it.

* I will update the regex to strictly handle `\d+\s*-\s*` (trailing hyphen) as just the number if it's a rep count, or properly parse "50-foot" as a distance.

* Specifically for "50-foot handstand walk", the parser should see "50" as `distance_meters` (converted from feet) and "handstand walk" as the movement. or for "2-min plank", the parser should see "2" as time in seconds (converted from minutes) and "plank"  as the movement

### 4. Implementation Steps

1. **Modify** **`CrossFitParser`** **class**:

   * Add `extract_circuit_type(text)`: Regex for "AMRAP", "EMOM", "Rounds for time".

   * Add `extract_time_cap(text)`: Regex for "in X minutes", "time cap: X".

   * Update `_parse_line` to handle `50-`or `2-`correctly (strip trailing dashes from numbers).
2. **Update** **`scrape_crossfit_workouts.py`**:

   * Pass the "intro text" (lines before the first exercise) to the new metadata methods.

   * Save `circuit_type`, `time_cap`, `rounds` into the JSON output.
3. **Update** **`ingest_crossfit_circuits.py`**:

   * Map the new fields to the database schema (storing structured metadata in `notes` or a new JSON field if DB schema allows, otherwise appending to description).

This will require a re-scrape (running the script again), which is acceptable as per your instructions.
