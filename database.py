import sqlite3
import os
from urllib.parse import urlparse


DB_NAME = "/app/data/blogs.db"



def normalize_url(url):

    if not url:
        return ""

    parsed = urlparse(url)

    return (
        parsed.scheme
        + "://"
        + parsed.netloc
        + parsed.path
    )



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

    url = normalize_url(url)


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
        (
            url,
        )
    )


    result = cur.fetchone()


    conn.close()


    return result is not None



def save_blog(blog):

    url = normalize_url(
        blog.get("url")
    )


    print(
        "DB保存開始:",
        url
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
            url,
            blog.get("group"),
            blog.get("title"),
            blog.get("date")
        )
    )


    conn.commit()

    conn.close()
