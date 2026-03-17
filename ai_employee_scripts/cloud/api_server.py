"""
Deduplication API Server - Real-time coordination for local/cloud watchers

Provides REST API for email deduplication between local and cloud watchers.
Uses SQLite for persistent storage (not git synced).

Endpoints:
- POST /register - Register a processed email ID
- GET /check?id=xxx - Check if an email was processed
- GET /sync - Get all processed IDs (for initial sync)
- GET /health - Health check

Usage:
    uv run python cloud/api_server.py

Environment Variables:
    DEDUP_API_PORT - Port to run on (default: 5000)
    DEDUP_API_KEY - Optional API key for authentication
    DEDUP_DB_PATH - Path to SQLite database (default: cloud_data/processed_emails.db)
"""

import os
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, request, jsonify, g

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

API_PORT = int(os.getenv("DEDUP_API_PORT", "5000"))
API_KEY = os.getenv("DEDUP_API_KEY")

# Database path - store outside vault (not git synced)
DB_PATH = Path(os.getenv(
    "DEDUP_DB_PATH",
    str(Path(__file__).parent.parent / "cloud_data" / "processed_emails.db")
))


# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DedupAPI")


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db() -> sqlite3.Connection:
    """Get database connection for current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(error=None):
    """Close database connection after request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            email_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            processed_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_processed_at
        ON processed_emails(processed_at)
    ''')

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__)


def check_api_key() -> Optional[str]:
    """Check API key if configured. Returns error message or None."""
    if not API_KEY:
        return None  # No API key required

    provided_key = request.headers.get("X-API-Key")
    if not provided_key or provided_key != API_KEY:
        return "Invalid or missing API key"
    return None


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        db = get_db()
        cursor = db.execute("SELECT COUNT(*) FROM processed_emails")
        count = cursor.fetchone()[0]

        return jsonify({
            "status": "ok",
            "database": str(DB_PATH),
            "total_processed": count,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/register', methods=['POST'])
def register():
    """Register a processed email ID."""
    # Check API key
    error = check_api_key()
    if error:
        return jsonify({"error": error}), 401

    # Validate request
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    email_id = data.get("email_id")
    source = data.get("source", "unknown")

    if not email_id:
        return jsonify({"error": "Missing email_id"}), 400

    try:
        db = get_db()
        processed_at = datetime.now().isoformat()

        # Use INSERT OR IGNORE to handle duplicates gracefully
        db.execute(
            """
            INSERT OR IGNORE INTO processed_emails
            (email_id, source, processed_at)
            VALUES (?, ?, ?)
            """,
            (email_id, source, processed_at)
        )
        db.commit()

        logger.info(f"Registered: {email_id} from {source}")

        return jsonify({
            "success": True,
            "email_id": email_id,
            "source": source,
            "processed_at": processed_at
        })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route('/check', methods=['GET'])
def check():
    """Check if an email was processed."""
    # Check API key
    error = check_api_key()
    if error:
        return jsonify({"error": error}), 401

    email_id = request.args.get("id")
    if not email_id:
        return jsonify({"error": "Missing id parameter"}), 400

    try:
        db = get_db()
        cursor = db.execute(
            """
            SELECT source, processed_at
            FROM processed_emails
            WHERE email_id = ?
            """,
            (email_id,)
        )
        row = cursor.fetchone()

        if row:
            return jsonify({
                "processed": True,
                "email_id": email_id,
                "source": row["source"],
                "processed_at": row["processed_at"]
            })
        else:
            return jsonify({
                "processed": False,
                "email_id": email_id
            })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route('/sync', methods=['GET'])
def sync():
    """Get all processed IDs for initial sync."""
    # Check API key
    error = check_api_key()
    if error:
        return jsonify({"error": error}), 401

    try:
        db = get_db()
        cursor = db.execute("SELECT email_id FROM processed_emails")
        rows = cursor.fetchall()

        email_ids = [row["email_id"] for row in rows]

        return jsonify({
            "processed_ids": email_ids,
            "count": len(email_ids),
            "timestamp": datetime.now().isoformat()
        })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route('/stats', methods=['GET'])
def stats():
    """Get statistics about processed emails."""
    # Check API key
    error = check_api_key()
    if error:
        return jsonify({"error": error}), 401

    try:
        db = get_db()

        # Total count
        cursor = db.execute("SELECT COUNT(*) FROM processed_emails")
        total = cursor.fetchone()[0]

        # Count by source
        cursor = db.execute(
            """
            SELECT source, COUNT(*) as count
            FROM processed_emails
            GROUP BY source
            """
        )
        by_source = {row["source"]: row["count"] for row in cursor.fetchall()}

        # Last processed
        cursor = db.execute(
            """
            SELECT email_id, source, processed_at
            FROM processed_emails
            ORDER BY processed_at DESC
            LIMIT 1
            """
        )
        last_row = cursor.fetchone()
        last_processed = dict(last_row) if last_row else None

        return jsonify({
            "total": total,
            "by_source": by_source,
            "last_processed": last_processed,
            "database": str(DB_PATH)
        })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Remove old processed IDs (older than specified days)."""
    # Check API key
    error = check_api_key()
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json() or {}
    days = data.get("days", 30)  # Default: keep last 30 days

    try:
        db = get_db()

        # Delete old entries
        cursor = db.execute(
            """
            DELETE FROM processed_emails
            WHERE processed_at < datetime('now', ?)
            """,
            (f"-{days} days",)
        )
        deleted = cursor.rowcount
        db.commit()

        logger.info(f"Cleanup: removed {deleted} entries older than {days} days")

        return jsonify({
            "success": True,
            "deleted": deleted,
            "days_kept": days
        })

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    init_db()

    logger.info(f"Starting Dedup API Server on port {API_PORT}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"API Key required: {'Yes' if API_KEY else 'No'}")

    app.run(
        host='0.0.0.0',
        port=API_PORT,
        debug=False
    )