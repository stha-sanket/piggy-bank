import sqlite3
from datetime import datetime

DATABASE_PATH = 'data/coin_tracker.db'
GOALS_DATABASE_PATH = 'data/goals.db'

def get_db_connection():
    """Connect to the goals database"""
    conn = sqlite3.connect(GOALS_DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def save_weight(weight):
    """Save weight reading to the database"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.execute(
                "INSERT INTO readings (weight) VALUES (?)",
                (weight,)
            )
            conn.commit()
    except Exception as e:
        print(f"Database error: {e}")

def init_databases():
    """Initialize both databases with required tables"""
    # Initialize the main readings database
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                weight REAL NOT NULL
            )
        """)
        conn.commit()
        print(f"Database '{DATABASE_PATH}' initialized.")

    # Initialize the goals database
    with sqlite3.connect(GOALS_DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                prize REAL NOT NULL,
                image_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print(f"Database '{GOALS_DATABASE_PATH}' initialized.")

if __name__ == '__main__':
    print("Initializing databases...")
    init_databases()
    print("Databases are ready.")
