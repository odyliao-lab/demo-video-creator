"""SQLite 紀錄：來源、權利聲明、模型、企劃與批准（文件 4 節關卡 5 的可追溯性）。"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .schemas import Phase1Result

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    source_path TEXT NOT NULL,
    rights TEXT NOT NULL,
    user_request TEXT,
    analyzer_model TEXT,
    planner_model TEXT,
    result_json TEXT
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    approved_at TEXT NOT NULL,
    treatment_title TEXT,
    edited_json TEXT
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.executescript(_SCHEMA)
    return conn


def save_run(result: Phase1Result) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO runs (created_at, source_path, rights, user_request,"
            " analyzer_model, planner_model, result_json) VALUES (?,?,?,?,?,?,?)",
            (
                datetime.now(timezone.utc).isoformat(),
                result.source_path,
                result.rights.value,
                result.user_request,
                result.analyzer_model,
                result.planner_model_used,
                result.model_dump_json(),
            ),
        )
        return cur.lastrowid


def save_approval(run_id: int, treatment_title: str, edited_json: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO approvals (run_id, approved_at, treatment_title, edited_json)"
            " VALUES (?,?,?,?)",
            (run_id, datetime.now(timezone.utc).isoformat(), treatment_title, edited_json),
        )


def list_runs() -> list[dict]:
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, created_at, source_path, rights, planner_model FROM runs"
            " ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
