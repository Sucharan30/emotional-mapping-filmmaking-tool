-- ==============================================================================
-- 005_schema_reconciliation.sql
-- RECONCILIATION MIGRATION FOR EMOTIONAL MAPPING SUPABASE DATABASE
--
-- PURPOSE:
-- Brings the existing live Supabase database into full harmony with the
-- backend API and Shot Designer feature requirements.
--
-- GUARANTEES:
-- 1. Non-destructive: Never drops tables, columns, or deletes existing data.
-- 2. Respects live primary-key types: Preserves projects.id as UUID and
--    scenes.id, shot_recommendations.id, knowledge_base.id as integer (int4).
-- 3. Idempotent: Safe to execute multiple times.
-- 4. Safe constraints: Checks existing rows before adding constraints.
--
-- EXECUTION:
-- Run in: Supabase Dashboard -> SQL Editor -> New query
-- ==============================================================================

-- ── 1. Extension ──────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ── 2. Table: PROJECTS ────────────────────────────────────────────────────────
-- projects.id is UUID.
-- Add missing columns safely and idempotently.
-- NOTE: user_id is added NULLABLE so existing test records are NOT deleted or broken.
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS updated_at  TIMESTAMPTZ DEFAULT NOW();

-- Ensure timestamp defaults exist even if columns were previously created without them
ALTER TABLE projects
    ALTER COLUMN updated_at SET DEFAULT NOW();

-- Create index on user_id for fast user project lookups
CREATE INDEX IF NOT EXISTS idx_projects_user_id
    ON projects (user_id);


-- ── 3. Table: SCENES ──────────────────────────────────────────────────────────
-- scenes.id is int4 (integer).
-- scenes.project_id is UUID referencing projects.id.
-- Add Shot Designer budget columns if missing.
ALTER TABLE scenes
    ADD COLUMN IF NOT EXISTS production_budget TEXT NOT NULL DEFAULT 'medium',
    ADD COLUMN IF NOT EXISTS budget_notes     TEXT;

-- Safely add budget check constraint if it does not already exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_scenes_production_budget'
    ) THEN
        ALTER TABLE scenes
            ADD CONSTRAINT chk_scenes_production_budget
            CHECK (production_budget IN ('low', 'medium', 'high'));
    END IF;
END $$;

-- Safely add character_focus check constraint if it does not already exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_scenes_character_focus'
    ) THEN
        ALTER TABLE scenes
            ADD CONSTRAINT chk_scenes_character_focus
            CHECK (character_focus IS NULL OR character_focus IN ('character_a', 'character_b', 'neutral_observer'));
    END IF;
END $$;

-- Create index on project_id for fast joins and cascade deletes
CREATE INDEX IF NOT EXISTS idx_scenes_project_id
    ON scenes (project_id);


-- ── 4. Table: SHOT_RECOMMENDATIONS ────────────────────────────────────────────
-- shot_recommendations.id is int4.
-- shot_recommendations.scene_id is int4 referencing scenes.id.
-- Add Shot Designer recommendation columns if missing.
ALTER TABLE shot_recommendations
    ADD COLUMN IF NOT EXISTS rank                         INT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS context_caveat               TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS budget_fit                   TEXT NOT NULL DEFAULT 'good_fit',
    ADD COLUMN IF NOT EXISTS budget_fit_reason            TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS knowledge_base_ids           JSONB NOT NULL DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS model_name                   TEXT;

-- Safely add budget_fit check constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_shot_recs_budget_fit'
    ) THEN
        ALTER TABLE shot_recommendations
            ADD CONSTRAINT chk_shot_recs_budget_fit
            CHECK (budget_fit IN ('good_fit', 'stretch', 'beyond_budget'));
    END IF;
END $$;

-- Safely add complexity check constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_shot_recs_complexity'
    ) THEN
        ALTER TABLE shot_recommendations
            ADD CONSTRAINT chk_shot_recs_complexity
            CHECK (production_complexity_level IS NULL OR production_complexity_level IN ('Low', 'Medium', 'High'));
    END IF;
END $$;

-- Index on scene_id for fast recommendation lookups
CREATE INDEX IF NOT EXISTS idx_shot_recommendations_scene_id
    ON shot_recommendations (scene_id);


-- ── 5. Table: KNOWLEDGE_BASE ──────────────────────────────────────────────────
-- knowledge_base.id is int4.
-- Add review and equipment tracking columns if missing.
ALTER TABLE knowledge_base
    ADD COLUMN IF NOT EXISTS equipment_needs    TEXT,
    ADD COLUMN IF NOT EXISTS typical_complexity TEXT NOT NULL DEFAULT 'Low',
    ADD COLUMN IF NOT EXISTS review_status      TEXT NOT NULL DEFAULT 'draft',
    ADD COLUMN IF NOT EXISTS source_note        TEXT;

-- Safely add UNIQUE constraint on technique_name if not present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_knowledge_base_technique_name'
    ) THEN
        -- Check if there are duplicate technique names before creating constraint
        IF NOT EXISTS (
            SELECT technique_name FROM knowledge_base GROUP BY technique_name HAVING COUNT(*) > 1
        ) THEN
            ALTER TABLE knowledge_base
                ADD CONSTRAINT uq_knowledge_base_technique_name UNIQUE (technique_name);
        END IF;
    END IF;
END $$;

-- Safely add review_status check constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_kb_review_status'
    ) THEN
        ALTER TABLE knowledge_base
            ADD CONSTRAINT chk_kb_review_status
            CHECK (review_status IN ('draft', 'reviewed'));
    END IF;
END $$;

-- Safely add complexity check constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_kb_complexity'
    ) THEN
        ALTER TABLE knowledge_base
            ADD CONSTRAINT chk_kb_complexity
            CHECK (typical_complexity IS NULL OR typical_complexity IN ('Low', 'Medium', 'High'));
    END IF;
END $$;

-- Indexes on category and review status for filtered browsing
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category
    ON knowledge_base (category);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_review_status
    ON knowledge_base (review_status);

-- GIN index on potential_emotions array for fast array searching
CREATE INDEX IF NOT EXISTS idx_knowledge_base_potential_emotions
    ON knowledge_base USING GIN (potential_emotions);


-- ── 6. Table: AI_USAGE ────────────────────────────────────────────────────────
-- Creates the AI rate limit tracking table if missing.
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


-- ── 7. Automatic updated_at Trigger for PROJECTS ──────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_projects_updated_at'
    ) THEN
        CREATE TRIGGER trg_projects_updated_at
            BEFORE UPDATE ON projects
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;


-- ── 8. Row Level Security (RLS) ───────────────────────────────────────────────
-- Enable RLS on all tables without dropping or altering any existing policies.
-- Direct client requests using public anon key are restricted.
-- Backend connections using DATABASE_URL bypass RLS and enforce ownership checks.
ALTER TABLE projects             ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenes               ENABLE ROW LEVEL SECURITY;
ALTER TABLE shot_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base       ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_usage             ENABLE ROW LEVEL SECURITY;
ALTER TABLE personas             ENABLE ROW LEVEL SECURITY;
ALTER TABLE audience_feedback    ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_responses ENABLE ROW LEVEL SECURITY;
