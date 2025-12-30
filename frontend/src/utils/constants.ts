/**
 * Application Constants
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Goals (for the Ten-Dollar method)
export const GOALS = [
  { value: 'strength', label: 'Strength', description: 'Max force production' },
  { value: 'hypertrophy', label: 'Hypertrophy', description: 'Muscle growth' },
  { value: 'endurance', label: 'Endurance', description: 'Work capacity' },
  { value: 'fat_loss', label: 'Fat Loss', description: 'Body composition' },
  { value: 'mobility', label: 'Mobility', description: 'Range of motion' },
  { value: 'explosiveness', label: 'Explosiveness', description: 'Power output' },
  { value: 'speed', label: 'Speed', description: 'Movement velocity' },
] as const

// Split Templates
export const SPLIT_TEMPLATES = [
  { value: 'UPPER_LOWER', label: 'Upper/Lower', description: '4 days/week, alternating upper and lower body' },
  { value: 'PPL', label: 'Push/Pull/Legs', description: '6 days/week, Push/Pull/Legs rotation' },
  { value: 'FULL_BODY', label: 'Full Body', description: '3 days/week, whole body each session' },
  { value: 'HYBRID', label: 'Hybrid', description: 'Custom day-by-day or block composition' },
] as const

// Progression Styles
export const PROGRESSION_STYLES = [
  { value: 'SINGLE', label: 'Single Progression', description: 'Increase weight when hitting rep target' },
  { value: 'DOUBLE', label: 'Double Progression', description: 'Increase reps, then weight' },
  { value: 'PAUSED_VARIATIONS', label: 'Paused Variations', description: 'Add pauses for difficulty' },
  { value: 'BUILD_TO_DROP', label: 'Build to Drop', description: 'Build reps, drop and add weight' },
] as const

// Persona Tones
export const PERSONA_TONES = [
  { value: 'supportive', label: 'Supportive', description: 'Encouraging and positive' },
  { value: 'neutral', label: 'Neutral', description: 'Balanced and informative' },
  { value: 'sarcastic', label: 'Sarcastic', description: 'Witty with some edge' },
  { value: 'drill_sergeant', label: 'Drill Sergeant', description: 'No-nonsense, tough love' },
] as const

// Persona Aggression Levels
export const PERSONA_AGGRESSION = [
  { value: 'conservative', label: 'Conservative', description: 'Cautious, lower volume' },
  { value: 'balanced', label: 'Balanced', description: 'Standard recommendations' },
  { value: 'aggressive', label: 'Aggressive', description: 'Push harder, higher volume' },
] as const

// e1RM Formulas
export const E1RM_FORMULAS = [
  { value: 'epley', label: 'Epley', description: 'weight × (1 + reps/30)' },
  { value: 'brzycki', label: 'Brzycki', description: 'weight × 36 / (37 - reps)' },
  { value: 'lombardi', label: 'Lombardi', description: 'weight × reps^0.10' },
  { value: 'oconner', label: "O'Conner", description: 'weight × (1 + reps/40)' },
] as const

// Session Types
export const SESSION_TYPES = [
  { value: 'upper', label: 'Upper Body' },
  { value: 'lower', label: 'Lower Body' },
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Legs' },
  { value: 'full_body', label: 'Full Body' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'mobility', label: 'Mobility' },
  { value: 'rest', label: 'Rest' },
] as const

// Movement Patterns
export const MOVEMENT_PATTERNS = [
  { value: 'squat', label: 'Squat' },
  { value: 'hinge', label: 'Hinge' },
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'carry', label: 'Carry' },
  { value: 'rotation', label: 'Rotation' },
  { value: 'core', label: 'Core' },
  { value: 'conditioning', label: 'Conditioning' },
] as const

// Recovery Sources
export const RECOVERY_SOURCES = [
  { value: 'MANUAL', label: 'Manual Entry' },
  { value: 'GARMIN', label: 'Garmin' },
  { value: 'OURA', label: 'Oura Ring' },
  { value: 'WHOOP', label: 'Whoop' },
  { value: 'APPLE_HEALTH', label: 'Apple Health' },
] as const

// Sleep Quality Options
export const SLEEP_QUALITY = [
  { value: 'poor', label: 'Poor' },
  { value: 'fair', label: 'Fair' },
  { value: 'good', label: 'Good' },
  { value: 'excellent', label: 'Excellent' },
] as const

// Soreness Levels
export const SORENESS_LEVELS = [
  { value: 1, label: 'None', description: 'No soreness' },
  { value: 2, label: 'Mild', description: 'Slight discomfort' },
  { value: 3, label: 'Moderate', description: 'Noticeable soreness' },
  { value: 4, label: 'High', description: 'Significant soreness' },
  { value: 5, label: 'Severe', description: 'Very sore, limited movement' },
] as const

// Body Parts for Soreness
export const BODY_PARTS = [
  'chest',
  'back',
  'shoulders',
  'biceps',
  'triceps',
  'forearms',
  'core',
  'glutes',
  'quadriceps',
  'hamstrings',
  'calves',
  'lower_back',
  'neck',
] as const

// Preference Options for Adaptation
export const ADAPTATION_PREFERENCES = [
  { value: 'lift', label: 'Lift Weights' },
  { value: 'calisthenics', label: 'Calisthenics' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'sport', label: 'Sport Activity' },
  { value: 'any', label: 'No Preference' },
] as const

// Adherence vs Optimality Options
export const ADHERENCE_OPTIONS = [
  { value: 'adherence', label: 'Follow the Plan', description: 'Stick closely to the original program' },
  { value: 'balanced', label: 'Balanced', description: 'Reasonable adaptations' },
  { value: 'optimality', label: 'Optimize for Today', description: 'Best workout given current state' },
] as const

// Program Duration Range
export const PROGRAM_DURATION = {
  min: 8,
  max: 12,
  default: 8,
} as const

// Deload Frequency Options
export const DELOAD_FREQUENCIES = [
  { value: 2, label: 'Every 2 weeks' },
  { value: 3, label: 'Every 3 weeks' },
  { value: 4, label: 'Every 4 weeks (default)' },
  { value: 5, label: 'Every 5 weeks' },
  { value: 6, label: 'Every 6 weeks' },
  { value: 8, label: 'Every 8 weeks' },
] as const

// Breakpoints (matching Tailwind)
export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const
