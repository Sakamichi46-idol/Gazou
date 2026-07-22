import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Any


# =========================
# データベース設定
# =========================

# RailwayでVolumeを使う場合は /data に保存する。
# ローカル実行などで /data が使えない場合は、
# プロジェクト内の data フォルダへ保存する。
RAILWAY_DATA_DIR = "/data"
LOCAL_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data"
)


def get_data_dir() -> str:
    """
    写真検索用データの保存先を返す。
    Railwayでは /data、ローカルでは ./data を使用する。
    """

    if os.path.isdir(RAILWAY_DATA_DIR):
        return RAILWAY_DATA_DIR

    os.makedirs(
        LOCAL_DATA_DIR,
        exist_ok=True
    )

    return LOCAL_DATA_DIR


DATA_DIR = get_data_dir()

PHOTO_DB_PATH = os.getenv(
    "PHOTO_DB_PATH",
    os.path.join(
        DATA_DIR,
        "photo_archive.db"
    )
)


# =========================
# 共通処理
# =========================

def utc_now_text() -> str:
    """
    現在時刻をUTCのISO形式で返す。
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


def get_connection() -> sqlite3.Connection:
    """
    SQLite接続を作成する。
    """

    connection = sqlite3.connect(
        PHOTO_DB_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        "PRAGMA journal_mode = WAL"
    )

    connection.execute(
        "PRAGMA synchronous = NORMAL"
    )

    return connection


def row_to_dict(
    row: sqlite3.Row | None
) -> dict[str, Any] | None:
    """
    sqlite3.Rowを辞書へ変換する。
    """

    if row is None:
        return None

    return dict(row)


# =========================
# DB初期化
# =========================

def init_photo_db() -> None:
    """
    写真検索用DBと必要なテーブルを作成する。
    """

    os.makedirs(
        os.path.dirname(PHOTO_DB_PATH),
        exist_ok=True
    )

    with closing(
        get_connection()
    ) as connection:

        cursor = connection.cursor()

        # -------------------------
        # ブログ記事
        # -------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photo_blogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                blog_url TEXT NOT NULL UNIQUE,

                group_name TEXT NOT NULL DEFAULT '',
                member_name TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                published_at TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # -------------------------
        # 画像
        # -------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photo_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                blog_id INTEGER NOT NULL,

                image_url TEXT NOT NULL,
                image_index INTEGER NOT NULL DEFAULT 0,

                local_path TEXT NOT NULL DEFAULT '',
                file_name TEXT NOT NULL DEFAULT '',
                mime_type TEXT NOT NULL DEFAULT '',

                file_size INTEGER NOT NULL DEFAULT 0,
                width INTEGER NOT NULL DEFAULT 0,
                height INTEGER NOT NULL DEFAULT 0,

                image_hash TEXT NOT NULL DEFAULT '',

                download_status TEXT NOT NULL DEFAULT 'pending',
                analysis_status TEXT NOT NULL DEFAULT 'pending',

                analysis_error TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                UNIQUE(blog_id, image_url),

                FOREIGN KEY(blog_id)
                    REFERENCES photo_blogs(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------
        # AIタグ
        # -------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photo_ai_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                image_id INTEGER NOT NULL,

                category TEXT NOT NULL DEFAULT '',
                tag TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0,

                model_name TEXT NOT NULL DEFAULT '',
                raw_value TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                UNIQUE(image_id, category, tag),

                FOREIGN KEY(image_id)
                    REFERENCES photo_images(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------
        # 人間が追加・修正したタグ
        # -------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photo_manual_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                image_id INTEGER NOT NULL,

                category TEXT NOT NULL DEFAULT '',
                tag TEXT NOT NULL,

                created_by TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                UNIQUE(image_id, category, tag),

                FOREIGN KEY(image_id)
                    REFERENCES photo_images(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------
        # AIの画像解析結果
        # -------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photo_ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                image_id INTEGER NOT NULL UNIQUE,

                model_name TEXT NOT NULL DEFAULT '',
                raw_response TEXT NOT NULL DEFAULT '',

                person_name TEXT NOT NULL DEFAULT '',
                clothing TEXT NOT NULL DEFAULT '',
                expression TEXT NOT NULL DEFAULT '',
                background TEXT NOT NULL DEFAULT '',
                pose TEXT NOT NULL DEFAULT '',
                objects TEXT NOT NULL DEFAULT '',

                person_count INTEGER NOT NULL DEFAULT 0,

                overall_confidence REAL NOT NULL DEFAULT 0,
                needs_review INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY(image_id)
                    REFERENCES photo_images(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------
        # 人間による確認待ち
        # -------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photo_review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                image_id INTEGER NOT NULL UNIQUE,

                review_type TEXT NOT NULL DEFAULT '',
                question TEXT NOT NULL DEFAULT '',
                candidates TEXT NOT NULL DEFAULT '',

                status TEXT NOT NULL DEFAULT 'pending',

                reviewed_by TEXT NOT NULL DEFAULT '',
                selected_value TEXT NOT NULL DEFAULT '',
                review_note TEXT NOT NULL DEFAULT '',

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                reviewed_at TEXT NOT NULL DEFAULT '',

                FOREIGN KEY(image_id)
                    REFERENCES photo_images(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------
        # お気に入り
        # -------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photo_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                image_id INTEGER NOT NULL,
                discord_user_id TEXT NOT NULL,

                created_at TEXT NOT NULL,

                UNIQUE(image_id, discord_user_id),

                FOREIGN KEY(image_id)
                    REFERENCES photo_images(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------
        # 検索高速化用インデックス
        # -------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_photo_blogs_group
            ON photo_blogs(group_name)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_photo_blogs_member
            ON photo_blogs(member_name)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_photo_blogs_published
            ON photo_blogs(published_at)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_photo_images_blog
            ON photo_images(blog_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_photo_images_analysis_status
            ON photo_images(analysis_status)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_photo_ai_tags_tag
            ON photo_ai_tags(tag)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_photo_manual_tags_tag
            ON photo_manual_tags(tag)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_photo_review_status
            ON photo_review_queue(status)
            """
        )

        connection.commit()

    print(
        "写真検索DB初期化完了:",
        PHOTO_DB_PATH
    )


