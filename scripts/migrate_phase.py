"""
One-time migration for Phase 9.5:
- Adds 'is_media' column to attachments table.
Run: python scripts/migrate_phase9_5.py
"""
import sqlite3
import os
from app.config import settings
def migrate():
    db_url = settings.database_url
    if not db_url.startswith("sqlite"):
        print("⚠️ This migration is for SQLite. Adapt for Postgres if needed.")
        return
    # Extract path from sqlite:///path
    db_path = db_url.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Nothing to migrate.")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Check if column already exists
    cursor.execute("PRAGMA table_info(attachments)")
    columns = [row[1] for row in cursor.fetchall()]
    if "is_media" in columns:
        print("✅ Column 'is_media' already exists. Nothing to do.")
    else:
        print("Adding 'is_media' column to attachments...")
        cursor.execute(
            "ALTER TABLE attachments ADD COLUMN is_media BOOLEAN NOT NULL DEFAULT 0"
        )
        conn.commit()
        print("✅ Migration complete.")
    # Also ensure VIDEO type is accepted (SQLAlchemy will handle this since
    # the Enum is stored as VARCHAR — no schema change needed)
    conn.close()
if __name__ == "__main__":
    migrate()