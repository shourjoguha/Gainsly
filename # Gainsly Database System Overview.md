# Gainsly Database System Overview

This document describes the database schema for Gainsly in detail:

- All core tables and relationships
- All enum types and **all of their allowed values**
- All categorical fields (including columns that store enum values as strings)
- Notes about JSON blobs and free‑text categorical fields

> Important: Some columns are “categorical” in practice but not enforced by the database (e.g. free‑text strings, tags). For those, this document describes the intended category space, but the **actual distinct values** depend on data in your running database.

---

## 1. Technology & Connection

- **Database engine:** PostgreSQL (via SQLAlchemy async engine)
- **Connection URL (app):**  
  `postgresql+asyncpg://gainsly:gainslypass@localhost:5432/gainslydb`
- **Connection URL (tools / psql / GUI):**  
  `postgresql://gainsly:gainslypass@localhost:5432/gainslydb`
- **ORM base:** `app.db.database.Base`  
- **Migrations:** Alembic (`/alembic`)

All tables described below are created via Alembic migrations plus `Base.metadata`.

---

## 2. Global Enums (Authoritative Categorical Spaces)

Defined in [app/models/enums.py](file:///Users/shourjosmac/Documents/Gainsly/app/models/enums.py).

### 2.0 How Enums Are Stored (Important)

Gainsly uses SQLAlchemy `Enum(MyPythonEnum)` for many columns. In the current migrations, those enums are materialized with **the Python enum member names** (typically UPPERCASE) as the allowed database values (example: `HARD_NO`, `PRIVATE`, `SQUAT`). Application code often uses `enum_member.value` (typically lowercase) for prompts and UI.

This section lists **both**:
- **DB values**: what is actually stored/allowed in enum-typed DB columns
- **Semantic values**: the Python `.value` strings used in business logic and prompts

### 2.1 MovementPattern

Used to classify movement patterns.

- Stored as **string** in `movements.pattern` (not DB-enforced; intended to match semantic values).
- Stored as **SQL enum** in `top_set_logs.pattern` and `pattern_exposures.pattern` (DB-enforced).

DB values (enforced in SQL enum columns):
- `SQUAT`
- `HINGE`
- `HORIZONTAL_PUSH`
- `VERTICAL_PUSH`
- `HORIZONTAL_PULL`
- `VERTICAL_PULL`
- `CARRY`
- `CORE`
- `LUNGE`
- `ROTATION`
- `PLYOMETRIC`
- `OLYMPIC`
- `ISOLATION`
- `MOBILITY`
- `ISOMETRIC`
- `CONDITIONING`
- `CARDIO`

Semantic values (Python `.value`, used in prompts/UI):
- `squat`
- `hinge`
- `horizontal_push`
- `vertical_push`
- `horizontal_pull`
- `vertical_pull`
- `carry`
- `core`
- `lunge`
- `rotation`
- `plyometric`
- `olympic`
- `isolation`
- `mobility`
- `isometric`
- `conditioning`
- `cardio`

### 2.2 PrimaryRegion

Body region emphasis:

- `anterior lower`
- `posterior lower`
- `shoulder`
- `anterior upper`
- `posterior upper`
- `full body`
- `lower body`
- `upper body`

### 2.3 PrimaryMuscle

Primary muscular focus:

- `quadriceps`
- `hamstrings`
- `glutes`
- `calves`
- `chest`
- `lats`
- `upper_back`
- `rear_delts`
- `front_delts`
- `side_delts`
- `biceps`
- `triceps`
- `forearms`
- `core`
- `obliques`
- `lower_back`
- `hip_flexors`
- `adductors`
- `full_body`

### 2.4 MetricType

Measurement units for movements:

- `reps`
- `time`
- `time_under_tension`
- `distance`

### 2.5 SkillLevel

Movement skill / complexity:

- `beginner`
- `intermediate`
- `advanced`
- `expert`
- `elite`

### 2.6 CNSLoad

Central nervous system demand:

- `very_low`
- `low`
- `moderate`
- `high`
- `very_high`

### 2.7 Goal

Program goal categories:

DB values:
- `STRENGTH`
- `HYPERTROPHY`
- `ENDURANCE`
- `FAT_LOSS`
- `MOBILITY`
- `EXPLOSIVENESS`
- `SPEED`

Semantic values:
- `strength`
- `hypertrophy`
- `endurance`
- `fat_loss`
- `mobility`
- `explosiveness`
- `speed`

### 2.8 SplitTemplate

Program split styles:

DB values:
- `UPPER_LOWER`
- `PPL` (Push/Pull/Legs)
- `FULL_BODY`
- `HYBRID` (user-customizable)

Semantic values:
- `upper_lower`
- `ppl`
- `full_body`
- `hybrid`

### 2.9 ProgressionStyle

Progression methodology:

DB values:
- `SINGLE_PROGRESSION`
- `DOUBLE_PROGRESSION`
- `PAUSED_VARIATIONS`
- `BUILD_TO_DROP`
- `WAVE_LOADING`

Semantic values:
- `single_progression`
- `double_progression`
- `paused_variations`
- `build_to_drop`
- `wave_loading`

### 2.10 MovementRuleType

User movement preference rules:

DB values:
- `HARD_NO` — never include
- `HARD_YES` — must appear at least once per microcycle
- `PREFERRED` — must appear at least once every 2 weeks

Semantic values:
- `hard_no`
- `hard_yes`
- `preferred`

### 2.11 RuleCadence

Cadence of movement rules:

DB values:
- `PER_MICROCYCLE`
- `WEEKLY`
- `BIWEEKLY`

Semantic values:
- `per_microcycle`
- `weekly`
- `biweekly`

### 2.12 EnjoyableActivity

Enjoyable non‑gym activities:

DB values:
- `TENNIS`
- `BOULDERING`
- `CYCLING`
- `SWIMMING`
- `HIKING`
- `BASKETBALL`
- `FOOTBALL`
- `YOGA`
- `MARTIAL_ARTS`
- `DANCE`
- `OTHER`

Semantic values:
- `tennis`
- `bouldering`
- `cycling`
- `swimming`
- `hiking`
- `basketball`
- `football`
- `yoga`
- `martial_arts`
- `dance`
- `other`

### 2.13 SessionType

Types of training sessions:

DB values:
- `UPPER`
- `LOWER`
- `PUSH`
- `PULL`
- `LEGS`
- `FULL_BODY`
- `CARDIO`
- `MOBILITY`
- `RECOVERY`
- `SKILL`
- `CUSTOM`

Semantic values:
- `upper`
- `lower`
- `push`
- `pull`
- `legs`
- `full_body`
- `cardio`
- `mobility`
- `recovery`
- `skill`
- `custom`

### 2.14 ExerciseRole

Exercise roles within a session:

DB values:
- `WARMUP`
- `MAIN`
- `ACCESSORY`
- `SKILL`
- `FINISHER`
- `COOLDOWN`

Semantic values:
- `warmup`
- `main`
- `accessory`
- `skill`
- `finisher`
- `cooldown`

### 2.15 MicrocycleStatus

Microcycle lifecycle status:

DB values:
- `PLANNED`
- `ACTIVE`
- `COMPLETE`

Semantic values:
- `planned`
- `active`
- `complete`

### 2.16 E1RMFormula

Estimated 1RM calculation formulas:

DB values:
- `EPLEY`
- `BRZYCKI`
- `LOMBARDI`
- `OCONNER`

Semantic values:
- `epley`
- `brzycki`
- `lombardi`
- `oconner`

### 2.17 RecoverySource

Source of recovery data:

DB values:
- `DUMMY`
- `MANUAL`
- `GARMIN`
- `APPLE`
- `AURA_RING`
- `WHOOP_BAND`

Semantic values:
- `dummy`
- `manual`
- `garmin`
- `apple`
- `aura ring`
- `whoop band`

### 2.18 PersonaTone

Coach persona / tone:

DB values:
- `DRILL_SERGEANT`
- `SUPPORTIVE`
- `ANALYTICAL`
- `MOTIVATIONAL`
- `MINIMALIST`

Semantic values:
- `drill_sergeant`
- `supportive`
- `analytical`
- `motivational`
- `minimalist`

### 2.19 RelationshipType

Movement relationship types:

- `progression`
- `regression`
- `variation`
- `antagonist`
- `prep`

### 2.20 CircuitType

Circuit structure types:

DB values:
- `ROUNDS_FOR_TIME`
- `AMRAP`
- `EMOM`
- `LADDER`
- `TABATA`
- `CHIPPER`
- `STATION`

Semantic values:
- `rounds_for_time`
- `amrap`
- `emom`
- `ladder`
- `tabata`
- `chipper`
- `station`

### 2.21 StressBucket

Stress normalization buckets:

- `strength`
- `conditioning`
- `impact_upper`
- `impact_lower`
- `cns`

### 2.22 PersonaAggression

Programming aggressiveness (stored as integer SQL enum):

DB values:
- `CONSERVATIVE` (semantic value: `1`)
- `MODERATE_CONSERVATIVE` (semantic value: `2`)
- `BALANCED` (semantic value: `3`)
- `MODERATE_AGGRESSIVE` (semantic value: `4`)
- `AGGRESSIVE` (semantic value: `5`)

### 2.23 ExperienceLevel

User experience level:

DB values:
- `BEGINNER`
- `INTERMEDIATE`
- `ADVANCED`
- `EXPERT`

Semantic values:
- `beginner`
- `intermediate`
- `advanced`
- `expert`

### 2.24 Visibility

Content visibility:

DB values:
- `PRIVATE`
- `FRIENDS`
- `PUBLIC`

Semantic values:
- `private`
- `friends`
- `public`

---

## 3. Tables and Categorical Columns

This section goes table by table, listing:

- Columns
- Types
- Primary and foreign keys
- Categorical fields and which enum/value sets they use

### 3.1 users

Model: [User](file:///Users/shourjosmac/Documents/Gainsly/app/models/user.py)

- **PK**
  - `id` (Integer, primary key, autoincrement)
- **Identity**
  - `name` (String(100), nullable)
  - `email` (String(255), nullable, unique)
- **Categorical**
  - `experience_level` (SQLEnum(ExperienceLevel), not null, default `INTERMEDIATE`)
    - DB values: `BEGINNER`, `INTERMEDIATE`, `ADVANCED`, `EXPERT`
    - Semantic values: `beginner`, `intermediate`, `advanced`, `expert`
  - `persona_tone` (SQLEnum(PersonaTone), not null, default `SUPPORTIVE`)
    - DB values: `DRILL_SERGEANT`, `SUPPORTIVE`, `ANALYTICAL`, `MOTIVATIONAL`, `MINIMALIST`
    - Semantic values: `drill_sergeant`, `supportive`, `analytical`, `motivational`, `minimalist`
  - `persona_aggression` (SQLEnum(PersonaAggression), not null, default `BALANCED`)
    - DB values: `CONSERVATIVE`, `MODERATE_CONSERVATIVE`, `BALANCED`, `MODERATE_AGGRESSIVE`, `AGGRESSIVE`
    - Semantic values: `1`, `2`, `3`, `4`, `5`
- **Relationships**
  - `movement_rules` → `user_movement_rules`
  - `enjoyable_activities` → `user_enjoyable_activities`
  - `programs` → `programs`
  - `workout_logs` → `workout_logs`
  - `soreness_logs` → `soreness_logs`
  - `recovery_signals` → `recovery_signals`
  - `settings` → `user_settings` (1:1)
  - `conversation_threads` → `conversation_threads`

### 3.2 user_settings

Model: `UserSettings` (same file)

- **PK**
  - `id` (Integer, autoincrement)
- **FK**
  - `user_id` (Integer, FK → users.id, unique)
- **Categorical**
  - `active_e1rm_formula` (SQLEnum(E1RMFormula), not null, default `EPLEY`)
    - DB values: `EPLEY`, `BRZYCKI`, `LOMBARDI`, `OCONNER`
    - Semantic values: `epley`, `brzycki`, `lombardi`, `oconner`
- **Other**
  - `use_metric` (Boolean, default True) — `True` = kg, `False` = lbs

### 3.3 user_movement_rules

Model: `UserMovementRule`

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, indexed)
  - `movement_id` (FK → movements.id, indexed)
- **Categorical**
  - `rule_type` (SQLEnum(MovementRuleType), not null)
    - DB values: `HARD_NO`, `HARD_YES`, `PREFERRED`
    - Semantic values: `hard_no`, `hard_yes`, `preferred`
  - `cadence` (SQLEnum(RuleCadence), not null, default `per_microcycle`)
    - DB values: `PER_MICROCYCLE`, `WEEKLY`, `BIWEEKLY`
    - Semantic values: `per_microcycle`, `weekly`, `biweekly`
- **Other**
  - `notes` (Text, nullable)

### 3.4 user_enjoyable_activities

Model: `UserEnjoyableActivity`

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, indexed)
- **Categorical**
  - `activity_type` (SQLEnum(EnjoyableActivity), not null)
    - DB values: `TENNIS`, `BOULDERING`, `CYCLING`, `SWIMMING`, `HIKING`, `BASKETBALL`, `FOOTBALL`, `YOGA`, `MARTIAL_ARTS`, `DANCE`, `OTHER`
    - Semantic values: `tennis`, `bouldering`, `cycling`, `swimming`, `hiking`, `basketball`, `football`, `yoga`, `martial_arts`, `dance`, `other`
