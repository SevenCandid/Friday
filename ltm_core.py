from path_helper import get_project_root
import os
import sqlite3
import datetime

DB_PATH = os.path.join(get_project_root(), "friday_memory.db")

def _init_db():
    """Initializes the SQLite database and creates the tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS UserFacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize on module import
_init_db()


def save_fact(fact: str):
    """Saves a new fact to the long-term memory database."""
    if not fact or not fact.strip():
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO UserFacts (fact, timestamp) VALUES (?, ?)', 
              (fact.strip(), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print(f"[LTM] Saved fact: {fact}")


def get_all_facts() -> list[str]:
    """Retrieves all stored facts from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT fact FROM UserFacts ORDER BY id ASC')
        results = [row[0] for row in c.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"[LTM Error] Failed to retrieve facts: {e}")
        return []

def clear_memory():
    """Deletes all facts (used for resetting memory)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM UserFacts')
    conn.commit()
    conn.close()
    print("[LTM] Memory cleared.")
