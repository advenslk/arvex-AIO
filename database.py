"""Small SQLite persistence layer for conversations and warnings."""
import sqlite3
from pathlib import Path

DB_PATH = Path("arvex.db")

def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("CREATE TABLE IF NOT EXISTS messages (user_id INTEGER, role TEXT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE IF NOT EXISTS warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, moderator_id INTEGER, reason TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

def add_message(user_id, role, content):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("INSERT INTO messages(user_id,role,content) VALUES(?,?,?)", (user_id, role, content))

def history(user_id, limit=12):
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT role,content FROM messages WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    return list(reversed(rows))

def add_warning(guild_id, user_id, moderator_id, reason):
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("INSERT INTO warnings(guild_id,user_id,moderator_id,reason) VALUES(?,?,?,?)", (guild_id,user_id,moderator_id,reason))
        return cur.lastrowid

def warning_count(guild_id, user_id):
    with sqlite3.connect(DB_PATH) as db:
        return db.execute("SELECT COUNT(*) FROM warnings WHERE guild_id=? AND user_id=?", (guild_id,user_id)).fetchone()[0]