# =========================
# ブログ登録
# =========================

def save_photo_blog(
    blog: dict[str, Any]
) -> int:
    """
    ブログ記事を登録または更新し、
    photo_blogs.idを返す。
    """

    blog_url = str(
        blog.get("url", "")
    ).strip()

    if not blog_url:
        raise ValueError(
            "ブログURLが空です。"
        )

    group_name = str(
        blog.get("group", "")
    ).strip()

    member_name = str(
        blog.get("member", "")
    ).strip()

    title = str(
        blog.get("title", "")
    ).strip()

    published_at = str(
        blog.get("date", "")
    ).strip()

    now = utc_now_text()

    with closing(
        get_connection()
    ) as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO photo_blogs (
                blog_url,
                group_name,
                member_name,
                title,
                published_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(blog_url)
            DO UPDATE SET
                group_name = excluded.group_name,
                member_name = excluded.member_name,
                title = excluded.title,
                published_at = excluded.published_at,
                updated_at = excluded.updated_at
            """,
            (
                blog_url,
                group_name,
                member_name,
                title,
                published_at,
                now,
                now,
            )
        )

        cursor.execute(
            """
            SELECT id
            FROM photo_blogs
            WHERE blog_url = ?
            """,
            (
                blog_url,
            )
        )

        row = cursor.fetchone()

        connection.commit()

    if row is None:
        raise RuntimeError(
            "ブログ情報の保存に失敗しました。"
        )

    return int(
        row["id"]
    )


def get_photo_blog_by_url(
    blog_url: str
) -> dict[str, Any] | None:
    """
    URLからブログ情報を取得する。
    """

    with closing(
        get_connection()
    ) as connection:

        cursor = connection.execute(
            """
            SELECT *
            FROM photo_blogs
            WHERE blog_url = ?
            """,
            (
                blog_url,
            )
        )

        return row_to_dict(
            cursor.fetchone()
        )


# =========================
# 画像登録
# =========================

def save_photo_image(
    blog_id: int,
    image_url: str,
    image_index: int = 0,
    local_path: str = "",
    file_name: str = "",
    mime_type: str = "",
    file_size: int = 0,
    width: int = 0,
    height: int = 0,
    image_hash: str = "",
    download_status: str = "pending",
) -> int:
    """
    ブログ画像を登録または更新し、
    photo_images.idを返す。
    """

    image_url = str(
        image_url
    ).strip()

    if not image_url:
        raise ValueError(
            "画像URLが空です。"
        )

    now = utc_now_text()

    with closing(
        get_connection()
    ) as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO photo_images (
                blog_id,
                image_url,
                image_index,
                local_path,
                file_name,
                mime_type,
                file_size,
                width,
                height,
                image_hash,
                download_status,
                analysis_status,
                analysis_error,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                'pending',
                '',
                ?, ?
            )

            ON CONFLICT(blog_id, image_url)
            DO UPDATE SET
                image_index = excluded.image_index,
                local_path = excluded.local_path,
                file_name = excluded.file_name,
                mime_type = excluded.mime_type,
                file_size = excluded.file_size,
                width = excluded.width,
                height = excluded.height,
                image_hash = excluded.image_hash,
                download_status = excluded.download_status,
                updated_at = excluded.updated_at
            """,
            (
                blog_id,
                image_url,
                image_index,
                local_path,
                file_name,
                mime_type,
                file_size,
                width,
                height,
                image_hash,
                download_status,
                now,
                now,
            )
        )

        cursor.execute(
            """
            SELECT id
            FROM photo_images
            WHERE blog_id = ?
            AND image_url = ?
            """,
            (
                blog_id,
                image_url,
            )
        )

        row = cursor.fetchone()

        connection.commit()

    if row is None:
        raise RuntimeError(
            "画像情報の保存に失敗しました。"
        )

    return int(
        row["id"]
    )