- **Other**
  - `custom_name` (String(100), nullable)
  - `recommend_every_days` (Integer, not null, default 28)
  - `enabled` (Boolean, default True)
  - `notes` (Text, nullable)

---

### 3.5 programs

Model: [Program](file:///Users/shourjosmac/Documents/Gainsly/app/models/program.py)

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, not null, indexed)
- **Identity**
  - `name` (String(100), nullable) — label for historic programs/templates
- **Duration**
  - `start_date` (Date, not null)
  - `duration_weeks` (Integer, not null)
    - Constraint: `8 <= duration_weeks <= 12`
- **Goals (categorical)**
  - `goal_1`, `goal_2`, `goal_3` (SQLEnum(Goal), not null)
    - DB values: `STRENGTH`, `HYPERTROPHY`, `ENDURANCE`, `FAT_LOSS`, `MOBILITY`, `EXPLOSIVENESS`, `SPEED`
    - Semantic values: `strength`, `hypertrophy`, `endurance`, `fat_loss`, `mobility`, `explosiveness`, `speed`
  - `goal_weight_1`, `goal_weight_2`, `goal_weight_3` (Integer, not null)
    - Constraints:
      - Sum to 10: `goal_weight_1 + goal_weight_2 + goal_weight_3 = 10`
      - Each non‑negative: `>= 0`
