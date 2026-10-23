-- ==============================================================================
-- diagnostic_queries.sql
-- READ-ONLY DIAGNOSTIC SCRIPT FOR SUPABASE POSTGRESQL
--
-- INSTRUCTIONS:
-- 1. Open Supabase Dashboard -> SQL Editor -> New query.
-- 2. Paste and run these queries one by one (or all together).
-- 3. These queries only SELECT information from system catalogs.
--    THEY DO NOT CHANGE, INSERT, UPDATE, OR DELETE ANY DATA.
-- ==============================================================================

-- ── 1. List all tables in public schema ────────────────────────────────────────
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;


-- ── 2. Detailed column definitions (types, nullability, defaults) ─────────────
SELECT 
    table_name,
    column_name,
    data_type,
    udt_name,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
    'projects', 'scenes', 'shot_recommendations', 
    'knowledge_base', 'personas', 'audience_feedback', 
    'experiment_responses', 'ai_usage'
  )
ORDER BY table_name, ordinal_position;


-- ── 3. Primary keys and Unique constraints ────────────────────────────────────
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'public'
  AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
ORDER BY tc.table_name, tc.constraint_type, kcu.ordinal_position;


-- ── 4. Foreign keys and referenced tables & columns ───────────────────────────
SELECT
    kcu.table_name AS foreign_table,
    kcu.column_name AS foreign_column,
    ccu.table_name AS primary_table,
    ccu.column_name AS primary_column,
    rc.delete_rule,
    rc.update_rule,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc
  ON tc.constraint_name = rc.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_schema = 'public'
ORDER BY kcu.table_name;


-- ── 5. Check constraints ──────────────────────────────────────────────────────
SELECT
    tc.table_name,
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc
  ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'public'
  AND tc.constraint_type = 'CHECK'
  -- Exclude system not-null check constraints
  AND cc.check_clause NOT LIKE '%IS NOT NULL%'
ORDER BY tc.table_name, tc.constraint_name;


-- ── 6. Existing Indexes ───────────────────────────────────────────────────────
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;


-- ── 7. Row Level Security (RLS) status on each table ──────────────────────────
SELECT 
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;


-- ── 8. Existing RLS policies ──────────────────────────────────────────────────
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;


-- ── 9. Inspect existing projects (safe check for ownership & type values) ──────
-- Displays existing project records using base columns guaranteed to exist:
SELECT 
    id,
    name,
    type,
    created_at,
    updated_at
FROM public.projects;

-- Verify if user_id column exists on projects:
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'projects'
  AND column_name = 'user_id';


-- ── 10. Check for duplicate technique_name in knowledge_base ──────────────────
SELECT 
    technique_name,
    COUNT(*) AS occurrences
FROM public.knowledge_base
GROUP BY technique_name
HAVING COUNT(*) > 1;


-- ── 11. Check if production_budget exists on scenes ────────────────────────────
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'scenes' 
  AND column_name = 'production_budget';


-- ── 12. Check presence of required Shot Designer columns in shot_recommendations ─
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'shot_recommendations'
  AND column_name IN (
    'rank', 'perspective_name', 'reasoning', 'visual_checklist',
    'context_caveat', 'production_complexity_level',
    'production_complexity_reason', 'budget_fit', 'budget_fit_reason',
    'knowledge_base_ids', 'model_name'
  );
