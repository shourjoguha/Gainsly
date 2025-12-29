# ShowMeGains Development Notes

## Architecture & Design Decisions

### 1. Heuristics Read-Only in MVP
**Decision**: Heuristic configs are read-only endpoints (`GET /settings/heuristics` only)

**Rationale**:
- Heuristics drive core algorithm logic (10 pre-seeded config sets)
- Used for goal-dose mapping, CNS thresholds, interference rules, deload triggers
- Write access would allow users to break system invariants
- Versioned model (`name`, `version`, `active`) supports future admin panel

**Future**: POST/PUT/DELETE endpoints after adding admin auth layer

---

### 2. Type Shadowing Pattern
**Problem**: Python reserved words conflict with schema field names (e.g., `date` type imported vs `date` field)

**Solution**: Field name aliases in schemas
- `date` → `log_date`, `plan_date`, `session_date`
- `date` → `session_date` in SessionResponse
- `date` → `micro_start_date` in MicrocycleResponse

**Pattern established**: When field name matches imported type, suffix with semantic context

---

### 3. SSE Streaming vs WebSocket
**Decision**: Use Server-Sent Events (SSE) instead of WebSocket for adaptation chat

**Rationale**:
- Simpler to implement with FastAPI
- No bidirectional complexity needed for chat flow
- REST + SSE cleaner than stateful WebSocket
- Stored conversation threads provide audit trail

**Endpoints**:
- `POST /days/{date}/adapt` - Non-streaming (full response)
- `POST /days/{date}/adapt/stream` - SSE streaming

---

### 4. User Authorization Pattern
**Current (MVP)**: Hardcoded `default_user_id = 1`

**Pattern**: Every endpoint validates with dependency injection:
```python
def get_current_user_id() -> int:
    return settings.default_user_id

# Then use: @router.post("...") async def endpoint(..., user_id: int = Depends(get_current_user_id))
```

**Future**: Replace with JWT token validation using same dependency

---

### 5. Database Session Management
**Pattern**: Async SQLAlchemy with aiosqlite (SQLite)

**Key decisions**:
- FastAPI `get_db` dependency injects per-request sessions
- `async with` not used; SQLAlchemy handles context
- No session pooling needed for MVP SQLite backend
- Greenlet dependency required for async sync ops

---

### 6. Movement Rules Flexibility
**Supported rule types**:
- `exclude` - Don't include this movement in programs
- `substitute` - Replace with this alternative movement
- `prefer` - Prioritize this movement (future)

**Pattern**: Rules include semantic context (reason field) for audit trail

---

## API Endpoint Pattern

All endpoints follow this structure:
```python
@router.post("/{resource_id}/action", response_model=ResponseSchema)
async def action(
    resource_id: int,
    request: RequestSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    # Verify resource ownership
    # Query related data
    # Business logic
    # Commit and return response
```

---

## LLM Integration

### Provider Interface
Located in `app/llm/base.py`:
- Abstract `LLMProvider` class
- `Message`, `LLMResponse`, `StreamChunk` data classes
- `PromptBuilder` for constructing system prompts

### Ollama Provider
Located in `app/llm/ollama_provider.py`:
- Implements `/api/chat` endpoint calls
- Enforces JSON schema on structured responses
- Supports streaming via `chat_stream()` generator
- Health check via `/api/tags`

### Schema Enforcement
Uses Ollama's `format.schema` parameter:
```python
{
    "type": "object",
    "properties": {
        "adapted_plan": {...},
        "reasoning": {"type": "string"},
        ...
    }
}
```

---

## e1RM Calculation
**Supported formulas** (configurable per user):
- `epley`: weight × (1 + reps/30)
- `brzycki`: weight × 36 / (37 - reps)
- `lombardi`: weight × reps^0.10
- `oconner`: weight × (1 + reps/40)

**Located in**: `app/services/metrics.py`

---

## Testing Strategy (TBD)

**Unit tests**:
- Metrics calculations (e1RM, PSI)
- Schema validation
- Enum mapping

**Integration tests**:
- Full endpoint flows with mock LLM
- Database session lifecycle
- Authorization checks

**Mock LLM provider**: Create for testing without Ollama

---

## Known Limitations

1. **No authentication** - MVP uses hardcoded user_id
2. **No update endpoints** - Movement rules/activities are create-only
3. **Single user** - No multi-tenant support
4. **SQLite backend** - No production scaling
5. **Heuristics immutable** - No user tuning
6. **No pagination defaults** - Clients must specify limits

---

## Common Patterns

### Error Handling
```python
if not resource or resource.user_id != user_id:
    raise HTTPException(status_code=404, detail="Not found")
```

### Enum Handling
```python
from app.models.enums import Goal
program.goal_1 = Goal.STRENGTH
# Value stored as string in DB, loaded as enum
```

### JSON Storage
```python
# Session sections stored as JSON
session.main_json = [{"movement": "squat", ...}]
```

---

## File Structure Reference

```
app/
├── api/routes/
│   ├── days.py          # Daily planning + adaptation
│   ├── logs.py          # Workout logging
│   ├── programs.py      # Program CRUD
│   └── settings.py      # User settings + config
├── config/
│   └── settings.py      # App configuration (Pydantic BaseSettings)
├── db/
│   ├── database.py      # SQLAlchemy setup
│   └── seed.py          # Database initialization
├── llm/
│   ├── base.py          # Provider interface
│   └── ollama_provider.py # Ollama implementation
├── models/
│   ├── enums.py         # All enum definitions
│   ├── movement.py      # Movement repository
│   ├── user.py          # User + settings models
│   ├── program.py       # Program + session models
│   ├── logging.py       # Workout log + recovery models
│   └── config.py        # Heuristics + conversation models
├── schemas/             # Pydantic request/response models
├── services/            # Business logic (metrics, time estimation)
└── main.py              # FastAPI app entry point
```

---

## Next Implementation Phase

1. **ProgramService** - Program generation logic
   - Distribute goals across microcycles
   - Generate session structures per split template
   - Apply progression style rules

2. **AdaptationService** - Session adaptation logic
   - Parse constraints
   - Apply interference rules
   - Generate alternative suggestions

3. **DeloadService** - Deload scheduling
   - Track microcycle history
   - Monitor PSI trends
   - Trigger time-based or performance-based deloads

4. **Testing** - Unit + integration test suite
   - Mock LLM provider
   - Database fixtures
   - End-to-end flows

---

## Environment Setup (Local Development)

```bash
# Create and activate venv
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Ollama (separate terminal)
ollama serve

# Run app
uvicorn app.main:app --reload

# Seed database (runs automatically on startup)
# Or manually: python -m app.db.seed
```

**Required Ollama model**:
```bash
ollama pull llama3.1:8b
```

---

## Session Tracking

See `SESSION_LOG.md` for detailed progress notes with timestamp headers for each development session (defined as ≤45 min interruption).
