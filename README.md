# ShowMeGains - AI Workout Coach

An AI-enabled workout coach that creates adaptive 8-12 week strength/fitness programs and adapts daily sessions based on your preferences, constraints, and recovery signals.

## Features

- **Program Generation**: Create personalized 8-12 week programs based on 3 weighted goals
- **Multiple Split Templates**: Upper/Lower, PPL, Full Body, or custom Hybrid splits
- **Daily Adaptation**: Real-time session adjustments based on constraints and recovery
- **Progress Tracking**: e1RM calculation with multiple formulas (Epley, Brzycki, Lombardi, O'Conner)
- **Pattern Strength Index (PSI)**: Track strength across movement patterns
- **Intelligent Deloading**: Time-based and performance-triggered deload scheduling
- **Interference Management**: Account for recreational activities affecting training
- **Coach Personas**: Customizable tone and programming aggressiveness

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite (designed for Postgres migration)
- **LLM**: Ollama (local) with provider-agnostic interface
- **HTTP Client**: httpx (async)

## Quick Start

### Prerequisites

1. Python 3.11+
2. Ollama installed and running (`ollama serve`)
3. llama3.1:8b model pulled (`ollama pull llama3.1:8b`)

### Installation

```bash
# Navigate to project directory
cd ShowMeGainsZues_1225

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

### Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Check LLM connection
curl http://localhost:8000/health/llm
```

## Project Structure

```
ShowMeGainsZues_1225/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoint routers
│   ├── config/
│   │   └── settings.py      # Application configuration
│   ├── db/
│   │   └── database.py      # Database connection
│   ├── llm/
│   │   ├── base.py          # LLM provider interface
│   │   └── ollama_provider.py  # Ollama implementation
│   ├── models/
│   │   ├── enums.py         # Enum definitions
│   │   ├── movement.py      # Movement repository
│   │   ├── user.py          # User configuration
│   │   ├── program.py       # Program/session planning
│   │   ├── logging.py       # Workout logging
│   │   └── config.py        # Heuristic configs
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/
│   │   ├── metrics.py       # e1RM and PSI calculations
│   │   └── time_estimation.py  # Session duration estimation
│   └── main.py              # FastAPI app entry point
├── seed_data/
│   ├── movements.json       # Pre-populated movement library
│   └── heuristic_configs.json  # Default configurations
├── tests/
├── requirements.txt
└── README.md
```

## API Endpoints (Planned)

### Program Lifecycle
- `POST /programs` - Create new program
- `GET /programs/{id}` - Get program details
- `POST /programs/{id}/microcycles/generate-next` - Generate next microcycle

### Daily Planning
- `GET /days/{date}/plan` - Get daily session plan
- `POST /days/{date}/adapt` - Adapt session with constraints (supports SSE streaming)

### Logging
- `POST /logs/workouts` - Log workout completion
- `POST /logs/soreness` - Log muscle soreness
- `POST /logs/recovery` - Log recovery signals

### Settings & Configuration
- `GET /settings` - Get user settings
- `PUT /settings` - Update settings
- `GET /configs` - List heuristic configurations
- `PUT /configs/{name}/active` - Activate config version

## Configuration

Environment variables (or `.env` file):

```env
# LLM Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT=120.0

# Database
DATABASE_URL=sqlite+aiosqlite:///./workout_coach.db

# App
DEBUG=true
```

## Goals (Ten-Dollar Method)

Select 3 goals and assign weights that sum to 10:
- `strength` - Max force production
- `hypertrophy` - Muscle growth
- `endurance` - Work capacity
- `fat_loss` - Body composition
- `mobility` - Range of motion
- `explosiveness` - Power output
- `speed` - Movement velocity

## Split Templates

- **Upper/Lower**: 4 days/week, alternating upper and lower body
- **PPL**: 6 days/week, Push/Pull/Legs rotation
- **Full Body**: 3 days/week, whole body each session
- **Hybrid**: Custom day-by-day or block composition

## Progression Styles

1. **Single Progression**: Increase weight when hitting rep target
2. **Double Progression**: Increase reps, then weight
3. **Paused Variations**: Add pauses for difficulty
4. **Build to Drop**: Build reps, drop and add weight

## Future Enhancements

- [ ] Garmin integration (OAuth2 PKCE) for recovery signals
- [ ] JWT authentication
- [ ] Cloud LLM providers (OpenAI, Anthropic)
- [ ] Postgres migration
- [ ] Frontend UI

## License

MIT