- **Program structure**
  - `split_template` (SQLEnum(SplitTemplate), not null)
    - DB values: `UPPER_LOWER`, `PPL`, `FULL_BODY`, `HYBRID`
    - Semantic values: `upper_lower`, `ppl`, `full_body`, `hybrid`
  - `days_per_week` (Integer, not null) — expected 2–7 (not enforced by constraint)
  - `progression_style` (SQLEnum(ProgressionStyle), not null)
    - DB values: `SINGLE_PROGRESSION`, `DOUBLE_PROGRESSION`, `PAUSED_VARIATIONS`, `BUILD_TO_DROP`, `WAVE_LOADING`
    - Semantic values: `single_progression`, `double_progression`, `paused_variations`, `build_to_drop`, `wave_loading`
  - `hybrid_definition` (JSON, nullable)  
    - Arbitrary structure describing a custom split.
  - `disciplines_json` (JSON, nullable)  
    - Expected shape: list of `{ "discipline": <str>, "weight": <int> }`.
- **Deload**
  - `deload_every_n_microcycles` (Integer, not null, default 4)
- **Persona snapshot (categorical)**
  - `persona_tone` (SQLEnum(PersonaTone), not null)
  - `persona_aggression` (SQLEnum(PersonaAggression), not null)
- **Status / visibility**
  - `is_active` (Boolean, default True)
  - `is_template` (Boolean, default False)
  - `visibility` (SQLEnum(Visibility), not null, default `private`)
    - DB values: `PRIVATE`, `FRIENDS`, `PUBLIC`
    - Semantic values: `private`, `friends`, `public`
  - `created_at` (DateTime, default now)
