import asyncio
import json
import math
import os
import re
import sys
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from difflib import SequenceMatcher

sys.path.insert(0, os.getcwd())

from app.db.database import async_session_maker
from app.models import (
    Movement,
    MovementPattern,
    PrimaryMuscle,
    PrimaryRegion,
    MetricType,
    SkillLevel,
    CNSLoad,
)


EXERCISES_URL = "https://raw.githubusercontent.com/exercemus/exercises/minified/minified-exercises.json"
OUTPUT_DIR = Path(__file__).parent.parent / "seed_data"
AMBIGUOUS_PATH = OUTPUT_DIR / "exercemus_ambiguous_candidates.json"
LOW_SCORE_PATH = OUTPUT_DIR / "exercemus_low_score_samples.json"
SUMMARY_PATH = OUTPUT_DIR / "exercemus_import_summary.json"
INVALID_PATH = OUTPUT_DIR / "exercemus_invalid_candidates.json"


EQUIPMENT_TERMS = [
    "barbell",
    "dumbbell",
    "kettlebell",
    "machine",
    "smith",
    "smith machine",
    "cable",
    "band",
    "resistance band",
    "bodyweight",
    "trap bar",
    "ez bar",
    "sled",
    "lever",
    "leverage",
]

MODIFIER_TERMS = [
    "high bar",
    "low bar",
    "wide stance",
    "narrow stance",
    "heels elevated",
    "paused",
    "pause",
    "tempo",
    "standing",
    "seated",
    "incline",
    "decline",
    "flat",
    "single arm",
    "single leg",
    "one arm",
    "one leg",
]


BODYWEIGHT_TERMS = ["bodyweight", "no equipment"]


NAME_TOKEN_SYNONYMS = {
    "roller": "rollout",
    "bw": "bodyweight",
    "db": "dumbbell",
    "kb": "kettlebell",
    "bar": "barbell",
}


def normalize_text_strict(text: str) -> str:
    # Replace separators with space
    text = re.sub(r'[-_/]', ' ', text)
    # Remove non-alphanumeric
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text.lower().strip()


@dataclass
class MovementCandidate:
    source_name: str
    source_aliases: List[str]
    canonical_base_name: str
    canonical_name_key: str
    pattern: str
    primary_muscle: str
    secondary_muscles: List[str]
    primary_region: str
    discipline_tags: List[str]
    equipment_tags: List[str]
    metric_type: str
    skill_level: str
    cns_load: str
    compound: bool
    is_complex_lift: bool
    is_unilateral: bool
    description: Optional[str]
    coaching_cues: List[str]
    substitution_group: Optional[str]
    variation_on_names: List[str]
    source_category: Optional[str]
    source_primary_muscles_raw: List[str]
    source_secondary_muscles_raw: List[str]
    source_equipment_raw: List[str]
    source_id: Optional[str]
    license_author: Optional[str]
    license_meta: Optional[Dict[str, Any]]


def normalize_space(text: str) -> str:
    parts = text.split()
    return " ".join(p for p in parts if p)


