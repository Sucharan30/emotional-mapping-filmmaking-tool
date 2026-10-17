# Database & Schema Compatibility Report

This document reports the audited schema, field-by-field ORM mapping, migration history, and RLS enforcement for the Emotional Mapping backend.

---

## 1. Migration History

| Migration Script | Status | Purpose | Safety |
|---|---|---|---|
| `backend/sql/001_foundation.sql` | Executed | Creates `projects`, `knowledge_base`, `scenes`, `shot_recommendations`, `ai_usage`. | Idempotent (`IF NOT EXISTS`). Safe. |
| `backend/sql/002_later_modules.sql` | Executed | Schema for future modules: `personas`, `audience_feedback`, `experiment_responses`. | Idempotent. Future tables only. |
| `backend/sql/003_seed_knowledge_base.sql` | Executed | Inserts 20 cinematographic techniques with draft review status. | `ON CONFLICT DO NOTHING`. Safe to rerun. |
| `backend/sql/004_schema_reconciliation.sql` | **New** | Adds performance indexes on foreign keys and `updated_at` trigger. | Non-destructive. No table/data changes. |

---

## 2. Table-by-Table Field Mapping Audit

### Table: `projects`
- Primary Key: `id UUID DEFAULT gen_random_uuid()`
- Columns:
  - `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  - `name TEXT NOT NULL`
  - `type TEXT CHECK (type IN ('shot_design', 'audience_test'))`
  - `description TEXT`
  - `created_at TIMESTAMPTZ DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ DEFAULT NOW()`
- **ORM Model:** `models.Project` matches exactly.
- **Index:** `idx_projects_user_id` added in migration `004`.

### Table: `scenes`
- Primary Key: `id UUID DEFAULT gen_random_uuid()`
- Foreign Key: `project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE`
- Columns:
  - `description TEXT NOT NULL`
  - `target_emotion TEXT` (validated against controlled vocabulary in API)
  - `character_focus TEXT CHECK (character_focus IN ('character_a', 'character_b', 'neutral_observer'))`
  - `production_budget TEXT NOT NULL DEFAULT 'medium' CHECK (production_budget IN ('low', 'medium', 'high'))`
  - `budget_notes TEXT`
  - `video_url TEXT`, `video_analysis JSONB`, `experiment_group_id UUID`, `variant_label TEXT`
  - `created_at TIMESTAMPTZ DEFAULT NOW()`
- **ORM Model:** `models.Scene` matches exactly.
- **Index:** `idx_scenes_project_id` added in migration `004`.

### Table: `shot_recommendations`
- Primary Key: `id UUID DEFAULT gen_random_uuid()`
- Foreign Key: `scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE`
- Columns:
  - `rank INT NOT NULL`
  - `perspective_name TEXT NOT NULL`
  - `reasoning TEXT NOT NULL`
  - `visual_checklist JSONB NOT NULL DEFAULT '[]'`
  - `context_caveat TEXT NOT NULL`
  - `production_complexity_level TEXT CHECK (production_complexity_level IN ('Low', 'Medium', 'High'))`
  - `production_complexity_reason TEXT NOT NULL`
  - `budget_fit TEXT CHECK (budget_fit IN ('good_fit', 'stretch', 'beyond_budget'))`
  - `budget_fit_reason TEXT NOT NULL`
  - `knowledge_base_ids JSONB NOT NULL DEFAULT '[]'`
  - `model_name TEXT`
  - `created_at TIMESTAMPTZ DEFAULT NOW()`
- **ORM Model:** `models.ShotRecommendation` matches exactly.
- **Index:** `idx_shot_recommendations_scene_id` added in migration `004`.

### Table: `knowledge_base`
- Primary Key: `id UUID DEFAULT gen_random_uuid()`
- Columns:
  - `technique_name TEXT NOT NULL UNIQUE`
  - `category TEXT CHECK (category IN ('angle', 'shot_type', 'framing', 'movement', 'distance'))`
  - `visual_characteristic TEXT NOT NULL`
  - `potential_emotions TEXT[] NOT NULL DEFAULT '{}'`
  - `context_note TEXT NOT NULL`
  - `example_scene TEXT`, `equipment_needs TEXT`
  - `typical_complexity TEXT CHECK (typical_complexity IN ('Low', 'Medium', 'High'))`
  - `review_status TEXT NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft', 'reviewed'))`
  - `source_note TEXT`
  - `created_at TIMESTAMPTZ DEFAULT NOW()`
- **ORM Model:** `models.KnowledgeBase` matches exactly.
- **Indexes:** `idx_knowledge_base_category`, `idx_knowledge_base_review_status`, and GIN index `idx_knowledge_base_potential_emotions` added in migration `004`.

### Table: `ai_usage`
- Primary Key: `id UUID DEFAULT gen_random_uuid()`
- Columns:
  - `user_id UUID NOT NULL`
  - `feature TEXT NOT NULL`
  - `model_name TEXT`
  - `input_tokens INT`
  - `output_tokens INT`
  - `created_at TIMESTAMPTZ DEFAULT NOW()`
- **ORM Model:** `models.AiUsage` matches exactly.
- **Index:** `idx_ai_usage_user_created` created in `001_foundation.sql`.

---

## 3. Row Level Security & Connection Privilege Audit

1. **Client / Browser Requests:**
   - Use the Supabase public anon key (`SUPABASE_ANON_KEY`).
   - All public tables have `ENABLE ROW LEVEL SECURITY` with NO policies.
   - Result: Any direct SQL or PostgREST call from the browser to read or write rows directly in tables is rejected by PostgreSQL.
2. **Backend Requests:**
   - Connect via `DATABASE_URL` using the Supabase transaction pooler.
   - Connects as the privileged database owner role (`postgres`), which intentionally bypasses RLS in PostgreSQL so the backend has full access to execute queries.
   - Multi-tenant data isolation is enforced at the application layer (`services/projects.py` and `services/scenes.py`) by explicitly filtering every query by `user_id = user.id`.
3. **No Credential Exposure:**
   - The database connection string and service role keys remain exclusively on the backend server and are never sent to the browser.