- **Relationships**
  - `user` → User
  - `microcycles` → Microcycle (cascade delete)

---

### 3.6 microcycles

Model: `Microcycle`

- **PK**
  - `id`
- **FK**
  - `program_id` (FK → programs.id, not null, indexed)
- **Timing**
  - `start_date` (Date, not null)
  - `length_days` (Integer, not null, constraint `7 <= length_days <= 10`)
  - `sequence_number` (Integer, not null) — 1,2,3...
- **Categorical**
  - `status` (SQLEnum(MicrocycleStatus), not null, default `planned`)
    - DB values: `PLANNED`, `ACTIVE`, `COMPLETE`
    - Semantic values: `planned`, `active`, `complete`
  - `is_deload` (Boolean, default False)
- **Relationships**
  - `program` → Program
  - `sessions` → Session (cascade delete)
  - `pattern_exposures` → PatternExposure (cascade delete)

---

### 3.7 sessions

Model: `Session`

- **PK**
  - `id`
- **FK**
  - `microcycle_id` (FK → microcycles.id, not null, indexed)
  - `main_circuit_id` (FK → circuit_templates.id, nullable)
  - `finisher_circuit_id` (FK → circuit_templates.id, nullable)
- **Scheduling**
  - `date` (Date, not null, indexed)
  - `day_number` (Integer, not null) — 1–10 within microcycle
