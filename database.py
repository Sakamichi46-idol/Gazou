import sqlite3


DB_NAME = "blogs.db"



def init_db():

    conn = sqlite3.connect(
        DB_NAME
    )

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
        "SELECT url FROM blogs WHERE url=?",
        (url,)
    )


    result = cur.fetchone()


    conn.close()


    return result is not None



def save_blog(blog):

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
        (
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            blog["url"],
            blog["group"],
            blog["title"],
            blog["date"]
        )
    )


    conn.commit()

    conn.close()
