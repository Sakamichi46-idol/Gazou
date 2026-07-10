import sqlite3


DB_NAME = "blogs.db"



def init_db():

    with sqlite3.connect(DB_NAME) as conn:

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



def is_notified(url):

    with sqlite3.connect(DB_NAME) as conn:

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


    return result is not None



def save_blog(blog):

    if not blog:
        return


    with sqlite3.connect(DB_NAME) as conn:

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
            (
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                blog.get("url"),
                blog.get("group"),
                blog.get("title"),
                blog.get("date")
            )
        )

        conn.commit()