- **Categorical**
  - `session_type` (SQLEnum(SessionType), not null)
    - Values: `upper`, `lower`, `push`, `pull`, `legs`, `full_body`, `cardio`, `mobility`, `recovery`, `skill`, `custom`
- **Intent tags**
  - `intent_tags` (JSON, default list)  
    - Typical values: strings like `"strength"`, `"hypertrophy"`, etc.  
    - This is an open categorical space; actual distinct values depend on your data.
- **Session content (JSON sections)**
  - `warmup_json` (JSON, nullable)
  - `main_json` (JSON, nullable)
  - `accessory_json` (JSON, nullable)
  - `finisher_json` (JSON, nullable)
  - `cooldown_json` (JSON, nullable)
  - These are arrays of exercise objects; structure is application‑level and not enforced by DB.
- **Source-of-truth note**
  - The LLM session generator currently produces these JSON sections directly (see `SESSION_PLAN_SCHEMA`), while `session_exercises` is a parallel normalized representation. If `session_exercises` is not kept in sync with the JSON sections, any logic reading from `session_exercises` will not reflect what the user sees in the session plan.
- **Time estimation**
  - `estimated_duration_minutes` (Integer, nullable)
  - `warmup_duration_minutes`, `main_duration_minutes`, `accessory_duration_minutes`, `finisher_duration_minutes`, `cooldown_duration_minutes` (Integer, nullable)
- **Coach reasoning**
  - `coach_notes` (Text, nullable)
- **Relationships**
  - `microcycle` → Microcycle
  - `exercises` → SessionExercise
  - `workout_logs` → WorkoutLog
  - `main_circuit`, `finisher_circuit` → CircuitTemplate

---

### 3.8 session_exercises

Model: `SessionExercise`

- **PK**
  - `id`
- **FK**
  - `session_id` (FK → sessions.id, not null, indexed)
  - `movement_id` (FK → movements.id, not null, indexed)
- **Categorical**
  - `role` (SQLEnum(ExerciseRole), not null)
    - Values: `warmup`, `main`, `accessory`, `skill`, `finisher`, `cooldown`
- **Ordering / grouping**
  - `order_in_session` (Integer, not null)
  - `superset_group` (Integer, nullable) — same number indicates supersets.
- **Prescription**
  - `target_sets` (Integer, not null)
  - `target_rep_range_min` (Integer, nullable)
  - `target_rep_range_max` (Integer, nullable)
  - `target_rpe` (Float, nullable)
  - `target_rir` (Integer, nullable)
  - `target_duration_seconds` (Integer, nullable)
- **Rest**
  - `default_rest_seconds` (Integer, nullable)
- **Flags**
  - `is_complex_lift` (Boolean, default False)
  - `substitution_allowed` (Boolean, default True)
- **Notes**
  - `notes` (Text, nullable)

---

### 3.9 movements

Model: [Movement](file:///Users/shourjosmac/Documents/Gainsly/app/models/movement.py)

> Note: This table stores enum values as **string columns**, not SQL enum types. The intended value sets come from the enums above.

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, nullable, indexed)  
    - `NULL` = system movement (global)
    - Non‑null = user‑defined movement
- **Identity**
  - `name` (String(200), not null, unique, indexed)
- **Categorical / classification**
  - `pattern` (String(50), not null, indexed)
    - Intended values: **MovementPattern** enum values:
      - `squat`, `hinge`, `horizontal_push`, `vertical_push`, `horizontal_pull`, `vertical_pull`, `carry`, `core`, `lunge`, `rotation`, `plyometric`, `olympic`, `isolation`, `mobility`, `isometric`, `conditioning`, `cardio`
  - `primary_muscle` (String(50), not null, indexed)
    - Intended values: **PrimaryMuscle** enum values.
  - `primary_region` (String(50), not null, indexed)
    - Intended values: **PrimaryRegion** enum values.
  - `secondary_muscles` (JSON, default list)
    - Array of strings, each intended to be a **PrimaryMuscle** value.
