import sqlite3
import os

DB_NAME = "ids_database.db"

def init_db():
    """Initializes the SQLite database and creates required tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create alerts table (Section 4.3.2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            src_ip TEXT,
            dst_ip TEXT,
            src_port INTEGER,
            dst_port INTEGER,
            protocol TEXT,
            attack_type TEXT,
            confidence_score REAL,
            status TEXT DEFAULT 'NEW'
        )
    ''')

    # Create system_log table (Section 4.3.2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT,
            message TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"[+] Database '{DB_NAME}' initialized successfully with 'alerts' and 'system_log' tables.")

def get_db_connection():
    """Returns a database connection for other modules to use."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows name-based access to columns
    return conn

if __name__ == "__main__":
    # Run this script directly once to create the database file
    init_db()