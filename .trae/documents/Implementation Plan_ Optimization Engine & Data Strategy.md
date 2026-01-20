I have updated the plan to include your expanded list of sports and activities.

### 1. Data Seeding & Cross-Validation
*   **Action**: Create `scripts/enrich_movement_data.py` to logically seed `fatigue_factor`, `stimulus_factor`, etc.
*   **Validation**: Generate `movement_audit.csv` for expert review.

### 2. The Optimization Engine (OR-Tools)
*   **Action**: Implement `ConstraintSolver` service using `ortools`.
*   **Logic**: Maximize Stimulus subject to Fatigue < Capacity and Injury Constraints.

### 3. External Activities (Expanded)
*   **Action**: Create `seed_data/activities.json` with the following comprehensive list:
    *   **Sports**: Tennis, Padel, Pickleball, Golf, Bouldering, Badminton, Squash, Basketball.
    *   **Football**: Indoor Football (6-a-side), 11-a-side Football.
    *   **Water**: Surfing, Kayaking.
    *   **Endurance**: Trail Run, City Run.
    *   **Fitness**: Pilates.
*   **Metrics**: Each will have a `default_metric_type` (e.g., Duration) and a `cns_impact` rating (e.g., Squash = High, Golf = Low) to estimate fatigue when HR/Power data is missing.

### 4. Handling Data Gaps
*   **Action**: Implement `UserFatigueState` logic that accepts manual "Check-in" signals to override estimated decay.

I will start by creating the **Activity Seeding Data** and the **Movement Enrichment Script**.