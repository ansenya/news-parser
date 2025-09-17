import os
import sqlite3
from contextlib import contextmanager

DB_PATH = "/app/db/news.db" if os.getenv("APP_ENV") == "prod" else "../db/news.db"

CATEGORY_INNER = "внутренняя"
CATEGORY_OUTER = "внешняя"


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)  # Увеличиваем timeout
    conn.execute("PRAGMA journal_mode=WAL")  # Включаем WAL mode для конкурентности
    try:

        yield conn
    finally:
        conn.close()


def save_news(date, text, category):
    with get_db_connection() as conn:
        cur = conn.cursor()
        query = "INSERT OR IGNORE INTO news (date, text, category) VALUES (?, ?, ?)"
        cur.execute(query, (date, text, category))
        conn.commit()


def news_exists(text):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM news WHERE text = ?", (text,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists
