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
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start DATE NOT NULL,
                text       TEXT,
                category   TEXT,
                UNIQUE (week_start, category)
            );
        """)
        conn.commit()


def get_news_by_week(date=None, category=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    params = []
    where_clauses = []

    if date is not None:
        # Конкретная неделя
        where_clauses.append("strftime('%Y-%W', date) = strftime('%Y-%W', ?)")
        params.extend(date)
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


def get_summary_by_week(date=None, category=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if date is None:
        # Если не указаны год и неделя, используем предыдущую неделю
        prev_week_info = cur.execute("""
            SELECT strftime('%Y-%m-%d', 'now', '-7 days')
        """).fetchone()
        date = str(prev_week_info[0])

    if category:
        query = """
            SELECT week_start, text, category 
            FROM summaries 
            WHERE strftime('%Y-%W', week_start) = strftime('%Y-%W', ?) AND category = ?
        """
        rows = cur.execute(query, (date, category)).fetchall()
    else:
        query = """
            SELECT week_start, text, category 
            FROM summaries 
            WHERE strftime('%Y-%W', week_start) = strftime('%Y-%W', ?)
            ORDER BY category
        """
        rows = cur.execute(query, (date,)).fetchall()

    conn.close()
    return rows


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


def get_news_count_by_weekday(date):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = """
       SELECT CASE strftime('%w', date)
           WHEN '0' THEN 'Воскресенье'
           WHEN '1' THEN 'Понедельник'
           WHEN '2' THEN 'Вторник'
           WHEN '3' THEN 'Среда'
           WHEN '4' THEN 'Четверг'
           WHEN '5' THEN 'Пятница'
           WHEN '6' THEN 'Суббота'
           END  AS day_of_week,
       COUNT(*) AS news_count
    FROM news
    where strftime('%W', date) = strftime('%W', (?))
    GROUP BY strftime('%w', date)
    ORDER BY strftime('%w', date);
    """
    rows = cur.execute(query, date).fetchall()
    conn.close()

    return rows
