/**
 * API Request and Response types
 * Directly mapped from backend schemas in app/schemas/
 */

// ============== Enums ==============
export type Goal = 'strength' | 'hypertrophy' | 'endurance' | 'fat_loss' | 'mobility' | 'explosiveness' | 'speed'
export type SplitTemplate = 'upper_lower' | 'ppl' | 'full_body' | 'hybrid'
export type ProgressionStyle = 'single_progression' | 'double_progression' | 'paused_variations' | 'build_to_drop'
export type PersonaTone = 'supportive' | 'neutral' | 'sarcastic' | 'drill_sergeant'
export type PersonaAggression = 'conservative' | 'balanced' | 'aggressive'
export type SessionType = 'upper' | 'lower' | 'push' | 'pull' | 'legs' | 'full_body' | 'cardio' | 'mobility' | 'rest'
export type MicrocycleStatus = 'PLANNED' | 'ACTIVE' | 'COMPLETED' | 'DELOAD'
export type E1RMFormula = 'epley' | 'brzycki' | 'lombardi' | 'oconner'
export type ExperienceLevel = 'beginner' | 'intermediate' | 'advanced' | 'elite'
export type MovementPattern = 'squat' | 'hinge' | 'push' | 'pull' | 'carry' | 'rotation' | 'core' | 'conditioning'
export type PrimaryRegion = 'upper_body' | 'lower_body' | 'core' | 'full_body'
export type RecoverySource = 'MANUAL' | 'GARMIN' | 'OURA' | 'WHOOP' | 'APPLE_HEALTH'

// ============== Program Schemas ==============

export interface GoalWeight {
  goal: Goal
  weight: number
}

export interface HybridDayDefinition {
  day: number
  session_type: SessionType
  focus?: string[]
  notes?: string
}

export interface HybridBlockComposition {
  blocks: string[]
}

export interface HybridDefinition {
  mode: 'day_by_day' | 'block_composition'
  days?: HybridDayDefinition[]
  composition?: HybridBlockComposition
}

export interface MovementRuleCreate {
  movement_id: number
  rule_type: 'hard_no' | 'hard_yes' | 'preferred'
  cadence?: 'per_microcycle' | 'weekly' | 'biweekly'
  notes?: string
}

export interface EnjoyableActivityCreate {
  activity_type: string
  custom_name?: string
  recommend_every_days?: number
}

export interface ProgramCreate {
  goals: GoalWeight[]
  duration_weeks: number
  program_start_date?: string
  split_template: SplitTemplate
  progression_style: ProgressionStyle
  hybrid_definition?: HybridDefinition
  deload_every_n_microcycles?: number
  persona_tone?: PersonaTone
  persona_aggression?: PersonaAggression
  movement_rules?: MovementRuleCreate[]
  enjoyable_activities?: EnjoyableActivityCreate[]
}

export interface ProgramResponse {
  id: number
  user_id: number
  program_start_date?: string
  duration_weeks: number
  goal_1: Goal
  goal_2: Goal
  goal_3: Goal
  goal_weight_1: number
  goal_weight_2: number
  goal_weight_3: number
  split_template: SplitTemplate
  progression_style: ProgressionStyle
  hybrid_definition?: Record<string, any>
  deload_every_n_microcycles: number
  persona_tone?: PersonaTone
  persona_aggression?: PersonaAggression
  is_active: boolean
  created_at?: string
}

// ============== Microcycle Schemas ==============

export interface MicrocycleResponse {
  id: number
  program_id: number
  micro_start_date?: string
  length_days: number
  sequence_number: number
  status: MicrocycleStatus
  is_deload: boolean
}

// ============== Session Schemas ==============

export interface ExerciseBlock {
  movement: string
  movement_id?: number
  sets: number
  rep_range_min?: number
  rep_range_max?: number
  target_rpe?: number
  target_rir?: number
  duration_seconds?: number
  rest_seconds?: number
  superset_with?: string
  notes?: string
}

export interface FinisherBlock {
  type: string
  duration_minutes?: number
  rounds?: number
  exercises?: ExerciseBlock[]
  notes?: string
}

export interface SessionResponse {
  id: number
  microcycle_id: number
  session_date?: string
  day_number: number
  session_type: SessionType
  intent_tags: string[]
  warmup?: ExerciseBlock[]
  main?: ExerciseBlock[]
  accessory?: ExerciseBlock[]
  finisher?: FinisherBlock
  cooldown?: ExerciseBlock[]
  estimated_duration_minutes?: number
  warmup_duration_minutes?: number
  main_duration_minutes?: number
  accessory_duration_minutes?: number
  finisher_duration_minutes?: number
  cooldown_duration_minutes?: number
  coach_notes?: string
}

