# FILE: internal/storage/database.py
"""
SQL database storage backend.
Supports PostgreSQL (production) and SQLite (development/testing).
Connection is configured via environment variables (see config.py).
"""
import json
import os
import sqlite3
from datetime import datetime

from internal.model.asset import Asset, ScanJob

# -- Environment-driven DB selection ----------------------------------------
DB_DRIVER = os.environ.get("DB_DRIVER", "sqlite")  # "sqlite" | "postgres"
DB_HOST     = os.environ.get("DB_HOST",     "localhost")
DB_PORT     = os.environ.get("DB_PORT",     "5432")
DB_USER     = os.environ.get("DB_USER",     "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_NAME     = os.environ.get("DB_NAME",     "mini_asm")
SQLITE_PATH = os.environ.get("SQLITE_PATH", "./mini_asm.db")


def _get_connection():
    """Return a DB connection based on DB_DRIVER env var."""
    if DB_DRIVER == "postgres":
        try:
            import psycopg2
        except ImportError:
            raise RuntimeError("psycopg2 not installed. Add 'psycopg2-binary' to requirements.txt.")
        dsn = (
            f"host={DB_HOST} port={DB_PORT} "
            f"user={DB_USER} password={DB_PASSWORD} "
            f"dbname={DB_NAME} sslmode=disable"
        )
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        return conn
    else:
        # SQLite — uses thread-check disabled for Flask's threaded mode
        conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn


def _placeholder():
    """Return the correct SQL placeholder for the active driver."""
    return "%s" if DB_DRIVER == "postgres" else "?"


class DatabaseStorage:
    """
    Persistent storage backend using SQLite or PostgreSQL.
    Implements the same interface as MemoryStorage so it can be
    swapped in transparently.
    """

    def __init__(self):
        self._run_migrations()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _conn(self):
        return _get_connection()

    def _run_migrations(self):
        """
        Apply schema migrations on startup.
        Reads SQL from migrations/001_create_assets.up.sql.
        """
        migration_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "migrations",
            "001_create_assets.up.sql"
        )
        migration_file = os.path.normpath(migration_file)
        if not os.path.exists(migration_file):
            return

        with open(migration_file, "r") as f:
            sql = f.read()

        conn = self._conn()
        try:
            cur = conn.cursor()
            # SQLite executes multiple statements via executescript
            if DB_DRIVER == "sqlite":
                conn.executescript(sql)
            else:
                # PostgreSQL: execute each statement separately
                for stmt in sql.split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        cur.execute(stmt)
                conn.commit()
        except Exception as e:
            print(f"[DB] Migration warning: {e}")
        finally:
            conn.close()

    def _row_to_asset(self, row) -> Asset:
        """Convert a DB row dict/Row to an Asset object."""
        asset = object.__new__(Asset)
        asset.id         = row["id"]
        asset.name       = row["name"]
        asset.type       = row["type"]
        asset.status     = row["status"]
        asset.tags       = json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"]
        asset.created_at = row["created_at"]
        asset.updated_at = row["updated_at"]
        return asset

    def _row_to_job(self, row) -> ScanJob:
        """Convert a DB row dict/Row to a ScanJob object."""
        job = object.__new__(ScanJob)
        job.id         = row["id"]
        job.asset_id   = row["asset_id"]
        job.scan_type  = row["scan_type"]
        job.status     = row["status"]
        job.started_at = row["started_at"]
        job.ended_at   = row["ended_at"]
        job.error      = row["error"] or ""
        job.results    = json.loads(row["results"]) if isinstance(row["results"], str) else (row["results"] or [])
        job.created_at = row["created_at"]
        return job

    # ------------------------------------------------------------------
    # Asset CRUD
    # ------------------------------------------------------------------

    def save_asset(self, asset: Asset) -> None:
        p = _placeholder()
        sql = f"""
            INSERT INTO assets (id, name, type, status, tags, created_at, updated_at)
            VALUES ({p},{p},{p},{p},{p},{p},{p})
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, type=excluded.type, status=excluded.status,
                tags=excluded.tags, updated_at=excluded.updated_at
        """
        # SQLite supports ON CONFLICT; PostgreSQL uses ON CONFLICT as well
        if DB_DRIVER == "postgres":
            sql = f"""
                INSERT INTO assets (id, name, type, status, tags, created_at, updated_at)
                VALUES ({p},{p},{p},{p},{p},{p},{p})
                ON CONFLICT(id) DO UPDATE SET
                    name=EXCLUDED.name, type=EXCLUDED.type, status=EXCLUDED.status,
                    tags=EXCLUDED.tags, updated_at=EXCLUDED.updated_at
            """
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(sql, (
                asset.id, asset.name, asset.type, asset.status,
                json.dumps(asset.tags), asset.created_at, asset.updated_at
            ))
            conn.commit()
        finally:
            conn.close()

    def get_asset(self, asset_id: str):
        p = _placeholder()
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM assets WHERE id={p}", (asset_id,))
            row = cur.fetchone()
            return self._row_to_asset(row) if row else None
        finally:
            conn.close()

    def list_assets(self) -> list:
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM assets ORDER BY created_at DESC")
            return [self._row_to_asset(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def delete_asset(self, asset_id: str) -> bool:
        p = _placeholder()
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM assets WHERE id={p}", (asset_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # ScanJob CRUD
    # ------------------------------------------------------------------

    def save_job(self, job: ScanJob) -> None:
        p = _placeholder()
        sql = f"""
            INSERT INTO scan_jobs
                (id, asset_id, scan_type, status, started_at, ended_at, error, results, created_at)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})
            ON CONFLICT(id) DO UPDATE SET
                status=excluded.status, started_at=excluded.started_at,
                ended_at=excluded.ended_at, error=excluded.error, results=excluded.results
        """
        if DB_DRIVER == "postgres":
            sql = sql.replace("excluded.", "EXCLUDED.")
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(sql, (
                job.id, job.asset_id, job.scan_type, job.status,
                job.started_at, job.ended_at, job.error,
                json.dumps(job.results), job.created_at
            ))
            conn.commit()
        finally:
            conn.close()

    def get_job(self, job_id: str):
        p = _placeholder()
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM scan_jobs WHERE id={p}", (job_id,))
            row = cur.fetchone()
            return self._row_to_job(row) if row else None
        finally:
            conn.close()

    def get_jobs_by_asset(self, asset_id: str) -> list:
        p = _placeholder()
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                f"SELECT * FROM scan_jobs WHERE asset_id={p} ORDER BY created_at DESC",
                (asset_id,)
            )
            return [self._row_to_job(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_all_results_for_asset(self, asset_id: str) -> list:
        """Aggregate all scan results across all jobs for a given asset."""
        jobs = self.get_jobs_by_asset(asset_id)
        all_results = []
        for job in jobs:
            for result in job.results:
                all_results.append({
                    "job_id": job.id,
                    "scan_type": job.scan_type,
                    "completed_at": job.ended_at,
                    "data": result,
                })
        return all_results
