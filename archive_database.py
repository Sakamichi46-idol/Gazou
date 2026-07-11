import os
import sqlite3


# =========================
# DB設定
# =========================

DB_DIR = "data"

DB_NAME = "archive.db"


os.makedirs(
    DB_DIR,
    exist_ok=True
)


DB_PATH = os.path.join(
    DB_DIR,
    DB_NAME
)


print(
    f"ARCHIVE DB PATH: {DB_PATH}"
)





# =========================
# DB初期化
# =========================

def init_archive_db():

    conn = sqlite3.connect(
        DB_PATH
    )

    cur = conn.cursor()


    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS archive (

            url TEXT PRIMARY KEY,

            group_name TEXT,

            member TEXT,

            title TEXT,

            date TEXT

        )
        """
    )


    conn.commit()

    conn.close()





# =========================
# 登録済み確認
# =========================

def is_archived(
    url
):

    conn = sqlite3.connect(
        DB_PATH
    )

    cur = conn.cursor()


    cur.execute(
        """
        SELECT 1
        FROM archive
        WHERE url = ?
        """,
        (
            url,
        )
    )


    result = cur.fetchone()


    conn.close()


    return result is not None





# =========================
# 保存
# =========================

def save_archive(
    group_name,
    member,
    title,
    date,
    url
):

    conn = sqlite3.connect(
        DB_PATH
    )

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
            url,
            group_name,
            member,
            title,
            date
        )
    )


    conn.commit()

    conn.close()





# =========================
# archive_main.py用
# =========================

def mark_archived(
    blog
):

    save_archive(

        blog.get(
            "group",
            ""
        ),

        blog.get(
            "member",
            ""
        ),

        blog.get(
            "title",
            ""
        ),

        blog.get(
            "date",
            ""
        ),

        blog.get(
            "url",
            ""
        )

    )





# =========================
# 件数確認
# =========================

def archive_count():

    conn = sqlite3.connect(
        DB_PATH
    )

    cur = conn.cursor()


    cur.execute(
        """
        SELECT COUNT(*)
        FROM archive
        """
    )


    count = cur.fetchone()[0]


    conn.close()


    return count
