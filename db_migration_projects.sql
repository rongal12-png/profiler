-- ============================================================
-- Migration: Add Project Workspace
-- Run this once against your PostgreSQL database.
-- Safe to run on an existing DB (uses IF NOT EXISTS / IF EXISTS).
-- ============================================================

-- 1. Create the projects table
CREATE TABLE IF NOT EXISTS projects (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR NOT NULL,
    description VARCHAR,
    wallet_list TEXT    NOT NULL,
    wallet_count INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_projects_name UNIQUE (name)
);

CREATE INDEX IF NOT EXISTS ix_projects_id ON projects (id);

-- 2. Add project_id FK to analysis_jobs (nullable — existing rows are unaffected)
ALTER TABLE analysis_jobs
    ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects (id) ON DELETE SET NULL;

-- Optional: index for fast "jobs for project" queries
CREATE INDEX IF NOT EXISTS ix_analysis_jobs_project_id ON analysis_jobs (project_id);

-- ============================================================
-- Verify
-- ============================================================
-- SELECT table_name FROM information_schema.tables WHERE table_name = 'projects';
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'analysis_jobs' AND column_name = 'project_id';
