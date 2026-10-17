# Emotional Mapping — AI-Powered Filmmaking & Audience Response Analysis

An AI-powered filmmaking decision-support application designed for directors, cinematographers, and producers.

The core research and artistic question addressed by the system is:
> *"Does camera perspective change viewers' empathy, perceived power, and blame toward characters experiencing the same event?"*

The application is structured into two major workflows:
1. **Shot Designer (Implemented in Backend Part 1):** Takes narrative scene parameters (description, target emotion, character focus, production budget) and generates 4–5 distinct, practical camera perspective options grounded in cinematographic theory.
2. **Audience Lens & Psychology Experiment (Future Phases):** Multimodal video analysis, simulated persona feedback, and empirical viewer response evaluation.

---

## Technology Stack

- **Backend Framework:** Python 3.10+ / FastAPI
- **Data Validation & Settings:** Pydantic v2 & `pydantic-settings`
- **Database ORM:** SQLAlchemy 2.0 (Async) + `asyncpg`
- **Database & Auth Platform:** Supabase (PostgreSQL with Transaction Pooler / pgBouncer)
- **Authentication:** Passwordless Supabase Email OTP (`auth.users` + Bearer JWT verification)
- **AI Engine:** Google Gemini API via official `google-genai` SDK (`gemini-2.0-flash`)
- **Testing:** `pytest` + `pytest-asyncio` (Fully isolated unit test suite using fakes/mocks)
- **Future Frontend:** React + Vite (JavaScript/JSX)

---

## Directory Structure

```
├── .env.example              # Example environment configuration template
├── backend/
│   ├── auth/                 # Pluggable authentication provider & dependencies
│   │   ├── base.py           # Abstract AuthProvider interface
│   │   ├── dependencies.py   # FastAPI get_current_user dependency
│   │   └── supabase_auth.py  # Supabase REST token verification with 60s cache
│   ├── config.py             # Validated application settings (Pydantic Settings)
│   ├── constants.py          # Single source of truth for controlled vocabularies
│   ├── db.py                 # Async SQLAlchemy engine (pgBouncer transaction pooler)
│   ├── llm/                  # Pluggable LLM provider abstraction
│   │   ├── base.py           # Abstract LLMProvider interface & usage dataclasses
│   │   └── gemini_provider.py# Google Gemini SDK implementation with auto-retries
│   ├── main.py               # FastAPI entry point, CORS, and uniform error handlers
│   ├── models.py             # SQLAlchemy 2.0 ORM models
│   ├── prompts/              # System prompt templates for Shot Designer
│   │   └── shot_designer.py  # Safety-guarded prompt for perspective recommendations
│   ├── requirements.txt      # Python dependencies
│   ├── routers/              # API endpoints mounted under /api/v1
│   │   ├── auth.py           # /api/v1/auth/me
│   │   ├── knowledge_base.py # /api/v1/knowledge-base (listing & filtering)
│   │   ├── meta.py           # /api/v1/meta/options (controlled vocabularies)
│   │   ├── projects.py       # /api/v1/projects (CRUD & user isolation)
│   │   └── scenes.py         # /api/v1/scenes & /api/v1/scenes/design-shots
│   ├── schemas.py            # Pydantic v2 request/response contracts
│   ├── services/             # Business logic layer
│   │   ├── knowledge_base.py # Technique filtering and retrieval
│   │   ├── projects.py       # Project management
│   │   ├── scenes.py         # Scene management with ownership validation
│   │   └── shot_designer.py  # AI generation, rate limiting, and persistence
│   ├── sql/                  # Supabase PostgreSQL migrations
│   │   ├── 001_foundation.sql
│   │   ├── 002_later_modules.sql
│   │   ├── 003_seed_knowledge_base.sql
│   │   └── 004_schema_reconciliation.sql (Performance indexes & triggers)
│   ├── storage/              # Object storage provider abstraction
│   │   ├── base.py
│   │   └── supabase_storage.py
│   └── tests/                # Automated unit test suite (no live keys needed)
│       ├── conftest.py       # Fixtures & FakeLLMProvider
│       ├── test_api_behavior.py
│       ├── test_auth.py
│       ├── test_knowledge_base.py
│       ├── test_projects_scenes.py
│       └── test_shot_designer.py
└── docs/                     # Project Documentation
    ├── api_contract.md               # Frontend API specification & error formats
    ├── architecture_overview.md      # System architecture & design decisions
    ├── authentication_flow.md        # Supabase Email OTP architecture
    ├── database_schema_report.md     # Schema mapping, RLS, and migration audit
    ├── gemini_integration.md         # Gemini SDK, anti-hallucination, rate limits
    ├── limitations_and_next_steps.md # Scope boundaries and frontend preparation
    └── manual_testing_guide.md       # Step-by-step beginner testing guide
```

---

## Quickstart & Verification

Please refer to the comprehensive [docs/manual_testing_guide.md](docs/manual_testing_guide.md) for full instructions.

### 1. Configure Environment
```powershell
Copy-Item .env.example .env
# Fill in your DATABASE_URL (port 6543 pooler), SUPABASE keys, and GEMINI_API_KEY
```

### 2. Run Database Migrations (Supabase Dashboard)
Execute the files in `backend/sql/` sequentially in your Supabase SQL Editor:
1. `001_foundation.sql`
2. `002_later_modules.sql`
3. `003_seed_knowledge_base.sql`
4. `004_schema_reconciliation.sql`

### 3. Run Unit Tests (Mocked)
```powershell
cd backend
pytest -v
```

### 4. Start Development Server
```powershell
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Interactive Swagger docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