- **Load and complexity**
  - `cns_load` (String(50), not null, default `"moderate"`)
    - Intended values: **CNSLoad** enum values (`very_low`, `low`, `moderate`, `high`, `very_high`).
  - `skill_level` (String(50), not null, default `"intermediate"`)
    - Intended values: **SkillLevel** enum values.
- **Movement characteristics**
  - `compound` (Boolean, default True)
  - `is_complex_lift` (Boolean, default False)
  - `is_unilateral` (Boolean, default False)
- **Measurement**
  - `metric_type` (String(50), not null, default `"reps"`)
    - Intended values: **MetricType** enum values (`reps`, `time`, `time_under_tension`, `distance`).
- **Additional categorization**
  - `primary_discipline` (String(50), not null, default `"All"`, server_default `"All"`)
    - Open categorical; typical values: `"All"`, `"powerlifting"`, `"crossfit"`, etc. Distinct values depend on data.
  - `discipline_tags` (JSON, default list)
    - Example values: `"powerlifting"`, `"olympic"`, `"calisthenics"`, `"crossfit"` (open set).
  - `equipment_tags` (JSON, default list)
    - Example values: `"barbell"`, `"dumbbell"`, `"bodyweight"`, `"kettlebell"`, etc.
  - `tags` (JSON, default list)
    - General tags like `"crossfit"`, `"athletic"`, `"mobility"` — open set.
- **Description**
  - `description` (Text, nullable)
  - `coaching_cues` (JSON, default list) — array of strings.
- **Substitution helper**
  - `substitution_group` (String(100), nullable, indexed)  
    - Example: `"single_arm_row"` grouping similar movements.
- **Relationships**
  - `user_rules` → UserMovementRule
  - `session_exercises` → SessionExercise
  - `top_set_logs` → TopSetLog
  - `outgoing_relationships` / `incoming_relationships` → MovementRelationship

---

### 3.10 movement_relationships

Model: `MovementRelationship`

- **PK**
  - `id`
- **FK**
  - `source_movement_id` (FK → movements.id, not null, indexed)
  - `target_movement_id` (FK → movements.id, not null, indexed)
- **Categorical**
  - `relationship_type` (String(50), not null, indexed)
    - Intended values: **RelationshipType**:
      - `progression`, `regression`, `variation`, `antagonist`, `prep`
- **Other**
  - `notes` (Text, nullable)

---

### 3.11 circuit_templates

Model: [CircuitTemplate](file:///Users/shourjosmac/Documents/Gainsly/app/models/circuit.py)

- **PK**
  - `id`
- **Identity**
  - `name` (String(200), not null, indexed)
  - `description` (Text, nullable)
- **Categorical**
  - `circuit_type` (SQLEnum(CircuitType), not null)
    - Values: `rounds_for_time`, `amrap`, `emom`, `ladder`, `tabata`, `chipper`, `station`
- **Structure**
  - `exercises_json` (JSON, not null, default list)
    - Contains the detailed circuit structure (rounds, reps, movements).
  - `default_rounds` (Integer, nullable)
  - `default_duration_seconds` (Integer, nullable)
- **Stress & tags**
  - `bucket_stress` (JSON, not null, default dict)
    - Typically maps **StressBucket** values to numeric intensities, e.g. `{ "strength": 5, "conditioning": 3 }`.
  - `tags` (JSON, default list)
    - Free‑form tags: e.g., `"crossfit"`, `"hyrox"`, `"hero_wod"`.
- **Difficulty**
  - `difficulty_tier` (Integer, default 1) — internal difficulty scale.

---

### 3.12 workout_logs

Model: [WorkoutLog](file:///Users/shourjosmac/Documents/Gainsly/app/models/logging.py)

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, not null, indexed)
  - `session_id` (FK → sessions.id, nullable, indexed)
- **Completion**
  - `date` (Date, not null, indexed)
  - `completed` (Boolean, not null, default True)
- **Feedback (categorical / numeric)**
  - `notes` (Text, nullable)
  - `perceived_difficulty` (Integer, nullable) — 1–10 (not enforced in DB)
  - `enjoyment_rating` (Integer, nullable) — 1–5 (not enforced)
  - `feedback_tags` (JSON, default list)
    - Open categorical tags, e.g. `"too_hard"`, `"boring"`, `"too_much_cardio"`.
- **Timing**
  - `actual_duration_minutes` (Integer, nullable)
- **Visibility**
  - `visibility` (SQLEnum(Visibility), not null, default `private`)
- **Timestamps**
  - `created_at` (DateTime, default now)
- **Relationships**
  - `user` → User
  - `session` → Session
  - `top_sets` → TopSetLog

---

### 3.13 top_set_logs

Model: `TopSetLog`

- **PK**
  - `id`
- **FK**
  - `workout_log_id` (FK → workout_logs.id, not null, indexed)
  - `movement_id` (FK → movements.id, not null, indexed)
- **Performance data**
  - `weight` (Float, not null)
  - `reps` (Integer, not null)
  - `rpe` (Float, nullable)
  - `rir` (Integer, nullable)
  - `avg_rest_seconds` (Integer, nullable)
- **Calculated metrics (categorical + numeric)**
  - `e1rm_value` (Float, nullable)
  - `e1rm_formula` (SQLEnum(E1RMFormula), nullable)
    - Values: `epley`, `brzycki`, `lombardi`, `oconner`
- **Denormalized categorical**
  - `pattern` (SQLEnum(MovementPattern), not null, indexed)
    - Values: see MovementPattern enum
- **Timestamps**
  - `created_at` (DateTime, default now)

---

### 3.14 pattern_exposures

Model: `PatternExposure`

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, not null, indexed)
  - `microcycle_id` (FK → microcycles.id, not null, indexed)
  - `source_top_set_log_id` (FK → top_set_logs.id, not null)
