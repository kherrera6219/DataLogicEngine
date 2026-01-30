import sqlite3
import os
from backend.config_manager import get_config

def verify_sqlite_config():
    config = get_config()
    db_url = config.get("database.url")
    
    if "sqlite" not in db_url:
        print("Not using SQLite, skipping PRAGMA verification.")
        return

    # Extract path from sqlite:///path
    db_path = db_url.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    print(f"Verifying database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check Journal Mode
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    print(f"Journal Mode: {mode}")
    
    # Check Foreign Keys
    cursor.execute("PRAGMA foreign_keys")
    fk = cursor.fetchone()[0]
    print(f"Foreign Keys: {'ON' if fk else 'OFF'}")
    
    conn.close()

if __name__ == "__main__":
    verify_sqlite_config()