def canonicalize_base_name(name: str) -> str:
    s = name.lower().replace("_", " ")
    s = re.sub(r"\([^)]*\)", " ", s)
    for term in EQUIPMENT_TERMS:
        s = s.replace(term, " ")
    for term in MODIFIER_TERMS:
        s = s.replace(term, " ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = normalize_space(s)
    if not s:
        return name.strip()
    words = [w.capitalize() for w in s.split()]
    return " ".join(words)


def canonical_key_from_base(name: str) -> str:
    return name.lower().replace(" ", "_")


def map_primary_muscle(name: str) -> str:
    key = name.lower().strip()
    mapping = {
        "quadriceps": PrimaryMuscle.QUADRICEPS.value,
        "quads": PrimaryMuscle.QUADRICEPS.value,
        "hamstrings": PrimaryMuscle.HAMSTRINGS.value,
        "glutes": PrimaryMuscle.GLUTES.value,
        "calves": PrimaryMuscle.CALVES.value,
        "chest": PrimaryMuscle.CHEST.value,
        "pectoralis major": PrimaryMuscle.CHEST.value,
        "lats": PrimaryMuscle.LATS.value,
        "latissimus dorsi": PrimaryMuscle.LATS.value,
        "upper back": PrimaryMuscle.UPPER_BACK.value,
        "traps": PrimaryMuscle.UPPER_BACK.value,
        "rear delts": PrimaryMuscle.REAR_DELTS.value,
        "rear deltoids": PrimaryMuscle.REAR_DELTS.value,
        "front delts": PrimaryMuscle.FRONT_DELTS.value,
        "anterior deltoids": PrimaryMuscle.FRONT_DELTS.value,
        "side delts": PrimaryMuscle.SIDE_DELTS.value,
        "lateral deltoids": PrimaryMuscle.SIDE_DELTS.value,
        "biceps": PrimaryMuscle.BICEPS.value,
        "triceps": PrimaryMuscle.TRICEPS.value,
        "forearms": PrimaryMuscle.FOREARMS.value,
        "abdominals": PrimaryMuscle.CORE.value,
        "abs": PrimaryMuscle.CORE.value,
        "core": PrimaryMuscle.CORE.value,
        "obliques": PrimaryMuscle.OBLIQUES.value,
        "lower back": PrimaryMuscle.LOWER_BACK.value,
        "hip flexors": PrimaryMuscle.HIP_FLEXORS.value,
    "adductors": PrimaryMuscle.ADDUCTORS.value,
    "abductors": PrimaryMuscle.ADDUCTORS.value,
        "full body": PrimaryMuscle.FULL_BODY.value,
    }
    return mapping.get(key, PrimaryMuscle.FULL_BODY.value)


def map_primary_region(primary_muscle: str) -> str:
    mapping = {
        PrimaryMuscle.QUADRICEPS.value: PrimaryRegion.ANTERIOR_LOWER.value,
        PrimaryMuscle.HAMSTRINGS.value: PrimaryRegion.POSTERIOR_LOWER.value,
        PrimaryMuscle.GLUTES.value: PrimaryRegion.POSTERIOR_LOWER.value,
        PrimaryMuscle.CALVES.value: PrimaryRegion.POSTERIOR_LOWER.value,
        PrimaryMuscle.CHEST.value: PrimaryRegion.ANTERIOR_UPPER.value,
        PrimaryMuscle.LATS.value: PrimaryRegion.POSTERIOR_UPPER.value,
        PrimaryMuscle.UPPER_BACK.value: PrimaryRegion.POSTERIOR_UPPER.value,
        PrimaryMuscle.REAR_DELTS.value: PrimaryRegion.POSTERIOR_UPPER.value,
        PrimaryMuscle.FRONT_DELTS.value: PrimaryRegion.ANTERIOR_UPPER.value,
        PrimaryMuscle.SIDE_DELTS.value: PrimaryRegion.SHOULDER.value,
        PrimaryMuscle.BICEPS.value: PrimaryRegion.ANTERIOR_UPPER.value,
        PrimaryMuscle.TRICEPS.value: PrimaryRegion.POSTERIOR_UPPER.value,
        PrimaryMuscle.FOREARMS.value: PrimaryRegion.ANTERIOR_UPPER.value,
        PrimaryMuscle.CORE.value: PrimaryRegion.FULL_BODY.value,
        PrimaryMuscle.OBLIQUES.value: PrimaryRegion.FULL_BODY.value,
        PrimaryMuscle.LOWER_BACK.value: PrimaryRegion.POSTERIOR_LOWER.value,
        PrimaryMuscle.HIP_FLEXORS.value: PrimaryRegion.ANTERIOR_LOWER.value,
        PrimaryMuscle.ADDUCTORS.value: PrimaryRegion.LOWER_BODY.value,
        PrimaryMuscle.FULL_BODY.value: PrimaryRegion.FULL_BODY.value,
    }
    return mapping.get(primary_muscle, PrimaryRegion.FULL_BODY.value)


def infer_pattern(name: str, category: Optional[str], primary_muscle: str) -> str:
    n = name.lower()
    c = category.lower() if category else ""
    if "squat" in n:
        return MovementPattern.SQUAT.value
    if "deadlift" in n or "romanian deadlift" in n or "rdl" in n:
        return MovementPattern.HINGE.value
    if "hip thrust" in n or "glute bridge" in n:
        return MovementPattern.HINGE.value
    if "bench" in n or ("press" in n and ("chest" in n or "bench" in n)):
        return MovementPattern.HORIZONTAL_PUSH.value
    if "overhead press" in n or "shoulder press" in n or "military press" in n:
        return MovementPattern.VERTICAL_PUSH.value
    if "row" in n and "upright" not in n:
        return MovementPattern.HORIZONTAL_PULL.value
    if "pulldown" in n or ("pull down" in n and "lat" in n):
        return MovementPattern.VERTICAL_PULL.value
    if "curl" in n or "extension" in n or "raise" in n or "fly" in n or "pullover" in n:
        return MovementPattern.ISOLATION.value
    if "lunge" in n or "split squat" in n or "step up" in n or "step-up" in n:
        return MovementPattern.LUNGE.value
    if "carry" in n or "farmer" in n:
        return MovementPattern.CARRY.value
    if "plank" in n or "crunch" in n or "sit up" in n or "sit-up" in n:
        return MovementPattern.CORE.value
    if "jump" in n or "plyo" in n or "box jump" in n:
        return MovementPattern.PLYOMETRIC.value
    if "snatch" in n or "clean" in n or "jerk" in n:
        return MovementPattern.OLYMPIC.value
    if c == "cardio":
        return MovementPattern.CARDIO.value
    if c in {"stretching", "mobility"}:
        return MovementPattern.MOBILITY.value
    if primary_muscle in {
        PrimaryMuscle.QUADRICEPS.value,
        PrimaryMuscle.HAMSTRINGS.value,
        PrimaryMuscle.GLUTES.value,
        PrimaryMuscle.CALVES.value,
    }:
        return MovementPattern.LUNGE.value
    return MovementPattern.ISOLATION.value


def infer_metric_type(category: Optional[str], name: str) -> str:
    c = category.lower() if category else ""
    n = name.lower()
    if c == "cardio":
        return MetricType.TIME.value
    if "run" in n or "jog" in n or "cycle" in n or "row" in n or "erg" in n:
        return MetricType.TIME.value
    return MetricType.REPS.value


def infer_skill_level(name: str) -> str:
    n = name.lower()
    if "pistol squat" in n or "muscle up" in n or "snatch" in n or "clean and jerk" in n:
        return SkillLevel.ADVANCED.value
    if "single leg" in n or "single-arm" in n or "single arm" in n or "one-arm" in n:
        return SkillLevel.INTERMEDIATE.value
    return SkillLevel.INTERMEDIATE.value


def infer_cns_load(name: str, category: Optional[str]) -> str:
    n = name.lower()
    c = category.lower() if category else ""
    if any(k in n for k in ["back squat", "front squat", "deadlift", "snatch", "clean and jerk"]):
        return CNSLoad.HIGH.value
    if c == "cardio":
        return CNSLoad.LOW.value
    return CNSLoad.MODERATE.value


def infer_compound_flags(name: str, primary_muscle: str) -> Tuple[bool, bool, bool]:
    n = name.lower()
    compound = any(k in n for k in ["squat", "deadlift", "press", "row", "lunge", "snatch", "clean", "jerk"])
    is_complex = any(k in n for k in ["snatch", "clean", "jerk"]) or "deadlift" in n or "back squat" in n
    unilateral = any(k in n for k in ["single leg", "single-leg", "single arm", "single-arm", "one leg", "one arm"])
    if primary_muscle in {
        PrimaryMuscle.QUADRICEPS.value,
        PrimaryMuscle.HAMSTRINGS.value,
        PrimaryMuscle.GLUTES.value,
    } and "machine" in n:
        compound = False
    return compound, is_complex, unilateral


def normalize_equipment(equipment: List[str]) -> List[str]:
    result: List[str] = []
    for item in equipment:
        key = item.lower().strip()
        if not key:
            continue
        if key in BODYWEIGHT_TERMS:
            if "bodyweight" not in result:
                result.append("bodyweight")
        else:
            if key not in result:
                result.append(key)
    return result


def infer_disciplines(category: Optional[str], equipment_tags: List[str]) -> List[str]:
    tags: List[str] = []
    c = category.lower() if category else ""
    if c:
        tags.append(c)
    if "bodyweight" in equipment_tags and "calisthenics" not in tags:
        tags.append("calisthenics")
    if "strongman" in tags and "powerlifting" not in tags:
        tags.append("powerlifting")
    return tags


def build_coaching_cues(instructions: List[str], tips: Optional[List[str]]) -> List[str]:
    cues: List[str] = []
    for item in instructions:
        text = item.strip()
        if text:
            cues.append(text)
    if tips:
        for item in tips:
            text = item.strip()
            if text and text not in cues:
                cues.append(text)
    return cues


def build_candidate(ex: Dict[str, Any], source_id: str) -> MovementCandidate:
    name = ex.get("name", "").strip()
    aliases = ex.get("aliases") or []
    category = ex.get("category")
    primary_raw = ex.get("primary_muscles") or []
    secondary_raw = ex.get("secondary_muscles") or []
    equipment_raw = ex.get("equipment") or []
    canonical_base = canonicalize_base_name(name)
    canonical_key = canonical_key_from_base(canonical_base)
    primary_muscle_value = map_primary_muscle(primary_raw[0]) if primary_raw else PrimaryMuscle.FULL_BODY.value
    secondary_muscles_values = [map_primary_muscle(m) for m in secondary_raw]
    primary_region_value = map_primary_region(primary_muscle_value)
    pattern_value = infer_pattern(canonical_base, category, primary_muscle_value)
    equipment_tags = normalize_equipment(equipment_raw)
    discipline_tags = infer_disciplines(category, equipment_tags)
    metric_type_value = infer_metric_type(category, name)
    skill_level_value = infer_skill_level(name)
    cns_load_value = infer_cns_load(name, category)
    compound, is_complex, unilateral = infer_compound_flags(name, primary_muscle_value)
    description = ex.get("description") or None
    instructions = ex.get("instructions") or []
    tips = ex.get("tips") or []
    coaching_cues = build_coaching_cues(instructions, tips)
    variation_on_names = ex.get("variation_on") or []
    substitution_group = canonical_key
    license_author = ex.get("license_author")
    license_meta = ex.get("license")
    return MovementCandidate(
        source_name=name,
        source_aliases=aliases,
        canonical_base_name=canonical_base,
        canonical_name_key=canonical_key,
        pattern=pattern_value,
        primary_muscle=primary_muscle_value,
        secondary_muscles=secondary_muscles_values,
        primary_region=primary_region_value,
        discipline_tags=discipline_tags,
        equipment_tags=equipment_tags,
        metric_type=metric_type_value,
        skill_level=skill_level_value,
        cns_load=cns_load_value,
        compound=compound,
        is_complex_lift=is_complex,
        is_unilateral=unilateral,
        description=description,
        coaching_cues=coaching_cues,
        substitution_group=substitution_group,
        variation_on_names=variation_on_names,
        source_category=category,
        source_primary_muscles_raw=primary_raw,
        source_secondary_muscles_raw=secondary_raw,
        source_equipment_raw=equipment_raw,
        source_id=source_id,
        license_author=license_author,
        license_meta=license_meta,
    )


def tokenize(text: str) -> List[str]:
    normalized = normalize_text_strict(text)
    tokens = [t for t in normalized.split() if t]
    return [NAME_TOKEN_SYNONYMS.get(t, t) for t in tokens]


def token_jaccard(a: str, b: str) -> float:
    ta = set(tokenize(a))
    tb = set(tokenize(b))
    if not ta or not tb:
        return 0.0
    inter = len(ta.intersection(tb))
    union = len(ta.union(tb))
    return inter / union if union else 0.0


def char_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def compute_similarity(candidate: MovementCandidate, existing: Dict[str, Any]) -> float:
    base = 0.0
    
    # 1. Exact canonical key match (Highest confidence)
    if candidate.canonical_name_key == existing["canonical_name_key"]:
        return 1.0

    # 2. Token Jaccard (Base score)
    base = token_jaccard(candidate.canonical_base_name, existing["canonical_base_name"])
    
    # 3. Char Similarity (Booster)
    base += char_similarity(candidate.canonical_base_name, existing["canonical_base_name"]) * 0.15

    # 4. Pattern Match (Context booster)
    if candidate.pattern == existing["pattern"]:
        base += 0.1

    # 5. Primary Muscle Match (Strong grouping signal)
    if candidate.primary_muscle == existing["primary_muscle"]:
        base += 0.15

    # 6. Equipment Match (Strong grouping signal)
    cand_eq = set(candidate.equipment_tags)
    exist_eq = set(existing.get("equipment_tags") or [])
    if cand_eq and exist_eq and cand_eq.intersection(exist_eq):
        base += 0.1
    elif not cand_eq and not exist_eq:
        # Both have no equipment (e.g. bodyweight implied) -> mild boost
        base += 0.05

    # 7. Substring Match (Grouping signal for variations)
    # Check if one normalized name is a substring of the other
    norm_cand = normalize_text_strict(candidate.canonical_base_name)
    norm_exist = normalize_text_strict(existing["canonical_base_name"])
    if norm_cand and norm_exist and (norm_cand in norm_exist or norm_exist in norm_cand):
        base += 0.1

    return min(base, 1.0)


async def fetch_exercises() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(EXERCISES_URL)
        response.raise_for_status()
        return response.json()


async def load_existing_movements(db: AsyncSession) -> List[Dict[str, Any]]:
    result = await db.execute(select(Movement))
    movements: List[Movement] = list(result.scalars().all())
    existing: List[Dict[str, Any]] = []
    for m in movements:
        base = canonicalize_base_name(m.name)
        key = canonical_key_from_base(base)
        existing.append(
            {
                "id": m.id,
                "name": m.name,
                "canonical_base_name": base,
                "canonical_name_key": key,
                "pattern": m.pattern,
                "primary_muscle": m.primary_muscle,
                "primary_region": m.primary_region,
                "equipment_tags": m.equipment_tags or [],
            }
        )
    return existing


def find_best_match(candidate: MovementCandidate, existing: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], float]:
    best = None
    best_score = 0.0
    for ex in existing:
        score = compute_similarity(candidate, ex)
        if score > best_score:
            best_score = score
            best = ex
    return best, best_score


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest exercemus exercises")
    parser.add_argument("--commit", action="store_true", help="Actually insert movements into database")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Fetching exercises...")
    data = await fetch_exercises()
    exercises = data.get("exercises") or []
    
    async with async_session_maker() as db:
        print("Loading existing movements...")
        existing = await load_existing_movements(db)
        
        candidates: List[MovementCandidate] = []
        invalid_candidates: List[Dict[str, Any]] = []
        
        print("Building candidates...")
        for idx, ex in enumerate(exercises):
            name = ex.get("name")
            if not name:
                invalid_candidates.append({"reason": "missing_name", "source": ex})
                continue
            try:
                candidate = build_candidate(ex, str(idx))
            except Exception as e:
                invalid_candidates.append({"reason": "build_error", "error": str(e), "source": ex})
                continue
            if not candidate.pattern or not candidate.primary_muscle or not candidate.primary_region or not candidate.metric_type:
                invalid_candidates.append({"reason": "missing_required_fields", "candidate": candidate.__dict__})
                continue
            candidates.append(candidate)
        
        threshold_hi = 0.55
        threshold_lo = 0.45
        
        ambiguous: List[Dict[str, Any]] = []
        low_score_samples: List[Dict[str, Any]] = []
        duplicates_count = 0
        likely_new_count = 0
        new_movements_to_insert: List[MovementCandidate] = []
        
        print("Matching candidates...")
        for i, candidate in enumerate(candidates):
            best, score = find_best_match(candidate, existing)
            
            is_new = False
            if best is None:
                is_new = True
                likely_new_count += 1
                if len(low_score_samples) < 100:
                    low_score_samples.append(
                        {
                            "candidate": candidate.__dict__,
                            "best_match": None,
                            "score": score,
                        }
                    )
            elif score >= threshold_hi:
                duplicates_count += 1
            elif score >= threshold_lo:
                ambiguous.append(
                    {
                        "candidate": candidate.__dict__,
                        "best_match": best,
                        "score": score,
                    }
                )
            else:
                is_new = True
                likely_new_count += 1
                if len(low_score_samples) < 100:
                    low_score_samples.append(
                        {
                            "candidate": candidate.__dict__,
                            "best_match": best,
                            "score": score,
                        }
                    )
            
            if is_new:
                new_movements_to_insert.append(candidate)

        summary = {
            "total_source_exercises": len(exercises),
            "valid_candidates": len(candidates),
            "invalid_candidates": len(invalid_candidates),
            "duplicate_candidates": duplicates_count,
            "ambiguous_candidates": len(ambiguous),
            "likely_new_candidates": likely_new_count,
            "threshold_hi": threshold_hi,
            "threshold_lo": threshold_lo,
        }
        
        print(json.dumps(summary, indent=2))
        
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2))
        AMBIGUOUS_PATH.write_text(json.dumps(ambiguous, indent=2))
        LOW_SCORE_PATH.write_text(json.dumps(low_score_samples, indent=2))
        INVALID_PATH.write_text(json.dumps(invalid_candidates, indent=2))
        
        if args.commit and new_movements_to_insert:
            print(f"Committing {len(new_movements_to_insert)} new movements to database...")
            for cand in new_movements_to_insert:
                movement = Movement(
                    name=cand.source_name,
                    pattern=cand.pattern,
                    primary_muscle=cand.primary_muscle,
                    primary_region=cand.primary_region,
                    secondary_muscles=cand.secondary_muscles,
                    cns_load=cand.cns_load,
                    skill_level=cand.skill_level,
                    compound=cand.compound,
                    is_complex_lift=cand.is_complex_lift,
                    is_unilateral=cand.is_unilateral,
                    metric_type=cand.metric_type,
                    discipline_tags=cand.discipline_tags,
                    equipment_tags=cand.equipment_tags,
                    description=cand.description,
                    coaching_cues=cand.coaching_cues,
                    substitution_group=cand.substitution_group,
                )
                db.add(movement)
            
            try:
                await db.commit()
                print("Successfully inserted new movements.")
            except Exception as e:
                await db.rollback()
                print(f"Error committing to database: {e}")
        elif args.commit:
            print("No new movements to insert.")
        else:
            print(f"Dry run complete. Use --commit to insert {len(new_movements_to_insert)} likely new movements.")


if __name__ == "__main__":
    asyncio.run(main())