def get_photo_image(
    image_id: int
) -> dict[str, Any] | None:
    """
    画像IDから画像情報を取得する。
    """

    with closing(
        get_connection()
    ) as connection:

        cursor = connection.execute(
            """
            SELECT
                photo_images.*,
                photo_blogs.blog_url,
                photo_blogs.group_name,
                photo_blogs.member_name,
                photo_blogs.title,
                photo_blogs.published_at

            FROM photo_images

            INNER JOIN photo_blogs
                ON photo_images.blog_id = photo_blogs.id

            WHERE photo_images.id = ?
            """,
            (
                image_id,
            )
        )

        return row_to_dict(
            cursor.fetchone()
        )


# =========================
# 画像状態更新
# =========================

def update_image_download(
    image_id: int,
    *,
    local_path: str,
    file_name: str,
    mime_type: str,
    file_size: int,
    width: int,
    height: int,
    image_hash: str,
    status: str = "completed",
) -> None:
    """
    画像ダウンロード後の情報を更新する。
    """

    with closing(
        get_connection()
    ) as connection:

        connection.execute(
            """
            UPDATE photo_images

            SET
                local_path = ?,
                file_name = ?,
                mime_type = ?,
                file_size = ?,
                width = ?,
                height = ?,
                image_hash = ?,
                download_status = ?,
                updated_at = ?

            WHERE id = ?
            """,
            (
                local_path,
                file_name,
                mime_type,
                file_size,
                width,
                height,
                image_hash,
                status,
                utc_now_text(),
                image_id,
            )
        )

        connection.commit()


def update_image_analysis_status(
    image_id: int,
    status: str,
    error_message: str = "",
) -> None:
    """
    AI解析状態を更新する。
    """

    with closing(
        get_connection()
    ) as connection:

        connection.execute(
            """
            UPDATE photo_images

            SET
                analysis_status = ?,
                analysis_error = ?,
                updated_at = ?

            WHERE id = ?
            """,
            (
                status,
                error_message,
                utc_now_text(),
                image_id,
            )
        )

        connection.commit()


# =========================
# AIタグ
# =========================

def save_ai_tag(
    image_id: int,
    tag: str,
    confidence: float,
    category: str = "",
    model_name: str = "",
    raw_value: str = "",
) -> None:
    """
    AIが判定したタグを保存する。
    """

    tag = str(
        tag
    ).strip()

    if not tag:
        return

    confidence = max(
        0.0,
        min(
            float(confidence),
            1.0
        )
    )

    now = utc_now_text()

    with closing(
        get_connection()
    ) as connection:

        connection.execute(
            """
            INSERT INTO photo_ai_tags (
                image_id,
                category,
                tag,
                confidence,
                model_name,
                raw_value,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(image_id, category, tag)
            DO UPDATE SET
                confidence = excluded.confidence,
                model_name = excluded.model_name,
                raw_value = excluded.raw_value,
                updated_at = excluded.updated_at
            """,
            (
                image_id,
                category,
                tag,
                confidence,
                model_name,
                raw_value,
                now,
                now,
            )
        )

        connection.commit()


# =========================
# 人間タグ
# =========================

def save_manual_tag(
    image_id: int,
    tag: str,
    category: str = "",
    created_by: str = "",
    note: str = "",
) -> None:
    """
    人間が設定したタグを保存する。
    """

    tag = str(
        tag
    ).strip()

    if not tag:
        return

    now = utc_now_text()

    with closing(
        get_connection()
    ) as connection:

        connection.execute(
            """
            INSERT INTO photo_manual_tags (
                image_id,
                category,
                tag,
                created_by,
                note,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(image_id, category, tag)
            DO UPDATE SET
                created_by = excluded.created_by,
                note = excluded.note,
                updated_at = excluded.updated_at
            """,
            (
                image_id,
                category,
                tag,
                created_by,
                note,
                now,
                now,
            )
        )

        connection.commit()


# =========================
# 確認待ち
# =========================

