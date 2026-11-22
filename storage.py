"""SQLite storage for BuildGuard AI detection runs and model predictions."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "buildguard.db"


def _connect():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DATABASE_PATH), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Create the database and required tables if they do not exist."""
    with _connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS detection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source_type TEXT NOT NULL CHECK(source_type IN ('image', 'video')),
                file_name TEXT NOT NULL,
                file_size INTEGER,
                status TEXT NOT NULL CHECK(status IN ('success', 'failed')),
                duration_seconds REAL,
                frames_analyzed INTEGER,
                error TEXT
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                frame_timestamp REAL,
                class_id INTEGER,
                class_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                x1 REAL,
                y1 REAL,
                x2 REAL,
                y2 REAL,
                FOREIGN KEY(run_id) REFERENCES detection_runs(id) ON DELETE CASCADE
            )
        """)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_runs_created_at ON detection_runs(created_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_run_id ON predictions(run_id)"
        )


def save_detection_run(
    source_type,
    file_name,
    file_size,
    detections,
    status="success",
    duration_seconds=None,
    frames_analyzed=None,
    error=None,
):
    """Save one analyzed file and its individual model predictions; return its ID.

    Each video prediction is stored separately with its sampled-frame timestamp.
    Counts therefore represent predictions across sampled frames, not unique people.
    """
    if source_type not in {"image", "video"}:
        raise ValueError("source_type must be 'image' or 'video'")
    if status not in {"success", "failed"}:
        raise ValueError("status must be 'success' or 'failed'")

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO detection_runs
            (created_at, source_type, file_name, file_size, status,
             duration_seconds, frames_analyzed, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at, source_type, str(file_name), file_size, status,
                duration_seconds, frames_analyzed, error,
            ),
        )
        run_id = cursor.lastrowid

        prediction_rows = []
        for item in detections or []:
            prediction_rows.append((
                run_id,
                item.get("frame_timestamp"),
                item.get("class_id"),
                str(item.get("class_name", "Unknown")),
                float(item.get("confidence", 0.0)),
                item.get("x1"),
                item.get("y1"),
                item.get("x2"),
                item.get("y2"),
            ))

        if prediction_rows:
            connection.executemany(
                """
                INSERT INTO predictions
                (run_id, frame_timestamp, class_id, class_name, confidence,
                 x1, y1, x2, y2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                prediction_rows,
            )
    return run_id


def get_dashboard_stats():
    """Return real totals calculated from the local SQLite database."""
    init_db()
    with _connect() as connection:
        run_stats = connection.execute("""
            SELECT
                COUNT(*) AS total_runs,
                SUM(CASE WHEN source_type = 'image' THEN 1 ELSE 0 END) AS image_runs,
                SUM(CASE WHEN source_type = 'video' THEN 1 ELSE 0 END) AS video_runs,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_runs
            FROM detection_runs
        """).fetchone()
        prediction_count = connection.execute(
            "SELECT COUNT(*) FROM predictions"
        ).fetchone()[0]

    return {
        "total_runs": run_stats["total_runs"] or 0,
        "image_runs": run_stats["image_runs"] or 0,
        "video_runs": run_stats["video_runs"] or 0,
        "failed_runs": run_stats["failed_runs"] or 0,
        "total_predictions": prediction_count or 0,
    }


def get_detection_history(limit=50):
    """Return recent analyzed files, newest first, with prediction counts."""
    init_db()
    safe_limit = max(1, min(int(limit), 500))
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT
                r.id, r.created_at, r.source_type, r.file_name, r.status,
                r.duration_seconds, r.frames_analyzed, r.error,
                COUNT(p.id) AS prediction_count
            FROM detection_runs AS r
            LEFT JOIN predictions AS p ON p.run_id = r.id
            GROUP BY r.id
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_run_details(run_id):
    """Return one run and all its stored predictions."""
    init_db()
    with _connect() as connection:
        run = connection.execute(
            "SELECT * FROM detection_runs WHERE id = ?", (int(run_id),)
        ).fetchone()
        if run is None:
            return None
        predictions = connection.execute(
            "SELECT * FROM predictions WHERE run_id = ? ORDER BY id",
            (int(run_id),),
        ).fetchall()
    return {"run": dict(run), "predictions": [dict(row) for row in predictions]}
