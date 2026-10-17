# Architecture Overview — Emotional Mapping Backend

## 1. System Context & Layered Design

The backend is built as a modular, stateless, async Python FastAPI application designed for high security, strict user isolation, and swappable provider abstractions.

```
┌─────────────────────────────────────────────────────────────┐
│                       Clients                               │
│       React + Vite Frontend (or Swagger UI / Postman)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Application (main.py)               │
│  - CORS Middleware (strict origin control)                  │
│  - Global Exception Handlers (uniform JSON error envelope)  │
│  - Router mounts under /api/v1 prefix                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
       ┌───────────────────────┼────────────────────────┐
       ▼                       ▼                        ▼
┌──────────────┐       ┌──────────────┐         ┌──────────────┐
│ Auth Router  │       │ Projects /   │         │ Knowledge    │
│  & Meta      │       │ Scenes Router│         │ Base Router  │
└──────┬───────┘       └──────┬───────┘         └──────┬───────┘
       │                      │                        │
       ▼                      ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│                       Service Layer                         │
│  - services/projects.py (User-scoped project lifecycle)     │
│  - services/scenes.py   (Project-verified scene CRUD)       │
│  - services/knowledge_base.py (Filtered technique retrieval)│
│  - services/shot_designer.py  (AI generation orchestration, │
│    anti-hallucination sanitization, atomic persistence)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
       ┌───────────────────────┼────────────────────────┐
       ▼                       ▼                        ▼
┌──────────────┐       ┌──────────────┐         ┌──────────────┐
│ Auth Provider│       │ LLM Provider │         │ Storage      │
│  Interface   │       │  Interface   │         │ Provider     │
│(SupabaseAuth)│       │ (Gemini 2.0) │         │ (Supabase)   │
└──────────────┘       └──────────────┘         └──────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Database & External Cloud                   │
│  - Supabase Auth REST (Bearer token verification)           │
│  - Supabase PostgreSQL (SQLAlchemy 2.0 Async + pgBouncer)   │
│  - Google AI Studio (Gemini 2.0 Flash structured outputs)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Key Architectural Decisions

### 1. Swappable Provider Abstractions
- **Auth Provider (`backend/auth/base.py`):** Defines abstract `verify_token(token: str) -> AuthUser`. The app uses `SupabaseAuthProvider`, which calls the Supabase Auth REST API with in-memory 60s SHA-256 token caching. To change auth providers (e.g. Firebase, Auth0), implement a new class and update one line in `auth/dependencies.py`.
- **LLM Provider (`backend/llm/base.py`):** Defines abstract `generate_structured(system_prompt, user_prompt, response_model)`. The app uses `GeminiProvider` (`backend/llm/gemini_provider.py`) leveraging the official `google-genai` SDK with built-in schema validation, 1 auto-retry, and timeout management.
- **Storage Provider (`backend/storage/base.py`):** Defines abstract file upload/delete operations implemented by `SupabaseStorageProvider`.

### 2. Transaction Pooler Compatibility
Direct PostgreSQL connections (port `5432`) frequently fail on modern cloud platforms due to IPv6 routing differences. The backend uses the **Supabase Transaction Pooler (port `6543`, pgBouncer)** with:
```python
connect_args={"prepared_statement_cache_size": 0}
```
This avoids `prepared statement already exists` or unsupported pgBouncer errors while maintaining optimal connection pooling.

### 3. Defence-in-Depth Security
1. **Row Level Security (RLS):** Enabled on all tables with no anon policies. Direct requests to Supabase from the browser using the public anon key are blocked.
2. **Backend Authentication:** Every protected endpoint requires a verified Supabase JWT Bearer token via `Depends(get_current_user)`.
3. **Application-Level Tenant Isolation:** The backend explicitly scopes all operations to `Project.user_id == user.id`. Foreign key traversal verifies that scenes belong to the user's project before reading, updating, or deleting.
4. **Anti-Enumeration 404 Responses:** When an unauthorized user requests another user's project or scene, the API returns HTTP 404 rather than 403, preventing attackers from discovering existing UUIDs.