- **Categorical**
  - `pattern` (SQLEnum(MovementPattern), not null, indexed)
    - Values: see MovementPattern enum
- **Metrics**
  - `date` (Date, not null, indexed)
  - `e1rm_value` (Float, not null)
- **Timestamps**
  - `created_at` (DateTime, default now)

---

### 3.15 soreness_logs

Model: `SorenessLog`

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, not null, indexed)
  - `inferred_cause_session_id` (FK → sessions.id, nullable)
- **Categorical**
  - `body_part` (String(50), not null)
    - Open categorical; examples: `"quads"`, `"hamstrings"`, `"lower_back"`.
    - Actual distinct values come from user input.
  - `soreness_1_5` (Integer, not null) — expected 1–5 (not enforced in DB).
- **Other**
  - `date` (Date, not null, indexed)
  - `notes` (Text, nullable)
  - `created_at` (DateTime, default now)

---

### 3.16 recovery_signals

Model: `RecoverySignal`

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, not null, indexed)
  - `session_id` (FK → sessions.id, nullable)
- **Timing**
  - `date` (Date, not null, indexed)
- **Categorical**
  - `source` (SQLEnum(RecoverySource), not null, default `dummy`)
    - Values: `dummy`, `manual`, `garmin`, `apple`, `aura ring`, `whoop band`
- **Metrics**
  - `hrv` (Float, nullable)
  - `resting_hr` (Integer, nullable)
  - `sleep_score` (Float, nullable)
  - `sleep_hours` (Float, nullable)
  - `readiness` (Float, nullable)
- **Notes**
  - `notes` (Text, nullable)
- **Timestamps**
  - `created_at` (DateTime, default now)

---

### 3.17 heuristic_configs