export interface ProgramWithMicrocycleResponse {
  program: ProgramResponse
  active_microcycle?: MicrocycleResponse
  upcoming_sessions: SessionResponse[]
}

// ============== Daily Plan Schemas ==============

export interface DailyPlanResponse {
  plan_date?: string
  session?: SessionResponse
  is_rest_day: boolean
  recommended_activities?: string[]
  coach_message?: string
}

// ============== Adaptation Schemas ==============

export interface SorenessInput {
  body_part: string
  level: number
}

export interface RecoveryInput {
  sleep_quality?: 'poor' | 'fair' | 'good' | 'excellent'
  sleep_hours?: number
  energy_level?: number
  stress_level?: number
  notes?: string
}

export interface AdaptationRequest {
  program_id: number
  focus_for_today?: string
  preference?: 'lift' | 'calisthenics' | 'cardio' | 'sport' | 'any'
  excluded_movements?: string[]
  excluded_patterns?: string[]
  time_available_minutes?: number
  soreness?: SorenessInput[]
  recovery?: RecoveryInput
  activity_yesterday?: string
  adherence_vs_optimality?: 'adherence' | 'optimality' | 'balanced'
  persona_tone_override?: PersonaTone
  persona_aggression_override?: PersonaAggression
  thread_id?: number
  user_message?: string
}

export interface AdaptedSessionPlan {
  warmup?: ExerciseBlock[]
  main?: ExerciseBlock[]
  accessory?: ExerciseBlock[]
  finisher?: FinisherBlock
  cooldown?: ExerciseBlock[]
  estimated_duration_minutes: number
  reasoning: string
  trade_offs?: string
}

export interface AdaptationResponse {
  plan_date?: string
  original_session_type?: SessionType
  adapted_plan?: AdaptedSessionPlan
  changes_made: string[]
  reasoning: string
  trade_offs?: string
  alternative_suggestion?: string
  follow_up_question?: string
  thread_id?: number
}

export interface ConversationTurnResponse {
  turn_number: number
  role: string
  content: string
  structured_response?: Record<string, any>
}

export interface ConversationThreadResponse {
  id: number
  context_type: string
  context_date?: string
  is_active: boolean
  final_plan_accepted: boolean
  turns: ConversationTurnResponse[]
  accepted_plan?: AdaptedSessionPlan
}

export interface AcceptPlanRequest {
  thread_id: number
}

export interface AcceptPlanResponse {
  success: boolean
  session_id?: number
  message: string
}

// ============== Logging Schemas ==============

export interface TopSetCreate {
  movement_id: number
  weight: number
  reps: number
  rpe?: number
  rir?: number
  avg_rest_seconds?: number
}

export interface TopSetResponse {
  id: number
  movement_id: number
  movement_name?: string
  weight: number
  reps: number
  rpe?: number
  rir?: number
  avg_rest_seconds?: number
  e1rm?: number
  e1rm_value?: number
  e1rm_formula?: E1RMFormula
  pattern?: MovementPattern
  is_pr: boolean
  created_at?: string
}

export interface WorkoutLogCreate {
  session_id?: number
  log_date?: string
  started_at?: string
  ended_at?: string
  completed?: boolean
  top_sets?: TopSetCreate[]
  exercises_completed?: Record<string, any>[]
  notes?: string
  perceived_exertion?: number
  perceived_difficulty?: number
  energy_level?: number
  adherence_percentage?: number
  coach_feedback_request?: string
  actual_duration_minutes?: number
}

export interface WorkoutLogResponse {
  id: number
  user_id?: number
  session_id?: number
  log_date?: string
  started_at?: string
  ended_at?: string
  completed: boolean
  notes?: string
  perceived_exertion?: number
  perceived_difficulty?: number
  energy_level?: number
  adherence_percentage?: number
  coach_feedback_request?: string
  exercises_completed?: Record<string, any>[]
  actual_duration_minutes?: number
  top_sets: TopSetResponse[]
  created_at?: string
}

export interface WorkoutLogListResponse {
  logs: WorkoutLogResponse[]
  total: number
  limit: number
  offset: number
}

export interface WorkoutLogSummary {
  workout_log: WorkoutLogResponse
  pattern_exposures_created: number
  psi_updates: Record<string, number | null>
}

export interface SorenessLogCreate {
  log_date?: string
  body_part: string
  soreness_1_5: number
  notes?: string
}

