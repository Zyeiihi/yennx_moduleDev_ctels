-- Migration 001: Create assets table
CREATE TABLE IF NOT EXISTS assets (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    type       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'active',
    tags       TEXT NOT NULL DEFAULT '["Unassigned"]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_assets_type   ON assets(type);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);

-- Migration 001: Create scan_jobs table
CREATE TABLE IF NOT EXISTS scan_jobs (
    id         TEXT PRIMARY KEY,
    asset_id   TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    scan_type  TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT,
    ended_at   TEXT,
    error      TEXT NOT NULL DEFAULT '',
    results    TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scan_jobs_asset_id ON scan_jobs(asset_id);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_status   ON scan_jobs(status);
