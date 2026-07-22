import os
import io
import tempfile
import asyncio
from urllib.parse import urlparse

import aiohttp
import discord
import imageio_ffmpeg


# =========================
# 基本設定
# =========================

DOWNLOAD_TIMEOUT = 60

# Discord側の上限ギリギリではなく、
# 少し余裕を持たせる
UPLOAD_SAFETY_MARGIN = 512 * 1024


# =========================
# 補助関数
# =========================

def format_file_size(size_bytes):

    return (
        f"{size_bytes / (1024 * 1024):.2f} MB"
    )


def is_gif_data(
    data,
    content_type,
    url
):

    content_type = (
        content_type
        or ""
    ).lower()

    url_path = urlparse(
        url
    ).path.lower()

    # Content-Typeで判定
    if "image/gif" in content_type:

        return True

    # URL末尾で判定
    if url_path.endswith(".gif"):

        return True

    # GIF本体の先頭データで判定
    if data.startswith(b"GIF87a"):

        return True

    if data.startswith(b"GIF89a"):

        return True

    return False


def get_normal_extension(
    content_type,
    url
):

    content_type = (
        content_type
        or ""
    ).lower()

    url_path = urlparse(
        url
    ).path.lower()

    if "image/png" in content_type:
        return ".png"

    if "image/webp" in content_type:
        return ".webp"

    if "image/jpeg" in content_type:
        return ".jpg"

    if "image/jpg" in content_type:
        return ".jpg"

    if url_path.endswith(".png"):
        return ".png"

    if url_path.endswith(".webp"):
        return ".webp"

    if (
        url_path.endswith(".jpeg")
        or url_path.endswith(".jpg")
    ):
        return ".jpg"

    return ".jpg"


# =========================
# FFmpeg実行
# =========================

async def run_ffmpeg(
    input_path,
    output_path,
    compressed=False
):

    ffmpeg_exe = (
        imageio_ffmpeg.get_ffmpeg_exe()
    )

    command = [
        ffmpeg_exe,
        "-y",
        "-loglevel",
        "error",
        "-i",
        input_path,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
    ]

    if compressed:

        # 1回目でまだ大きすぎた場合の
        # 強めの圧縮
        command.extend([
            "-vf",
            (
                "scale="
                "'min(1280,iw)':"
                "-2"
            ),
            "-crf",
            "30",
        ])

    else:

        # 幅・高さが奇数の場合にも
        # H.264で保存できるよう偶数化
        command.extend([
            "-vf",
            (
                "scale="
                "trunc(iw/2)*2:"
                "trunc(ih/2)*2"
            ),
            "-crf",
            "24",
        ])

    command.extend([
        "-movflags",
        "+faststart",
        output_path,
    ])

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:

        error_text = stderr.decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"FFmpeg変換失敗: {error_text}"
        )


# =========================
# GIF → MP4
# =========================

async def convert_gif_to_mp4(
    gif_data,
    index,
    max_bytes
):

    with tempfile.TemporaryDirectory() as temp_dir:

        input_path = os.path.join(
            temp_dir,
            f"input_{index}.gif"
        )

        output_path = os.path.join(
            temp_dir,
            f"output_{index}.mp4"
        )

        with open(
            input_path,
            "wb"
        ) as file:

            file.write(
                gif_data
            )

        # ---------------------
        # 通常変換
        # ---------------------

        await run_ffmpeg(
            input_path,
            output_path,
            compressed=False
        )

        with open(
            output_path,
            "rb"
        ) as file:

            mp4_data = file.read()

        print(
            f"GIF→MP4変換完了: "
            f"{format_file_size(len(gif_data))}"
            f" → "
            f"{format_file_size(len(mp4_data))}"
        )

        if len(mp4_data) <= max_bytes:

            return mp4_data

        # ---------------------
        # 強めの再圧縮
        # ---------------------

        print(
            "MP4がまだ大きいため、"
            "解像度を下げて再変換します。"
        )

        await run_ffmpeg(
            input_path,
            output_path,
            compressed=True
        )

        with open(
            output_path,
            "rb"
        ) as file:

            mp4_data = file.read()

        print(
            f"GIF→MP4再圧縮完了: "
            f"{format_file_size(len(mp4_data))}"
        )

        if len(mp4_data) <= max_bytes:

            return mp4_data

        return None


# =========================
# 添付ファイル取得
# =========================

async def download_attachment(
    session,
    url,
    index,
    upload_limit
):

    try:

        timeout = aiohttp.ClientTimeout(
            total=DOWNLOAD_TIMEOUT
        )

        async with session.get(
            url,
            timeout=timeout
        ) as response:

            if response.status != 200:

                print(
                    f"画像取得失敗: "
                    f"status={response.status} "
                    f"url={url}"
                )

                return None

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            data = await response.read()

        original_size = len(
            data
        )

        print(
            f"画像{index}: "
            f"{format_file_size(original_size)} "
            f"/ {content_type}"
        )

        max_bytes = max(
            upload_limit
            - UPLOAD_SAFETY_MARGIN,
            1 * 1024 * 1024
        )

        # =====================
        # GIFの場合
        # =====================

        if is_gif_data(
            data,
            content_type,
            url
        ):

            print(
                f"GIFを検出しました: "
                f"画像{index}"
            )

            mp4_data = await convert_gif_to_mp4(
                data,
                index,
                max_bytes
            )

            if mp4_data is None:

                print(
                    f"MP4変換後も容量超過: "
                    f"画像{index}"
                )

                return {
                    "file": None,
                    "size": 0,
                    "url": url,
                    "reason": (
                        "GIFをMP4へ変換しましたが、"
                        "容量上限を超えました。"
                    )
                }

            return {
                "file": discord.File(
                    io.BytesIO(
                        mp4_data
                    ),
                    filename=(
                        f"image_{index}.mp4"
                    )
                ),
                "size": len(
                    mp4_data
                ),
                "url": url,
                "reason": "",
            }

        # =====================
        # 通常画像の場合
        # =====================

        if original_size > max_bytes:

            print(
                f"画像容量超過: "
                f"{format_file_size(original_size)}"
            )

            return {
                "file": None,
                "size": 0,
                "url": url,
                "reason": (
                    "画像容量がDiscordの"
                    "アップロード上限を超えました。"
                )
            }

        extension = get_normal_extension(
            content_type,
            url
        )

        return {
            "file": discord.File(
                io.BytesIO(
                    data
                ),
                filename=(
                    f"image_{index}"
                    f"{extension}"
                )
            ),
            "size": original_size,
            "url": url,
            "reason": "",
        }

    except Exception as e:

        print(
            f"画像取得・変換エラー "
            f"画像{index}:",
            e
        )

        return {
            "file": None,
            "size": 0,
            "url": url,
            "reason": (
                f"画像の取得または変換に"
                f"失敗しました: {e}"
            )
        }
