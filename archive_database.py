import os
import sqlite3

DB_DIR = "data"
DB_NAME = "archive.db"

os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, DB_NAME)

print(f"ARCHIVE DB PATH: {DB_PATH}")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_archive_db():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS archive(
            url TEXT PRIMARY KEY,
            group_name TEXT,
            member TEXT,
            title TEXT,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()


def is_archived(url):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM archive WHERE url=?",
        (url,)
    )

    result = cur.fetchone()

    conn.close()

    return result is not None


def save_archive(group_name, member, title, date, url):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO archive
        (
            url,
            group_name,
            member,
            title,
            date
        )
        VALUES
        (?, ?, ?, ?, ?)
    """,
    (
        url,
        group_name,
        member,
        title,
        date
    ))

    conn.commit()
    conn.close()


def archive_count():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM archive"
    )

    count = cur.fetchone()[0]

    conn.close()

    return count


def get_oldest_not_archived(blogs):
    """
    まだ保存されていない一番古いブログを返す
    """

    for blog in blogs:

        if not is_archived(blog["url"]):
            return blog

    return None
