import sqlite3
import os

def init_db():
    conn = sqlite3.connect('coin_tracker.db')
    c = conn.cursor()
    
    # Create goals table
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  prize REAL NOT NULL,
                  image_path TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create weight history table
    c.execute('''CREATE TABLE IF NOT EXISTS weight_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  weight REAL NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("Database initialized")

def get_db_connection():
    conn = sqlite3.connect('coin_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

def save_weight(weight):
    """Save weight to history"""
    conn = get_db_connection()
    conn.execute('INSERT INTO weight_history (weight) VALUES (?)', (weight,))
    conn.commit()
    conn.close()

def get_last_weight():
    """Get the most recent weight"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT weight FROM weight_history ORDER BY timestamp DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row['weight'] if row else 0.0

# Initialize database
init_db()