import sqlite3
import os

# Get the absolute path to the directory this file is in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Join that directory with the database file name
DB_NAME = os.path.join(BASE_DIR, "ids_database.db")

def init_db():
    """Initializes the SQLite database and creates required tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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
    print(f"[+] Database initialized successfully at: {DB_NAME}")

def get_db_connection():
    """Returns a database connection for other modules to use."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

if __name__ == "__main__":
    init_db()