import json
import secrets
import sqlite3
import string
import threading
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "analytics.db"

_local = threading.local()

_DIAGNOSTIC_COLUMNS = {
    "request_id": "TEXT",
    "model": "TEXT",
    "attempts": "INTEGER",
    "error_kind": "TEXT",
    "status_code": "INTEGER",
}


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _local.conn = sqlite3.connect(str(DB_PATH))
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _init_db(_local.conn)
    return _local.conn


def _init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            topic TEXT NOT NULL,
            grid_size INTEGER NOT NULL,
            words_requested INTEGER NOT NULL,
            words_placed INTEGER NOT NULL,
            provider TEXT NOT NULL,
            duration_ms INTEGER NOT NULL,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            error TEXT
        )
    """)
    # Diagnostic columns added after the initial schema; ALTER keeps existing databases working.
    existing = {row[1] for row in conn.execute("PRAGMA table_info(generations)")}
    for col, ddl in _DIAGNOSTIC_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE generations ADD COLUMN {col} {ddl}")
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_gen_created ON generations(created_at)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS puzzles (
            puzzle_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)
    conn.commit()


def log_generation(
    topic: str,
    grid_size: int,
    words_requested: int,
    words_placed: int,
    provider: str,
    duration_ms: int,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    error: str | None = None,
    request_id: str | None = None,
    model: str | None = None,
    attempts: int | None = None,
    error_kind: str | None = None,
    status_code: int | None = None,
):
    conn = _get_conn()
    conn.execute(
        """INSERT INTO generations
           (created_at, topic, grid_size, words_requested, words_placed,
            provider, duration_ms, prompt_tokens, completion_tokens, total_tokens, error,
            request_id, model, attempts, error_kind, status_code)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            topic,
            grid_size,
            words_requested,
            words_placed,
            provider,
            duration_ms,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            error,
            request_id,
            model,
            attempts,
            error_kind,
            status_code,
        ),
    )
    conn.commit()


