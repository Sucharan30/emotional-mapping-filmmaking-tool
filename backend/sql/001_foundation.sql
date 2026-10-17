-- =============================================================
-- 001_foundation.sql
-- Foundation tables: projects, knowledge_base, scenes,
-- shot_recommendations, ai_usage.
--
-- Rules:
--   * Every statement is idempotent (CREATE ... IF NOT EXISTS,
--     ADD COLUMN ... IF NOT EXISTS).
--   * Never DROP or TRUNCATE anything that already exists.
--   * UUID primary keys everywhere.
--   * Every FK to projects.id uses UUID.
--   * RLS enabled on every table, no policies (backend uses
--     DATABASE_URL which bypasses RLS; the anon key cannot
--     read any row directly).
--
-- Run in: Supabase Dashboard -> SQL Editor -> New query
-- =============================================================

-- Extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── PROJECTS ─────────────────────────────────────────────────
-- The existing table may already have: id (uuid), name,
-- description, created_at.
-- We reconcile by adding the missing columns safely.
CREATE TABLE IF NOT EXISTS projects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Add each missing column idempotently.
-- user_id is added NULLABLE first because existing rows have no owner.
-- See MANUAL STEP in the backend README.
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS type        TEXT CHECK (type IN ('shot_design','audience_test')),
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS updated_at  TIMESTAMPTZ DEFAULT NOW();

-- ── KNOWLEDGE BASE ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_base (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technique_name        TEXT NOT NULL UNIQUE,
    category              TEXT NOT NULL CHECK (category IN ('angle','shot_type','framing','movement','distance')),
    visual_characteristic TEXT NOT NULL,
    potential_emotions    TEXT[] NOT NULL DEFAULT '{}',
    context_note          TEXT NOT NULL,
    example_scene         TEXT,
    equipment_needs       TEXT,
    typical_complexity    TEXT NOT NULL CHECK (typical_complexity IN ('Low','Medium','High')),
    review_status         TEXT NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft','reviewed')),
    source_note           TEXT,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);

-- ── SCENES ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scenes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    description         TEXT NOT NULL,
    target_emotion      TEXT,
    character_focus     TEXT CHECK (character_focus IN ('character_a','character_b','neutral_observer')),
    production_budget   TEXT NOT NULL DEFAULT 'medium' CHECK (production_budget IN ('low','medium','high')),
    budget_notes        TEXT,
    video_url           TEXT,
    video_analysis      JSONB,
    experiment_group_id UUID,
    variant_label       TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── SHOT RECOMMENDATIONS ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS shot_recommendations (
    id                            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id                      UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    rank                          INT NOT NULL,
    perspective_name              TEXT NOT NULL,
    reasoning                     TEXT NOT NULL,
    visual_checklist              JSONB NOT NULL DEFAULT '[]',
    context_caveat                TEXT NOT NULL,
    production_complexity_level   TEXT NOT NULL CHECK (production_complexity_level IN ('Low','Medium','High')),
    production_complexity_reason  TEXT NOT NULL,
    budget_fit                    TEXT NOT NULL CHECK (budget_fit IN ('good_fit','stretch','beyond_budget')),
    budget_fit_reason             TEXT NOT NULL,
    knowledge_base_ids            JSONB NOT NULL DEFAULT '[]',
    model_name                    TEXT,
    created_at                    TIMESTAMPTZ DEFAULT NOW()
);

-- ── AI USAGE ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_usage (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL,
    feature       TEXT NOT NULL,
    model_name    TEXT,
    input_tokens  INT,
    output_tokens INT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_usage_user_created
    ON ai_usage (user_id, created_at);

-- ── ROW LEVEL SECURITY ───────────────────────────────────────
-- Enable RLS with NO policies. The anon key cannot read any
-- row directly. The backend's DATABASE_URL bypasses RLS.
ALTER TABLE projects             ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base       ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenes               ENABLE ROW LEVEL SECURITY;
ALTER TABLE shot_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_usage             ENABLE ROW LEVEL SECURITY;
