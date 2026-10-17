-- =============================================================
-- 002_later_modules.sql
-- Tables for future modules: Audience Lens, Personas,
-- Psychology Experiment.
-- No backend endpoints exist yet for these tables.
-- Run AFTER 001_foundation.sql.
-- =============================================================

-- ── PERSONAS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS personas (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             TEXT NOT NULL,
    age_range        TEXT,
    region           TEXT,
    language         TEXT,
    cultural_context TEXT,
    film_familiarity TEXT CHECK (film_familiarity IN ('Casual','Regular','Enthusiast')),
    description      TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── AUDIENCE FEEDBACK ────────────────────────────────────────
-- Stores AI-generated audience predictions per scene + persona.
CREATE TABLE IF NOT EXISTS audience_feedback (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id                  UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    persona_id                UUID REFERENCES personas(id) ON DELETE SET NULL,
    empathy_score             NUMERIC(3,1) CHECK (empathy_score BETWEEN 1 AND 7),
    perceived_power_score     NUMERIC(3,1) CHECK (perceived_power_score BETWEEN 1 AND 7),
    blame_score               NUMERIC(3,1) CHECK (blame_score BETWEEN 1 AND 7),
    emotional_intensity_score NUMERIC(3,1) CHECK (emotional_intensity_score BETWEEN 1 AND 7),
    overall_interpretation    TEXT,
    reasoning                 TEXT,
    model_name                TEXT,
    created_at                TIMESTAMPTZ DEFAULT NOW()
);

-- ── EXPERIMENT RESPONSES ─────────────────────────────────────
-- Stores human participant ratings for the psychology experiment.
-- participant_code is an anonymised identifier — no real names.
CREATE TABLE IF NOT EXISTS experiment_responses (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id                  UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    participant_code          TEXT NOT NULL,
    empathy_score             NUMERIC(3,1) CHECK (empathy_score BETWEEN 1 AND 7),
    perceived_power_score     NUMERIC(3,1) CHECK (perceived_power_score BETWEEN 1 AND 7),
    blame_score               NUMERIC(3,1) CHECK (blame_score BETWEEN 1 AND 7),
    emotional_intensity_score NUMERIC(3,1) CHECK (emotional_intensity_score BETWEEN 1 AND 7),
    notes                     TEXT,
    created_at                TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_experiment_responses_scene
    ON experiment_responses (scene_id);

CREATE INDEX IF NOT EXISTS idx_experiment_responses_participant
    ON experiment_responses (participant_code);

-- ── ROW LEVEL SECURITY ───────────────────────────────────────
ALTER TABLE personas             ENABLE ROW LEVEL SECURITY;
ALTER TABLE audience_feedback    ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_responses ENABLE ROW LEVEL SECURITY;
