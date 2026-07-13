import os
import sqlite3

DB_DIR = "/data"
DB_NAME = "archive.db"

os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, DB_NAME)

print(f"ARCHIVE DB PATH: {DB_PATH}")


# =========================
# DB接続
# =========================

def get_connection():
    return sqlite3.connect(DB_PATH)


# =========================
# 初期化
# =========================

def init_archive_db():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS archive(
            url TEXT PRIMARY KEY,
            group_name TEXT,
            member TEXT,
            title TEXT,
            date TEXT,
            archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================
# 保存済み確認
# =========================

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


# =========================
# 保存
# =========================

def save_archive(blog):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
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
            blog["url"],
            blog["group"],
            blog["member"],
            blog["title"],
            blog["date"]
        )
    )

    conn.commit()
    conn.close()


# =========================
# 未保存だけ返す
# =========================

def filter_not_archived(blogs):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT url FROM archive")

    archived = {
        row[0]
        for row in cur.fetchall()
    }

    conn.close()

    return [
        blog
        for blog in blogs
        if blog["url"] not in archived
    ]


# =========================
# 件数
# =========================

def archive_count():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM archive"
    )

    count = cur.fetchone()[0]

    conn.close()

    return count


# =========================
# 全削除
# =========================

def reset_archive():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM archive"
    )

    conn.commit()
    conn.close()
