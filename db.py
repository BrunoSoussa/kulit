import os
import sqlite3
from contextlib import contextmanager
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "app.db"))


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                diagnosis_json TEXT NOT NULL,
                diagnosis TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )


def create_user(name: str, email: str, password: str) -> bool:
    password_hash = generate_password_hash(password)
    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email.lower().strip(), password_hash),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_by_email(email: str):
    with get_db() as db:
        cur = db.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        return cur.fetchone()


def verify_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None
    if check_password_hash(user["password_hash"], password):
        return user
    return None


def save_analysis(user_id: int, image_path: str, diagnosis_json: str, diagnosis: Optional[str] = None):
    if not user_id:
        print("save_analysis: user_id ausente")
        return
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                diagnosis_json TEXT NOT NULL,
                diagnosis TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        db.execute(
            "INSERT INTO analyses (user_id, image_path, diagnosis_json, diagnosis) VALUES (?, ?, ?, ?)",
            (user_id, image_path, diagnosis_json, diagnosis),
        )


def list_analyses_by_user(user_id: int, limit: int = 50):
    with get_db() as db:
        cur = db.execute(
            """
            SELECT id, user_id, image_path, diagnosis_json, diagnosis, created_at
            FROM analyses
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return cur.fetchall()