Model: [HeuristicConfig](file:///Users/shourjosmac/Documents/Gainsly/app/models/config.py)

- **PK**
  - `id`
- **Identity**
  - `name` (String(100), not null, indexed)
  - `version` (Integer, not null)
- **Config data**
  - `json_blob` (JSON, not null)
  - `description` (Text, nullable)
- **Categorical / flags**
  - `active` (Boolean, default False, indexed)
- **Timestamps**
  - `created_at` (DateTime, default now)

---

### 3.18 conversation_threads

Model: `ConversationThread`

- **PK**
  - `id`
- **FK**
  - `user_id` (FK → users.id, not null, indexed)
  - `context_session_id` (FK → sessions.id, nullable)
- **Categorical (string)**
  - `context_type` (String(50), not null)
    - Intended categorical values (not enforced):
      - `"daily_adaptation"`
      - `"program_setup"`
      - Other future thread types. Distinct values depend on data.
- **Context**
  - `context_date` (DateTime, nullable)
- **Status / flags**
  - `is_active` (Boolean, default True)
  - `final_plan_accepted` (Boolean, default False)
- **Accepted plan snapshot**
  - `accepted_plan_json` (JSON, nullable)
- **Timestamps**
  - `created_at` (DateTime, default now)
  - `updated_at` (DateTime, default now, auto‑updated)
- **Relationships**
  - `user` → User
  - `turns` → ConversationTurn

---

### 3.19 conversation_turns

Model: `ConversationTurn`

- **PK**
  - `id`
- **FK**
  - `thread_id` (FK → conversation_threads.id, not null, indexed)
- **Categorical**
  - `role` (String(20), not null)
    - Intended values:
      - `"user"`
      - `"assistant"`
    - This is effectively a small enum, but represented as plain string.
- **Turn info**
  - `turn_number` (Integer, not null)
  - `content` (Text, not null)
  - `structured_response_json` (JSON, nullable)
- **Timestamps**
  - `created_at` (DateTime, default now)

---

## 4. Summary of Categorical Columns by Source

### 4.1 True SQL Enums in Columns

These are literal SQL Enum types:

- `users.experience_level` → ExperienceLevel
- `users.persona_tone` → PersonaTone
- `users.persona_aggression` → PersonaAggression
- `user_settings.active_e1rm_formula` → E1RMFormula
- `user_movement_rules.rule_type` → MovementRuleType
- `user_movement_rules.cadence` → RuleCadence
- `user_enjoyable_activities.activity_type` → EnjoyableActivity
- `programs.goal_1`, `goal_2`, `goal_3` → Goal
- `programs.split_template` → SplitTemplate
- `programs.progression_style` → ProgressionStyle
- `programs.persona_tone` → PersonaTone
- `programs.persona_aggression` → PersonaAggression
- `programs.visibility` → Visibility
- `microcycles.status` → MicrocycleStatus
- `sessions.session_type` → SessionType
- `session_exercises.role` → ExerciseRole
- `workout_logs.visibility` → Visibility
- `top_set_logs.e1rm_formula` → E1RMFormula
- `top_set_logs.pattern` → MovementPattern
- `pattern_exposures.pattern` → MovementPattern
- `recovery_signals.source` → RecoverySource
- `circuit_templates.circuit_type` → CircuitType

### 4.2 Enum-Backed String Columns

These store enum values as strings (no SQL enum constraint, but application logic expects specific sets):

- `movements.pattern` → MovementPattern values
- `movements.primary_muscle` → PrimaryMuscle values
- `movements.primary_region` → PrimaryRegion values
- `movements.cns_load` → CNSLoad values
- `movements.skill_level` → SkillLevel values
- `movements.metric_type` → MetricType values
- `movement_relationships.relationship_type` → RelationshipType values
- `movement.secondary_muscles` (JSON array) → PrimaryMuscle values

### 4.3 Open Categorical / Free-Text Fields

These are conceptually categorical but not bounded by code:

- `movements.primary_discipline` (String, default `"All"`)
- `movements.discipline_tags` (JSON array)
- `movements.equipment_tags` (JSON array)
- `movements.tags` (JSON array)
- `sessions.intent_tags` (JSON array of strings)
- `workout_logs.feedback_tags` (JSON array)
- `soreness_logs.body_part` (String)
- `conversation_threads.context_type` (String)
- `conversation_turns.role` (String: effectively `"user"` / `"assistant"`)

Actual **distinct values** for these fields can be inspected directly in the database using SQL or a GUI client.

---

## 5. How to Inspect Actual Unique Values

For open or enum‑backed string columns, you can see the **real** unique values currently stored in your DB with SQL:

Examples (run in `psql` or GUI):

```sql
-- Unique movement patterns actually present in DB
SELECT DISTINCT pattern FROM movements ORDER BY pattern;

-- Unique primary_discipline values
SELECT DISTINCT primary_discipline FROM movements ORDER BY primary_discipline;

-- Unique body parts logged for soreness
SELECT DISTINCT body_part FROM soreness_logs ORDER BY body_part;

-- Unique conversation thread types
SELECT DISTINCT context_type FROM conversation_threads ORDER BY context_type;
```

For JSON arrays (e.g. tags, discipline_tags), you can unnest them (PostgreSQL):

```sql
-- All distinct equipment tags
SELECT DISTINCT tag
FROM movements,
LATERAL jsonb_array_elements_text(equipment_tags::jsonb) AS tag
ORDER BY tag;
```

This will give you a true data‑driven list of categorical values currently in use, complementing the **design‑time enums** documented above.
