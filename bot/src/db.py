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


def init_db():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS news
            (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     DATE DEFAULT (date('now')),
                text     TEXT UNIQUE,
                category TEXT 
            );
        """)
        conn.commit()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS summaries
            (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                year     INTEGER NOT NULL,
                week     INTEGER NOT NULL,
                text     TEXT,
                category TEXT,               
                UNIQUE (year, week, category)
            );
        """)
        conn.commit()


def get_news_by_week(year=None, week=None, category=None):
    """
    Получить новости за указанную неделю или текущую неделю

    Args:
        year: год (если None - используется текущая неделя)
        week: номер недели (если None - используется текущая неделя)
        category: категория новостей (внутренняя/внешняя), если None - все категории

    Returns:
        Список новостей за указанный период
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    params = []
    where_clauses = []

    if year is not None and week is not None:
        # Конкретная неделя
        where_clauses.append("strftime('%Y', date) = ?")
        where_clauses.append("strftime('%W', date) = ?")
        params.extend([str(year), str(week).zfill(2)])
    else:
        # Прошедшая неделя
        where_clauses.append("strftime('%Y-%W', date) = strftime('%Y-%W', 'now', '-7 days')")

    if category:
        where_clauses.append("category = ?")
        params.append(category)

    query = f"""
        SELECT date, text, category 
        FROM news 
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
        ORDER BY date DESC
    """

    rows = cur.execute(query, params).fetchall()
    conn.close()
    return rows


def get_summary_by_week(year=None, week=None, category=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if year is None or week is None:
        # Если не указаны год и неделя, используем предыдущую неделю
        prev_week_info = cur.execute("""
            SELECT 
                strftime('%Y', 'now', '-7 days') as year,
                strftime('%W', 'now', '-7 days') as week
        """).fetchone()
        year, week = int(prev_week_info[0]), int(prev_week_info[1])

    if category:
        query = """
            SELECT year, week, text, category 
            FROM summaries 
            WHERE year = ? AND week = ? AND category = ?
        """
        rows = cur.execute(query, (year, week, category)).fetchall()
    else:
        query = """
            SELECT year, week, text, category 
            FROM summaries 
            WHERE year = ? AND week = ?
            ORDER BY category
        """
        rows = cur.execute(query, (year, week)).fetchall()

    conn.close()
    return rows


def save_news(date, text, category):
    with get_db_connection() as conn:
        cur = conn.cursor()
        query = "INSERT INTO news (date, text, category) VALUES (?, ?, ?)"
        cur.execute(query, (date, text, category))
        conn.commit()
