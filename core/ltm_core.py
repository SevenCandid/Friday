"""
Long-Term Memory Core for SEVEN.
Provides persistent fact storage using SQLite — facts survive restarts and rebuilds.
"""
from .path_helper import get_project_root
import os
import sqlite3
import datetime

DB_PATH = os.path.join(get_project_root(), "seven_memory.db")

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


def get_all_facts_with_ids() -> list[tuple]:
    """Retrieves all stored facts with their IDs and timestamps."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, fact, timestamp FROM UserFacts ORDER BY id ASC')
        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"[LTM Error] Failed to retrieve facts: {e}")
        return []


def delete_fact_by_id(fact_id: int) -> bool:
    """Deletes a specific fact by its ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM UserFacts WHERE id = ?', (fact_id,))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        if deleted:
            print(f"[LTM] Deleted fact ID: {fact_id}")
        return deleted
    except Exception as e:
        print(f"[LTM Error] Failed to delete fact: {e}")
        return False


def delete_last_fact() -> str:
    """Deletes the most recently saved fact. Returns the deleted fact text."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, fact FROM UserFacts ORDER BY id DESC LIMIT 1')
        row = c.fetchone()
        if row:
            c.execute('DELETE FROM UserFacts WHERE id = ?', (row[0],))
            conn.commit()
            conn.close()
            print(f"[LTM] Deleted last fact: {row[1]}")
            return row[1]
        conn.close()
        return ""
    except Exception as e:
        print(f"[LTM Error] Failed to delete last fact: {e}")
        return ""


def search_facts(keyword: str) -> list[tuple]:
    """Searches facts containing a keyword. Returns list of (id, fact)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, fact FROM UserFacts WHERE fact LIKE ? ORDER BY id ASC',
                  (f'%{keyword}%',))
        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"[LTM Error] Search failed: {e}")
        return []


def clear_memory():
    """Deletes all facts (used for resetting memory)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM UserFacts')
    conn.commit()
    conn.close()
    print("[LTM] Memory cleared.")


def fact_count() -> int:
    """Returns the total number of stored facts."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM UserFacts')
        count = c.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0