export interface SorenessLogResponse {
  id: number
  user_id?: number
  log_date?: string
  body_part: string
  soreness_1_5: number
  inferred_cause_session_id?: number
  inferred_cause_description?: string
  notes?: string
  created_at?: string
}

export interface RecoverySignalCreate {
  log_date?: string
  session_id?: number
  source?: RecoverySource
  hrv?: number
  resting_hr?: number
  sleep_score?: number
  sleep_hours?: number
  readiness?: number
  raw_payload?: Record<string, any>
  notes?: string
}

export interface RecoverySignalResponse {
  id: number
  user_id?: number
  log_date?: string
  session_id?: number
  source: RecoverySource
  hrv?: number
  resting_hr?: number
  sleep_score?: number
  sleep_hours?: number
  readiness?: number
  notes?: string
  created_at?: string
}

export interface PatternPSIResponse {
  pattern: MovementPattern
  psi_value?: number
  exposure_count: number
  trend?: string
}

export interface ProgressSummaryResponse {
  user_id: number
  as_of_date: string
  pattern_psi: PatternPSIResponse[]
  recent_workouts_count: number
  total_volume_last_week?: number
  deload_recommended: boolean
  declining_patterns: MovementPattern[]
}

// ============== Settings Schemas ==============

export interface UserSettingsUpdate {
  active_e1rm_formula?: E1RMFormula
  e1rm_formula?: string
  use_metric?: boolean
  preferred_units?: string
  persona_coaching_style?: string
  persona_strictness?: number
  persona_humor?: number
  persona_explanation_level?: number
  notification_preference?: string
  default_session_duration_minutes?: number
}

export interface UserSettingsResponse {
  id: number
  user_id?: number
  active_e1rm_formula?: E1RMFormula
  e1rm_formula?: string
  use_metric?: boolean
  preferred_units?: string
  persona_coaching_style?: string
  persona_strictness?: number
  persona_humor?: number
  persona_explanation_level?: number
  notification_preference?: string
  default_session_duration_minutes?: number
}

export interface UserProfileUpdate {
  name?: string
  experience_level?: ExperienceLevel
  persona_tone?: PersonaTone
  persona_aggression?: PersonaAggression
}

export interface UserProfileResponse {
  id: number
  name?: string
  email?: string
  experience_level: ExperienceLevel
  persona_tone: PersonaTone
  persona_aggression: PersonaAggression
}

export interface MovementResponse {
  id: number
  name: string
  pattern?: string
  primary_pattern?: MovementPattern
  secondary_patterns?: string[]
  primary_muscle?: string
  primary_muscles?: string[]
  secondary_muscles?: string[]
  primary_region?: PrimaryRegion | string
  default_equipment?: string
  complexity?: number
  cns_load?: string
  cns_demand?: number
  skill_level?: number
  compound?: boolean
  is_compound?: boolean
  is_complex_lift?: boolean
  is_unilateral?: boolean
  metric_type?: string
  discipline_tags?: string[]
  equipment_tags?: string[]
  substitution_group?: string
  description?: string
}

export interface MovementListResponse {
  movements: MovementResponse[]
  total: number
  limit?: number
  offset?: number
  filters_applied?: Record<string, any>
}

export interface HeuristicConfigResponse {
  id: number
  name?: string
  key?: string
  category?: string
  version?: number
  json_blob?: Record<string, any>
  value?: Record<string, any>
  description?: string
  active?: boolean
  created_at?: string
}

export interface HeuristicConfigListResponse {
  configs: HeuristicConfigResponse[]
}

export interface MovementRuleResponse {
  id: number
  user_id?: number
  movement_id: number
  movement_name?: string
  rule_type: string
  substitute_movement_id?: number
  substitute_movement_name?: string
  cadence?: string
  reason?: string
  notes?: string
}

export interface MovementRuleUpdate {
  rule_type?: string
  substitute_movement_id?: number
  cadence?: string
  reason?: string
  notes?: string
}

export interface EnjoyableActivityResponse {
  id: number
  user_id?: number
  activity_name?: string
  activity_type?: string
  category?: string
  custom_name?: string
  typical_duration_minutes?: number
  recommend_every_days?: number
  enabled?: boolean
  notes?: string
}

export interface EnjoyableActivityUpdate {
  activity_name?: string
  category?: string
  typical_duration_minutes?: number
  recommend_every_days?: number
  enabled?: boolean
  notes?: string
}

// ============== SSE Event Types ==============

export interface SSEEvent {
  type: 'recovery_score' | 'thread_id' | 'content' | 'error' | 'done'
  data: any
}
