-- =============================================================
-- 004_schema_reconciliation.sql
-- Non-destructive performance indexes, verification triggers,
-- and schema reconciliation for Emotional Mapping Backend.
--
-- Rules:
--   * Idempotent (IF NOT EXISTS everywhere).
--   * NEVER drops or truncates any existing table, column, or data.
--   * Does not modify existing RLS settings.
--   * Safe to run multiple times.
--
-- Run in: Supabase Dashboard -> SQL Editor -> New query
-- =============================================================

-- ── PERFORMANCE INDEXES ───────────────────────────────────────
-- PostgreSQL does NOT automatically index foreign keys.
-- Adding indexes prevents full table sequential scans during
-- joins, cascades, and ownership-filtered queries.

-- Projects index on user_id for fast user project listings
CREATE INDEX IF NOT EXISTS idx_projects_user_id
    ON projects (user_id);

-- Scenes index on project_id for fast cascading lookups & joins
CREATE INDEX IF NOT EXISTS idx_scenes_project_id
    ON scenes (project_id);

-- Shot recommendations index on scene_id
CREATE INDEX IF NOT EXISTS idx_shot_recommendations_scene_id
    ON shot_recommendations (scene_id);

-- Knowledge base index on category for filtered browsing
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category
    ON knowledge_base (category);

-- Knowledge base index on review_status
CREATE INDEX IF NOT EXISTS idx_knowledge_base_review_status
    ON knowledge_base (review_status);

-- GIN index on knowledge_base potential_emotions array for fast emotion filtering
CREATE INDEX IF NOT EXISTS idx_knowledge_base_potential_emotions
    ON knowledge_base USING GIN (potential_emotions);

-- ── UPDATED_AT TRIGGER ─────────────────────────────────────────
-- Automatically updates updated_at whenever a project row is modified
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
