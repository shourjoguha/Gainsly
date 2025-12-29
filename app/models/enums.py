"""Enum definitions for database models."""
from enum import Enum


class MovementPattern(str, Enum):
    """Movement pattern categories."""
    SQUAT = "squat"
    HINGE = "hinge"
    HORIZONTAL_PUSH = "horizontal_push"
    VERTICAL_PUSH = "vertical_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PULL = "vertical_pull"
    CARRY = "carry"
    CORE = "core"
    LUNGE = "lunge"
    ROTATION = "rotation"
    PLYOMETRIC = "plyometric"
    OLYMPIC = "olympic"
    ISOLATION = "isolation"
    MOBILITY = "mobility"
    ISOMETRIC = "isometric"

class PrimaryRegion(str, Enum):
    ANTERIOR_LOWER = "anterior lower"
    POSTERIOR_LOWER = "posterior lower"
    SHOULDER = "shoulder"
    ANTERIOR_UPPER = "anterior upper"
    POSTERIOR_UPPER = "anterrior lower"
    FULL_BODY = "full body"

class PrimaryMuscle(str, Enum):
    """Primary muscle groups."""
    QUADRICEPS = "quadriceps"    
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    CHEST = "chest"
    LATS = "lats"
    UPPER_BACK = "upper_back"
    REAR_DELTS = "rear_delts"
    FRONT_DELTS = "front_delts"
    SIDE_DELTS = "side_delts"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    CORE = "core"
    OBLIQUES = "obliques"
    LOWER_BACK = "lower_back"
    HIP_FLEXORS = "hip_flexors"
    ADDUCTORS = "adductors"
    ABDUCTORS = "abductors"
    FULL_BODY = "full_body"


class MetricType(str, Enum):
    """How the movement is measured."""
    REPS = "reps"
    TIME = "time"
    TIME_UNDER_TENSION = "time_under_tension"
    DISTANCE = "distance"


class SkillLevel(int, Enum):
    """Movement skill/complexity level."""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    ELITE = 5


class CNSLoad(str, Enum):
    """Central nervous system load category."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Goal(str, Enum):
    """Training goals."""
    STRENGTH = "strength"
    HYPERTROPHY = "hypertrophy"
    ENDURANCE = "endurance"
    FAT_LOSS = "fat_loss"
    MOBILITY = "mobility"
    EXPLOSIVENESS = "explosiveness"
    SPEED = "speed"


class SplitTemplate(str, Enum):
    """Program split templates."""
    UPPER_LOWER = "upper_lower"
    PPL = "ppl"  # Push/Pull/Legs
    FULL_BODY = "full_body"
    HYBRID = "hybrid"  # User-customizable


class ProgressionStyle(str, Enum):
    """Progression methodologies."""
    SINGLE_PROGRESSION = "single_progression"  # Increase weight when hitting rep target
    DOUBLE_PROGRESSION = "double_progression"  # Increase reps then weight
    PAUSED_VARIATIONS = "paused_variations"  # Add pauses for progression
    BUILD_TO_DROP = "build_to_drop"  # Build to rep range, drop reps + increase load


class MovementRuleType(str, Enum):
    """User movement preference rules."""
    HARD_NO = "hard_no"  # Never include
    HARD_YES = "hard_yes"  # Must appear at least once per microcycle
    PREFERRED = "preferred"  # Must appear at least once every 2 weeks


class RuleCadence(str, Enum):
    """Cadence for movement rules."""
    PER_MICROCYCLE = "per_microcycle"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"


class EnjoyableActivity(str, Enum):
    """Enjoyable activities for recommendations."""
    TENNIS = "tennis"
    BOULDERING = "bouldering"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    HIKING = "hiking"
    BASKETBALL = "basketball"
    FOOTBALL = "football"
    YOGA = "yoga"
    MARTIAL_ARTS = "martial_arts"
    DANCE = "dance"
    OTHER = "other"


class SessionType(str, Enum):
    """Types of training sessions."""
    UPPER = "upper"
    LOWER = "lower"
    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"
    FULL_BODY = "full_body"
    CARDIO = "cardio"
    MOBILITY = "mobility"
    RECOVERY = "recovery"
    SKILL = "skill"
    CUSTOM = "custom"


class ExerciseRole(str, Enum):
    """Role of exercise within a session."""
    WARMUP = "warmup"
    MAIN = "main"
    ACCESSORY = "accessory"
    SKILL = "skill"
    FINISHER = "finisher"
    COOLDOWN = "cooldown"


class MicrocycleStatus(str, Enum):
    """Status of a microcycle."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETE = "complete"


class E1RMFormula(str, Enum):
    """Estimated 1RM calculation formulas."""
    EPLEY = "epley"
    BRZYCKI = "brzycki"
    LOMBARDI = "lombardi"
    OCONNER = "oconner"


class RecoverySource(str, Enum):
    """Source of recovery signals."""
    DUMMY = "dummy"
    MANUAL = "manual"
    GARMIN = "garmin"
    APPLE = "apple"
    AURA_RING = "aura ring"
    WHOOP_BAND = "whoop band"

class PersonaTone(str, Enum):
    """Coach communication tone presets."""
    DRILL_SERGEANT = "drill_sergeant"
    SUPPORTIVE = "supportive"
    ANALYTICAL = "analytical"
    MOTIVATIONAL = "motivational"
    MINIMALIST = "minimalist"


class PersonaAggression(int, Enum):
    """Programming aggressiveness level (1-5)."""
    CONSERVATIVE = 1
    MODERATE_CONSERVATIVE = 2
    BALANCED = 3
    MODERATE_AGGRESSIVE = 4
    AGGRESSIVE = 5


class ExperienceLevel(str, Enum):
    """User experience level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
