import sqlite3
import os


DB_NAME = "/app/data/blogs.db"



def init_db():

    print("DB PATH:", DB_NAME)
    print("DB EXISTS:", os.path.exists(DB_NAME))

    conn = sqlite3.connect(DB_NAME)

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS blogs (
            url TEXT PRIMARY KEY,
            group_name TEXT,
            title TEXT,
            date TEXT
        )
        """
    )

    conn.commit()
    conn.close()



def is_notified(url):

    conn = sqlite3.connect(
        DB_NAME
    )

    cur = conn.cursor()


    cur.execute(
        """
        SELECT url
        FROM blogs
        WHERE url = ?
        """,
        (url,)
    )


    result = cur.fetchone()


    conn.close()


    return result is not None



def save_blog(blog):

    print(

        "DB保存開始:",

        blog.get("url")

    )

    conn = sqlite3.connect(

        DB_NAME

    )

    cur = conn.cursor()


    cur.execute(
        """
        INSERT OR IGNORE INTO blogs
        (
            url,
            group_name,
            title,
            date
        )
        VALUES
        (?, ?, ?, ?)
        """,
        (
            blog.get("url"),
            blog.get("group"),
            blog.get("title"),
            blog.get("date")
        )
    )


    conn.commit()
    conn.close()
