I am glad the structural wireframe aligns with your vision. 

Regarding your addition: **You are spot on.** The ability to regress a "Back Squat" to a "Box Squat" (due to fatigue) or progress a "Curtsy Squat" to a "Pistol Squat" (due to skill) is critical for an adaptive coach.

**Good News:** The `MovementRelationship` table **already exists** in your schema (`app/models/movement.py`) and is perfectly structured for this. It supports `relationship_type` (Progression, Regression, Variation). 

I have refined the plan to explicitly leverage this existing table in the "Ensemble Coach" workflow and proceed with the missing pieces.

### Finalized Schema Implementation Plan

1.  **The Anatomy Bridge (Optimization Engine)**
    *   **Action:** Fully expose the `MovementMuscleMap` relationship on `Movement`.
    *   **Benefit:** Enables cumulative load calculation (e.g., "Total Posterior Chain Volume") across disciplines.

2.  **The Internal Fitness Function (Reward Logic)**
    *   **Action:** Add RL/Optimization metrics to `Movement`:
        *   `fatigue_factor` (Float): Systemic cost.
        *   `stimulus_factor` (Float): Growth signal.
        *   `injury_risk_factor` (Float): Base complexity.
        *   `min_recovery_hours` (Int): Recovery decay.

3.  **The Skill Matrix (Personalization)**
    *   **Action:** Create `UserSkill` table (`user_id`, `discipline_id`, `skill_level`, `experience_years`).
    *   **Benefit:** Replaces simple "Global Experience" with granular, discipline-specific capabilities (e.g., Elite Runner, Beginner Lifter).

4.  **Health & Safety (Guardrails)**
    *   **Action:** Create `UserInjury` table (`user_id`, `body_part`, `severity`) instead of a JSON list.
    *   **Benefit:** Allows the Optimization Engine to "hard exclude" dangerous movements via fast SQL joins, rather than slow application-side filtering.

5.  **Raw Activity Ingestion (Physics)**
    *   **Action:** Add physics columns (`distance`, `watts`, `hr`, `elevation`) to `ExternalActivityRecord`.
    *   **Benefit:** Enables instant "Daily Load" calculation without parsing JSON.

6.  **The Adaptation Logic (Leveraging Existing Structure)**
    *   **Strategy:** The system will use the existing `MovementRelationship` table to find substitutes.
    *   **Workflow:** If `UserFatigueState` is high -> Query `MovementRelationship` for `REGRESSION` of planned lift.

I will now implement these schema changes and generate the migration.