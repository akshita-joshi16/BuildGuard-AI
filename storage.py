"""SQLite storage and analytics for BuildGuard AI (multi-user)."""

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


def _require_user(user_id):
    """Every storage call must belong to a real, non-empty user."""
    user_id = str(user_id or "").strip().lower()
    if not user_id:
        raise PermissionError("A signed-in user is required.")
    return user_id


def init_db():
    """Create tables if missing, and upgrade an older single-user database."""
    with _connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS detection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                source_type TEXT NOT NULL
                    CHECK(source_type IN ('image', 'video')),
                file_name TEXT NOT NULL,
                file_size INTEGER,
                status TEXT NOT NULL
                    CHECK(status IN ('success', 'failed')),
                duration_seconds REAL,
                frames_analyzed INTEGER,
                error TEXT
            )
        """)

        # Upgrade older databases that were created before user accounts.
        # Old rows get user_id = '' and are never shown to any real user.
        columns = [
            row["name"]
            for row in connection.execute("PRAGMA table_info(detection_runs)")
        ]
        if "user_id" not in columns:
            connection.execute(
                "ALTER TABLE detection_runs "
                "ADD COLUMN user_id TEXT NOT NULL DEFAULT ''"
            )

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
                FOREIGN KEY(run_id)
                    REFERENCES detection_runs(id) ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_created_at
            ON detection_runs(created_at)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_user_id
            ON detection_runs(user_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_run_id
            ON predictions(run_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_class_name
            ON predictions(class_name)
        """)


def _normalize_days(days):
    """Validate an analytics date range. None means all available history."""
    if days is None:
        return None
    return max(1, min(int(days), 3650))


def _date_filter(days, column="r.created_at"):
    """Return a safe SQL date filter and its parameters."""
    safe_days = _normalize_days(days)

    if safe_days is None:
        return "", ()

    return f" AND date({column}) >= date('now', ?)", (
        f"-{safe_days - 1} days",
    )


