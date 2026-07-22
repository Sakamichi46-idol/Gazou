import hashlib
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp
from PIL import Image

from photo_database import (
    update_image_download,
)


# =========================
# 保存先設定
# =========================

RAILWAY_DATA_DIR = "/data"

LOCAL_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
)

REQUEST_TIMEOUT = 60

MAX_FILE_SIZE = 50 * 1024 * 1024


def get_data_dir() -> str:
    """
    Railwayでは /data、
    ローカルではプロジェクト内の data を使う。
    """

    if os.path.isdir(RAILWAY_DATA_DIR):
        return RAILWAY_DATA_DIR

    os.makedirs(
        LOCAL_DATA_DIR,
        exist_ok=True,
    )

    return LOCAL_DATA_DIR


DATA_DIR = get_data_dir()

PHOTO_IMAGE_DIR = os.getenv(
    "PHOTO_IMAGE_DIR",
    os.path.join(
        DATA_DIR,
        "photo_images",
    ),
)


# =========================
# 文字列整理
# =========================

def sanitize_name(
    value: str,
    default: str = "unknown",
) -> str:
    """
    フォルダ名やファイル名に使えない文字を除去する。
    """

    value = str(
        value or ""
    ).strip()

    if not value:
        return default

    value = re.sub(
        r'[\\/:*?"<>|]',
        "_",
        value,
    )

    value = re.sub(
        r"\s+",
        "_",
        value,
    )

    value = value.strip(
        "._ "
    )

    if not value:
        return default

    return value[:100]


def get_extension_from_content_type(
    content_type: str,
) -> str:
    """
    Content-Typeから拡張子を決める。
    """

    content_type = (
        content_type
        .split(";")[0]
        .strip()
        .lower()
    )

    extension_map = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
        "image/avif": ".avif",
    }

    return extension_map.get(
        content_type,
        "",
    )


def get_extension_from_url(
    image_url: str,
) -> str:
    """
    URLから画像拡張子を取得する。
    """

    parsed = urlparse(
        image_url
    )

    path = parsed.path.lower()

    extension = os.path.splitext(
        path
    )[1]

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
        ".avif",
    }

    if extension not in allowed_extensions:
        return ""

    if extension == ".jpeg":
        return ".jpg"

    if extension == ".tif":
        return ".tiff"

    return extension


def build_image_path(
    *,
    group_name: str,
    member_name: str,
    published_at: str,
    blog_id: int,
    image_index: int,
    extension: str,
) -> str:
    """
    保存先パスを作成する。

    例:
    /data/photo_images/乃木坂46/井上和/2026/07/blog_123/001.jpg
    """

    group_folder = sanitize_name(
        group_name,
        "unknown_group",
    )

    member_folder = sanitize_name(
        member_name,
        "unknown_member",
    )

    year = "unknown_year"
    month = "unknown_month"

    date_match = re.search(
        r"(\d{4})[./\-年](\d{1,2})",
        str(published_at or ""),
    )

    if date_match:
        year = date_match.group(1)
        month = date_match.group(2).zfill(2)

    blog_folder = f"blog_{blog_id}"

    file_name = (
        f"{int(image_index):03d}"
        f"{extension}"
    )

    folder_path = os.path.join(
        PHOTO_IMAGE_DIR,
        group_folder,
        member_folder,
        year,
        month,
        blog_folder,
    )

    os.makedirs(
        folder_path,
        exist_ok=True,
    )

    return os.path.join(
        folder_path,
        file_name,
    )


# =========================
# 画像情報取得
# =========================

def calculate_sha256(
    content: bytes,
) -> str:
    """
    画像データのSHA-256を返す。
    """

    return hashlib.sha256(
        content
    ).hexdigest()


def get_image_dimensions(
    file_path: str,
) -> tuple[int, int]:
    """
    Pillowで画像の幅と高さを取得する。
    取得できない形式の場合は0を返す。
    """

    try:

        with Image.open(
            file_path
        ) as image:

            width, height = image.size

            return (
                int(width),
                int(height),
            )

    except Exception as error:

        print(
            "画像サイズ取得エラー:",
            file_path,
            error,
        )

        return (
            0,
            0,
        )


# =========================
# ダウンロード本体
# =========================

