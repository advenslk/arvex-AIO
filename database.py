"""SQLite persistence for ArveX AI memory, conversations and moderation."""
import sqlite3
from pathlib import Path

DB_PATH = Path("arvex.db")


def _connect():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    return db


def init_db():
    with _connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS messages (user_id INTEGER, role TEXT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE IF NOT EXISTS warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, moderator_id INTEGER, reason TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE IF NOT EXISTS user_profiles (user_id INTEGER PRIMARY KEY, display_name TEXT, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, memory TEXT, source TEXT DEFAULT 'user', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")


def upsert_user(user_id, display_name):
    with _connect() as db:
        db.execute("INSERT INTO user_profiles(user_id,display_name) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET display_name=excluded.display_name,last_seen=CURRENT_TIMESTAMP", (user_id, display_name))


def add_message(user_id, role, content):
    with _connect() as db:
        db.execute("INSERT INTO messages(user_id,role,content) VALUES(?,?,?)", (user_id, role, content))


def history(user_id, limit=12):
    with _connect() as db:
        rows = db.execute("SELECT role,content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?", (user_id, limit)).fetchall()
    return list(reversed(rows))


def add_memory(user_id, memory, source="user"):
    memory = memory.strip()
    if not memory:
        return
    with _connect() as db:
        db.execute("INSERT INTO memories(user_id,memory,source) VALUES(?,?,?)", (user_id, memory, source))


def get_memories(user_id, limit=8):
    with _connect() as db:
        return [r[0] for r in db.execute("SELECT memory FROM memories WHERE user_id=? ORDER BY updated_at DESC, id DESC LIMIT ?", (user_id, limit)).fetchall()]


def forget_memories(user_id):
    with _connect() as db:
        db.execute("DELETE FROM memories WHERE user_id=?", (user_id,))


def add_warning(guild_id, user_id, moderator_id, reason):
    with _connect() as db:
        cur = db.execute("INSERT INTO warnings(guild_id,user_id,moderator_id,reason) VALUES(?,?,?,?)", (guild_id,user_id,moderator_id,reason))
        return cur.lastrowid


def warning_count(guild_id, user_id):
    with _connect() as db:
        return db.execute("SELECT COUNT(*) FROM warnings WHERE guild_id=? AND user_id=?", (guild_id,user_id)).fetchone()[0]