def get_stats() -> dict:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row

    now_utc = datetime.now(timezone.utc).isoformat()

    total = conn.execute("SELECT COUNT(*) as c FROM generations WHERE error IS NULL").fetchone()["c"]
    errors = conn.execute("SELECT COUNT(*) as c FROM generations WHERE error IS NOT NULL").fetchone()["c"]

    today = conn.execute(
        "SELECT COUNT(*) as c FROM generations WHERE error IS NULL AND created_at >= date('now')"
    ).fetchone()["c"]

    last_7d = conn.execute(
        "SELECT COUNT(*) as c FROM generations WHERE error IS NULL AND created_at >= date('now', '-7 days')"
    ).fetchone()["c"]

    last_30d = conn.execute(
        "SELECT COUNT(*) as c FROM generations WHERE error IS NULL AND created_at >= date('now', '-30 days')"
    ).fetchone()["c"]

    avg_duration = conn.execute(
        "SELECT AVG(duration_ms) as avg FROM generations WHERE error IS NULL"
    ).fetchone()["avg"]

    avg_placement = conn.execute(
        "SELECT AVG(CAST(words_placed AS REAL) / words_requested) as avg FROM generations WHERE error IS NULL AND words_requested > 0"
    ).fetchone()["avg"]

    total_prompt_tokens = conn.execute(
        "SELECT COALESCE(SUM(prompt_tokens), 0) as s FROM generations"
    ).fetchone()["s"]
    total_completion_tokens = conn.execute(
        "SELECT COALESCE(SUM(completion_tokens), 0) as s FROM generations"
    ).fetchone()["s"]
    total_all_tokens = conn.execute(
        "SELECT COALESCE(SUM(total_tokens), 0) as s FROM generations"
    ).fetchone()["s"]

    top_topics = conn.execute(
        """SELECT LOWER(topic) as topic, COUNT(*) as count
           FROM generations WHERE error IS NULL
           GROUP BY LOWER(topic) ORDER BY count DESC LIMIT 20"""
    ).fetchall()

    grid_sizes = conn.execute(
        """SELECT grid_size, COUNT(*) as count
           FROM generations WHERE error IS NULL
           GROUP BY grid_size ORDER BY count DESC"""
    ).fetchall()

    hourly = conn.execute(
        """SELECT CAST(strftime('%H', created_at) AS INTEGER) as hour, COUNT(*) as count
           FROM generations WHERE error IS NULL
           GROUP BY hour ORDER BY count DESC LIMIT 5"""
    ).fetchall()

    daily = conn.execute(
        """SELECT date(created_at) as day, COUNT(*) as count
           FROM generations WHERE error IS NULL
           GROUP BY day ORDER BY day DESC LIMIT 30"""
    ).fetchall()

    last_error = conn.execute(
        "SELECT error, created_at FROM generations WHERE error IS NOT NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()

    error_breakdown = conn.execute(
        """SELECT COALESCE(error_kind, 'legacy') as kind, status_code, provider, COUNT(*) as count
           FROM generations
           WHERE error IS NOT NULL AND created_at >= date('now', '-7 days')
           GROUP BY kind, status_code, provider ORDER BY count DESC"""
    ).fetchall()

    recent_errors = conn.execute(
        """SELECT created_at, request_id, provider, model, attempts, error_kind,
                  status_code, duration_ms, error
           FROM generations WHERE error IS NOT NULL ORDER BY id DESC LIMIT 20"""
    ).fetchall()

    # Successes that needed more than one attempt show how often retries are saving requests.
    retried_ok = conn.execute(
        """SELECT COUNT(*) as c FROM generations
           WHERE error IS NULL AND attempts > 1 AND created_at >= date('now', '-7 days')"""
    ).fetchone()["c"]

    recent = conn.execute(
        """SELECT topic, grid_size, words_placed, words_requested, duration_ms,
                  total_tokens, created_at
           FROM generations WHERE error IS NULL ORDER BY id DESC LIMIT 10"""
    ).fetchall()

    return {
        "generated_at": now_utc,
        "counts": {
            "total": total,
            "today": today,
            "last_7d": last_7d,
            "last_30d": last_30d,
            "errors": errors,
        },
        "performance": {
            "avg_duration_ms": round(avg_duration) if avg_duration else 0,
            "avg_placement_rate": round(avg_placement * 100, 1) if avg_placement else 0,
        },
        "tokens": {
            "prompt": total_prompt_tokens,
            "completion": total_completion_tokens,
            "total": total_all_tokens,
        },
        "top_topics": [{"topic": r["topic"], "count": r["count"]} for r in top_topics],
        "grid_sizes": [{"size": r["grid_size"], "count": r["count"]} for r in grid_sizes],
        "peak_hours": [{"hour": r["hour"], "count": r["count"]} for r in hourly],
        "daily": [{"date": r["day"], "count": r["count"]} for r in daily],
        "last_error": {
            "message": last_error["error"],
            "at": last_error["created_at"],
        } if last_error else None,
        "reliability_7d": {
            "succeeded_after_retry": retried_ok,
            "errors": [
                {"kind": r["kind"], "status": r["status_code"], "provider": r["provider"], "count": r["count"]}
                for r in error_breakdown
            ],
        },
        "recent_errors": [dict(r) for r in recent_errors],
        "recent": [
            {
                "topic": r["topic"],
                "grid_size": r["grid_size"],
                "words": f"{r['words_placed']}/{r['words_requested']}",
                "duration_ms": r["duration_ms"],
                "tokens": r["total_tokens"],
                "at": r["created_at"],
            }
            for r in recent
        ],
    }


_ID_CHARS = string.ascii_lowercase + string.digits


def _generate_id(length: int = 8) -> str:
    return "".join(secrets.choice(_ID_CHARS) for _ in range(length))


def save_puzzle(puzzle_data: dict) -> str:
    conn = _get_conn()
    puzzle_id = _generate_id()
    conn.execute(
        "INSERT INTO puzzles (puzzle_id, created_at, data) VALUES (?, ?, ?)",
        (puzzle_id, datetime.now(timezone.utc).isoformat(), json.dumps(puzzle_data)),
    )
    conn.commit()
    return puzzle_id


def load_puzzle(puzzle_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT data FROM puzzles WHERE puzzle_id = ?", (puzzle_id,)
    ).fetchone()
    if not row:
        return None
    return json.loads(row[0])
