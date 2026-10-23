# Database & Schema Compatibility Report (Reconciled)

This document reports the reconciled database schema, field-by-field ORM mapping, migration history, and RLS enforcement for the Emotional Mapping backend.

---

## 1. Migration History

| Migration Script | Type | Purpose | Safety |
|---|---|---|---|
| `backend/sql/001_foundation.sql` | Historical | Initial proposed foundation schema. | Do not rerun. |
| `backend/sql/002_later_modules.sql` | Historical | Schema for future modules. | Do not rerun. |
| `backend/sql/003_seed_knowledge_base.sql` | Active Seed | Seeds 20 cinematography techniques with `review_status = 'draft'`. | Safe to run / rerun (`ON CONFLICT (technique_name) DO NOTHING`). |
| `backend/sql/004_schema_reconciliation.sql` | Historical | Previous index addition. | Safe. |
| `backend/sql/005_schema_reconciliation.sql` | **Active Reconciliation** | Reconciles live Supabase database with Shot Designer features while preserving integer primary keys and existing data. | Safe, non-destructive, idempotent. |

---

## 2. Table-by-Table Field Mapping Audit

### Table: `projects`
- **Primary Key:** `id` (`uuid`, `DEFAULT gen_random_uuid()`)
- **Foreign Keys:** `user_id` (`uuid`, references `auth.users(id) ON DELETE CASCADE`, nullable for existing test records)
- **Columns:**
  - `name` (`text`, `NOT NULL`)
  - `type` (`text`, `NOT NULL`, e.g. `'shot_design'`, `'audience_test'`)
  - `description` (`text`, optional narrative notes)
  - `created_at` (`timestamptz`, `DEFAULT NOW()`)
  - `updated_at` (`timestamptz`, `DEFAULT NOW()`, auto-updated via trigger)
- **ORM Model:** `models.Project` matches exactly.
- **Index:** `idx_projects_user_id` on `projects(user_id)`.

### Table: `scenes`
- **Primary Key:** `id` (`int4` / `integer`, serial/identity)
- **Foreign Key:** `project_id` (`uuid`, references `projects.id ON DELETE CASCADE`, `NOT NULL`)
- **Columns:**
  - `description` (`text`, `NOT NULL`)
  - `target_emotion` (`text`, validated against controlled vocabulary in API)
  - `character_focus` (`text`, check constraint: `'character_a'`, `'character_b'`, `'neutral_observer'`)
  - `production_budget` (`text`, check constraint: `'low'`, `'medium'`, `'high'`, default `'medium'`)
  - `budget_notes` (`text`, optional)
  - `video_url` (`text`, optional)
  - `video_analysis` (`jsonb`, optional)
  - `experiment_group_id` (`int4`, optional)
  - `variant_label` (`text`, optional)
  - `created_at` (`timestamptz`, `DEFAULT NOW()`)
- **ORM Model:** `models.Scene` matches exactly.
- **Index:** `idx_scenes_project_id` on `scenes(project_id)`.

### Table: `shot_recommendations`
- **Primary Key:** `id` (`int4` / `integer`, serial/identity)
- **Foreign Key:** `scene_id` (`int4`, references `scenes.id ON DELETE CASCADE`, `NOT NULL`)
- **Columns:**
  - `rank` (`int`, `NOT NULL`)
  - `perspective_name` (`text`, `NOT NULL`)
  - `reasoning` (`text`, `NOT NULL`)
  - `visual_checklist` (`jsonb`, `NOT NULL`, list of actionable technical instructions)
  - `context_caveat` (`text`, `NOT NULL`, potential failure modes)
  - `production_complexity_level` (`text`, check constraint: `'Low'`, `'Medium'`, `'High'`)
  - `production_complexity_reason` (`text`, `NOT NULL`)
  - `budget_fit` (`text`, check constraint: `'good_fit'`, `'stretch'`, `'beyond_budget'`)
  - `budget_fit_reason` (`text`, `NOT NULL`)
  - `knowledge_base_ids` (`jsonb`, `NOT NULL`, array of referenced KB IDs)
  - `model_name` (`text`, e.g. `'gemini-2.0-flash'`)
  - `created_at` (`timestamptz`, `DEFAULT NOW()`)
- **ORM Model:** `models.ShotRecommendation` matches exactly.
- **Index:** `idx_shot_recommendations_scene_id` on `shot_recommendations(scene_id)`.

### Table: `knowledge_base`
- **Primary Key:** `id` (`int4` / `integer`, serial/identity)
- **Columns:**
  - `technique_name` (`text`, `NOT NULL`, `UNIQUE`)
  - `category` (`text`, `NOT NULL`, check constraint: `'angle'`, `'shot_type'`, `'framing'`, `'movement'`, `'distance'`)
  - `visual_characteristic` (`text`, `NOT NULL`)
  - `potential_emotions` (`text[]`, `NOT NULL`, default `'{}'`)
  - `context_note` (`text`, `NOT NULL`)
  - `example_scene` (`text`, optional)
  - `equipment_needs` (`text`, optional)
  - `typical_complexity` (`text`, check constraint: `'Low'`, `'Medium'`, `'High'`, default `'Low'`)
  - `review_status` (`text`, check constraint: `'draft'`, `'reviewed'`, default `'draft'`)
  - `source_note` (`text`, optional reference citation)
  - `created_at` (`timestamptz`, `DEFAULT NOW()`)
- **ORM Model:** `models.KnowledgeBase` matches exactly.
- **Indexes:** `idx_knowledge_base_category`, `idx_knowledge_base_review_status`, and GIN index `idx_knowledge_base_potential_emotions`.

### Table: `ai_usage`
- **Primary Key:** `id` (`uuid`, `DEFAULT gen_random_uuid()`)
- **Columns:**
  - `user_id` (`uuid`, `NOT NULL`)
  - `feature` (`text`, `NOT NULL`, e.g. `'shot_designer'`)
  - `model_name` (`text`, optional)
  - `input_tokens` (`int`, optional)
  - `output_tokens` (`int`, optional)
  - `created_at` (`timestamptz`, `DEFAULT NOW()`)
- **ORM Model:** `models.AiUsage` matches exactly.
- **Index:** `idx_ai_usage_user_created` on `(user_id, created_at)`.

### Tables for Future Modules: `personas`, `audience_feedback`, `experiment_responses`
- All use `int4` primary keys matching the live Supabase database.
- `audience_feedback.scene_id` and `experiment_responses.scene_id` reference `scenes(id)` using `int4`.
- Column names in `experiment_responses` aligned with live database: `empathy_rating`, `perceived_power_rating`, `blame_rating`, `emotional_intensity_rating`, and `submitted_at`.

---

## 3. Row Level Security & Access Control

1. **Client / Browser Requests:**
   - Use public anon key (`SUPABASE_ANON_KEY`).
   - RLS is enabled on all tables with NO public policies.
   - Result: Direct access from client browsers directly to tables is blocked by PostgreSQL.
2. **Backend Connection:**
   - Connects via `DATABASE_URL` (Supabase transaction pooler, port 6543) using the `postgres` role.
   - Intentionally bypasses RLS in PostgreSQL. Multi-tenant security is enforced at the application layer by checking `Project.user_id == user.id`.