def add_review_item(
    image_id: int,
    review_type: str,
    question: str,
    candidates: str = "",
) -> None:
    """
    人間による確認待ち画像を登録する。

    candidatesはJSON文字列などで保存できる。
    """

    now = utc_now_text()

    with closing(
        get_connection()
    ) as connection:

        connection.execute(
            """
            INSERT INTO photo_review_queue (
                image_id,
                review_type,
                question,
                candidates,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 'pending', ?, ?)

            ON CONFLICT(image_id)
            DO UPDATE SET
                review_type = excluded.review_type,
                question = excluded.question,
                candidates = excluded.candidates,
                status = 'pending',
                updated_at = excluded.updated_at
            """,
            (
                image_id,
                review_type,
                question,
                candidates,
                now,
                now,
            )
        )

        connection.commit()


def complete_review_item(
    image_id: int,
    selected_value: str,
    reviewed_by: str = "",
    review_note: str = "",
) -> None:
    """
    人間による判定を完了状態にする。
    """

    now = utc_now_text()

    with closing(
        get_connection()
    ) as connection:

        connection.execute(
            """
            UPDATE photo_review_queue

            SET
                status = 'completed',
                selected_value = ?,
                reviewed_by = ?,
                review_note = ?,
                reviewed_at = ?,
                updated_at = ?

            WHERE image_id = ?
            """,
            (
                selected_value,
                reviewed_by,
                review_note,
                now,
                now,
                image_id,
            )
        )

        connection.commit()


# =========================
# 件数確認
# =========================

def get_photo_db_counts() -> dict[str, int]:
    """
    写真検索DB内の件数を返す。
    """

    table_names = {
        "blogs": "photo_blogs",
        "images": "photo_images",
        "ai_tags": "photo_ai_tags",
        "manual_tags": "photo_manual_tags",
        "pending_reviews": "photo_review_queue",
        "favorites": "photo_favorites",
    }

    counts: dict[str, int] = {}

    with closing(
        get_connection()
    ) as connection:

        for key, table_name in table_names.items():

            if key == "pending_reviews":

                cursor = connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM photo_review_queue
                    WHERE status = 'pending'
                    """
                )

            else:

                cursor = connection.execute(
                    f"""
                    SELECT COUNT(*) AS count
                    FROM {table_name}
                    """
                )

            row = cursor.fetchone()

            counts[key] = (
                int(row["count"])
                if row
                else 0
            )

    return counts

# =========================
# 画像保存状況
# =========================

def get_photo_storage_stats() -> dict[str, int]:
    """
    画像ファイルの保存状況を返す。

    completed:
        ダウンロード完了件数

    pending:
        未ダウンロード件数

    failed:
        ダウンロード失敗件数

    total_size:
        保存済み画像の合計容量（bytes）
    """

    with closing(
        get_connection()
    ) as connection:

        cursor = connection.execute(
            """
            SELECT
                COUNT(*) AS total_images,

                SUM(
                    CASE
                        WHEN download_status = 'completed'
                        THEN 1
                        ELSE 0
                    END
                ) AS completed,

                SUM(
                    CASE
                        WHEN download_status = 'pending'
                        THEN 1
                        ELSE 0
                    END
                ) AS pending,

                SUM(
                    CASE
                        WHEN download_status = 'failed'
                        THEN 1
                        ELSE 0
                    END
                ) AS failed,

                SUM(
                    CASE
                        WHEN download_status = 'completed'
                        THEN file_size
                        ELSE 0
                    END
                ) AS total_size

            FROM photo_images
            """
        )

        row = cursor.fetchone()

    if row is None:

        return {
            "total_images": 0,
            "completed": 0,
            "pending": 0,
            "failed": 0,
            "total_size": 0,
        }

    return {
        "total_images": int(
            row["total_images"] or 0
        ),
        "completed": int(
            row["completed"] or 0
        ),
        "pending": int(
            row["pending"] or 0
        ),
        "failed": int(
            row["failed"] or 0
        ),
        "total_size": int(
            row["total_size"] or 0
        ),
    }


# =========================
# 単体実行テスト
# =========================

if __name__ == "__main__":

    init_photo_db()

    counts = get_photo_db_counts()

    print("=" * 40)
    print("写真検索DB状態")
    print(f"ブログ: {counts['blogs']}件")
    print(f"画像: {counts['images']}件")
    print(f"AIタグ: {counts['ai_tags']}件")
    print(f"手動タグ: {counts['manual_tags']}件")
    print(
        f"確認待ち: "
        f"{counts['pending_reviews']}件"
    )
    print(
        f"お気に入り: "
        f"{counts['favorites']}件"
    )
    print("=" * 40)