def save_detection_run(
    user_id,
    source_type,
    file_name,
    file_size,
    detections,
    status="success",
    duration_seconds=None,
    frames_analyzed=None,
    error=None,
):
    """Save an analyzed file and its predictions for one user."""
    user_id = _require_user(user_id)

    if source_type not in {"image", "video"}:
        raise ValueError("source_type must be 'image' or 'video'")

    if status not in {"success", "failed"}:
        raise ValueError("status must be 'success' or 'failed'")

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO detection_runs
            (user_id, created_at, source_type, file_name, file_size, status,
             duration_seconds, frames_analyzed, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                created_at,
                source_type,
                str(file_name),
                file_size,
                status,
                duration_seconds,
                frames_analyzed,
                error,
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
                (run_id, frame_timestamp, class_id, class_name,
                 confidence, x1, y1, x2, y2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                prediction_rows,
            )

    return run_id


def get_dashboard_stats(user_id):
    """Return overall dashboard totals for one user."""
    user_id = _require_user(user_id)
    init_db()

    with _connect() as connection:
        run_stats = connection.execute(
            """
            SELECT
                COUNT(*) AS total_runs,
                SUM(CASE WHEN source_type = 'image'
                    THEN 1 ELSE 0 END) AS image_runs,
                SUM(CASE WHEN source_type = 'video'
                    THEN 1 ELSE 0 END) AS video_runs,
                SUM(CASE WHEN status = 'failed'
                    THEN 1 ELSE 0 END) AS failed_runs
            FROM detection_runs
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        prediction_count = connection.execute(
            """
            SELECT COUNT(p.id)
            FROM predictions AS p
            JOIN detection_runs AS r ON r.id = p.run_id
            WHERE r.user_id = ?
            """,
            (user_id,),
        ).fetchone()[0]

    return {
        "total_runs": run_stats["total_runs"] or 0,
        "image_runs": run_stats["image_runs"] or 0,
        "video_runs": run_stats["video_runs"] or 0,
        "failed_runs": run_stats["failed_runs"] or 0,
        "total_predictions": prediction_count or 0,
    }


def get_detection_history(user_id, limit=50):
    """Return one user's recent analyzed files with prediction counts."""
    user_id = _require_user(user_id)
    init_db()
    safe_limit = max(1, min(int(limit), 500))

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT
                r.id,
                r.created_at,
                r.source_type,
                r.file_name,
                r.status,
                r.duration_seconds,
                r.frames_analyzed,
                r.error,
                COUNT(p.id) AS prediction_count
            FROM detection_runs AS r
            LEFT JOIN predictions AS p ON p.run_id = r.id
            WHERE r.user_id = ?
            GROUP BY r.id
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (user_id, safe_limit),
        ).fetchall()

    return [dict(row) for row in rows]


def get_run_details(user_id, run_id):
    """Return one run and its predictions, only if it belongs to the user."""
    user_id = _require_user(user_id)
    init_db()

    with _connect() as connection:
        run = connection.execute(
            "SELECT * FROM detection_runs WHERE id = ? AND user_id = ?",
            (int(run_id), user_id),
        ).fetchone()

        if run is None:
            return None

        predictions = connection.execute(
            """
            SELECT * FROM predictions
            WHERE run_id = ?
            ORDER BY id
            """,
            (int(run_id),),
        ).fetchall()

    run_dict = dict(run)
    run_dict.pop("user_id", None)  # never expose the owner field to the UI

    return {
        "run": run_dict,
        "predictions": [dict(row) for row in predictions],
    }


# ==========================================================
# ANALYTICS FUNCTIONS (all scoped to one user)
# ==========================================================

def get_daily_detection_trends(user_id, days=30):
    """Return a user's daily image/video runs and prediction counts."""
    user_id = _require_user(user_id)
    init_db()
    date_filter, date_params = _date_filter(days)

    with _connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                date(r.created_at) AS detection_date,
                COUNT(DISTINCT r.id) AS total_runs,
                COUNT(DISTINCT CASE
                    WHEN r.source_type = 'image' THEN r.id
                END) AS image_runs,
                COUNT(DISTINCT CASE
                    WHEN r.source_type = 'video' THEN r.id
                END) AS video_runs,
                COUNT(p.id) AS prediction_count
            FROM detection_runs AS r
            LEFT JOIN predictions AS p ON p.run_id = r.id
            WHERE r.status = 'success'
              AND r.user_id = ?
            {date_filter}
            GROUP BY date(r.created_at)
            ORDER BY detection_date ASC
            """,
            (user_id,) + date_params,
        ).fetchall()

    return [dict(row) for row in rows]


def get_class_distribution(user_id, days=30):
    """Return a user's prediction counts grouped by detected class."""
    user_id = _require_user(user_id)
    init_db()
    date_filter, date_params = _date_filter(days)

    with _connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                p.class_name,
                COUNT(p.id) AS prediction_count,
                ROUND(AVG(p.confidence), 4) AS average_confidence
            FROM predictions AS p
            JOIN detection_runs AS r ON r.id = p.run_id
            WHERE r.status = 'success'
              AND r.user_id = ?
            {date_filter}
            GROUP BY p.class_name
            ORDER BY prediction_count DESC
            """,
            (user_id,) + date_params,
        ).fetchall()

    return [dict(row) for row in rows]


def get_source_type_stats(user_id, days=30):
    """Compare a user's successful image and video analysis runs."""
    user_id = _require_user(user_id)
    init_db()
    date_filter, date_params = _date_filter(days)

    with _connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                r.source_type,
                COUNT(DISTINCT r.id) AS total_runs,
                COUNT(p.id) AS prediction_count
            FROM detection_runs AS r
            LEFT JOIN predictions AS p ON p.run_id = r.id
            WHERE r.status = 'success'
              AND r.user_id = ?
            {date_filter}
            GROUP BY r.source_type
            ORDER BY r.source_type
            """,
            (user_id,) + date_params,
        ).fetchall()

    return [dict(row) for row in rows]


def get_confidence_stats(user_id, days=30):
    """Return a user's overall model prediction confidence statistics."""
    user_id = _require_user(user_id)
    init_db()
    date_filter, date_params = _date_filter(days)

    with _connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                COUNT(p.id) AS prediction_count,
                ROUND(AVG(p.confidence), 4) AS average_confidence,
                ROUND(MIN(p.confidence), 4) AS minimum_confidence,
                ROUND(MAX(p.confidence), 4) AS maximum_confidence
            FROM predictions AS p
            JOIN detection_runs AS r ON r.id = p.run_id
            WHERE r.status = 'success'
              AND r.user_id = ?
            {date_filter}
            """,
            (user_id,) + date_params,
        ).fetchone()

    return {
        "prediction_count": row["prediction_count"] or 0,
        "average_confidence": row["average_confidence"],
        "minimum_confidence": row["minimum_confidence"],
        "maximum_confidence": row["maximum_confidence"],
    }


def get_analytics_summary(user_id, days=30):
    """Return a user's combined summary for the analytics dashboard."""
    user_id = _require_user(user_id)
    init_db()
    date_filter, date_params = _date_filter(days)

    with _connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_runs,
                SUM(CASE WHEN status = 'success'
                    THEN 1 ELSE 0 END) AS successful_runs,
                SUM(CASE WHEN status = 'failed'
                    THEN 1 ELSE 0 END) AS failed_runs
            FROM detection_runs AS r
            WHERE r.user_id = ?
            {date_filter}
            """,
            (user_id,) + date_params,
        ).fetchone()

        prediction_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM predictions AS p
            JOIN detection_runs AS r ON r.id = p.run_id
            WHERE r.status = 'success'
              AND r.user_id = ?
            {date_filter}
            """,
            (user_id,) + date_params,
        ).fetchone()[0]

    return {
        "total_runs": row["total_runs"] or 0,
        "successful_runs": row["successful_runs"] or 0,
        "failed_runs": row["failed_runs"] or 0,
        "total_predictions": prediction_count or 0,
    }