async def download_photo_image(
    session: aiohttp.ClientSession,
    *,
    image_id: int,
    blog_id: int,
    image_url: str,
    image_index: int,
    group_name: str,
    member_name: str,
    published_at: str,
) -> dict[str, Any]:
    """
    画像をダウンロードし、Volumeへ保存する。
    保存後にphoto_imagesテーブルを更新する。
    """

    image_url = str(
        image_url or ""
    ).strip()

    if not image_url:

        return {
            "success": False,
            "image_id": image_id,
            "error": "画像URLが空です。",
        }

    timeout = aiohttp.ClientTimeout(
        total=REQUEST_TIMEOUT
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Referer": image_url,
    }

    try:

        async with session.get(
            image_url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        ) as response:

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type",
                "",
            )

            if (
                content_type
                and not content_type.lower().startswith(
                    "image/"
                )
            ):

                raise ValueError(
                    "画像ではないContent-Typeです: "
                    f"{content_type}"
                )

            content_length = response.headers.get(
                "Content-Length"
            )

            if content_length:

                declared_size = int(
                    content_length
                )

                if declared_size > MAX_FILE_SIZE:

                    raise ValueError(
                        "画像サイズが上限を超えています: "
                        f"{declared_size} bytes"
                    )

            content = await response.read()

    except Exception as error:

        print(
            "写真画像ダウンロードエラー:",
            image_url,
            error,
        )

        return {
            "success": False,
            "image_id": image_id,
            "error": str(error),
        }

    if not content:

        return {
            "success": False,
            "image_id": image_id,
            "error": "画像データが空です。",
        }

    if len(content) > MAX_FILE_SIZE:

        return {
            "success": False,
            "image_id": image_id,
            "error": (
                "画像サイズが上限を超えています: "
                f"{len(content)} bytes"
            ),
        }

    extension = get_extension_from_content_type(
        content_type
    )

    if not extension:

        extension = get_extension_from_url(
            image_url
        )

    if not extension:
        extension = ".jpg"

    file_path = build_image_path(
        group_name=group_name,
        member_name=member_name,
        published_at=published_at,
        blog_id=blog_id,
        image_index=image_index,
        extension=extension,
    )

    temporary_path = (
        file_path
        + ".part"
    )

    try:

        with open(
            temporary_path,
            "wb",
        ) as file:

            file.write(
                content
            )

        os.replace(
            temporary_path,
            file_path,
        )

    except Exception as error:

        if os.path.exists(
            temporary_path
        ):

            try:
                os.remove(
                    temporary_path
                )

            except OSError:
                pass

        print(
            "写真画像保存エラー:",
            file_path,
            error,
        )

        return {
            "success": False,
            "image_id": image_id,
            "error": str(error),
        }

    width, height = get_image_dimensions(
        file_path
    )

    image_hash = calculate_sha256(
        content
    )

    file_size = len(
        content
    )

    file_name = os.path.basename(
        file_path
    )

    try:

        update_image_download(
            image_id,
            local_path=file_path,
            file_name=file_name,
            mime_type=content_type,
            file_size=file_size,
            width=width,
            height=height,
            image_hash=image_hash,
            status="completed",
        )

    except Exception as error:

        print(
            "写真画像DB更新エラー:",
            image_id,
            error,
        )

        return {
            "success": False,
            "image_id": image_id,
            "file_path": file_path,
            "error": str(error),
        }

    print(
        "写真画像保存完了:",
        image_id,
        file_path,
    )

    return {
        "success": True,
        "image_id": image_id,
        "file_path": file_path,
        "file_name": file_name,
        "file_size": file_size,
        "width": width,
        "height": height,
        "image_hash": image_hash,
    }


async def download_blog_images(
    session: aiohttp.ClientSession,
    *,
    blog_id: int,
    blog: dict[str, Any],
    image_records: list[dict[str, Any]],
) -> dict[str, int]:
    """
    ブログ1件分の画像を順番に保存する。
    """

    success_count = 0
    failed_count = 0

    group_name = str(
        blog.get("group", "")
    )

    member_name = str(
        blog.get("member", "")
    )

    published_at = str(
        blog.get("date", "")
    )

    for image_record in image_records:

        result = await download_photo_image(
            session,
            image_id=int(
                image_record["image_id"]
            ),
            blog_id=blog_id,
            image_url=str(
                image_record["image_url"]
            ),
            image_index=int(
                image_record["image_index"]
            ),
            group_name=group_name,
            member_name=member_name,
            published_at=published_at,
        )

        if result.get("success"):

            success_count += 1

        else:

            failed_count += 1

        await asyncio_sleep()

    return {
        "success": success_count,
        "failed": failed_count,
    }


async def asyncio_sleep() -> None:
    """
    連続アクセスを少し抑える。
    """

    import asyncio

    await asyncio.sleep(
        0.2
    )


# =========================
# 保存先確認
# =========================

def get_photo_storage_path() -> str:
    """
    画像保存先を返す。
    """

    os.makedirs(
        PHOTO_IMAGE_DIR,
        exist_ok=True,
    )

    return PHOTO_IMAGE_DIR


if __name__ == "__main__":

    path = get_photo_storage_path()

    print(
        "写真画像保存先:",
        path,
    )
