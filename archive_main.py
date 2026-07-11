import os
import asyncio
import io

import aiohttp
import discord
from discord.ext import commands, tasks


from archive_checker import (
    get_archive_targets
)


from archive_database import (
    init_archive_db,
    save_archive
)

from archive_image_getter import (
    get_images
)

from archive_config import (
    ARCHIVE_INTERVAL,
    SEND_DELAY
)


# =========================
# Discord設定
# =========================

TOKEN = os.getenv(
    "DISCORD_TOKEN"
)


# 💡 【カスタム】メッセージ内容の取得権限を追加し、警告を消しました
intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)




# =========================
# チャンネル設定
# =========================

# 全記事を保存するアーカイブチャンネル
ARCHIVE_ALL_CHANNEL = 1524064741016862883




# メンバー別アーカイブチャンネル
ARCHIVE_MEMBER_CHANNELS = {
    # 例
    # "遠藤さくら": 123456789012345678,
}




# =========================
# 画像取得
# =========================

async def download_image(
    url
):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=20
            ) as response:

                data = await response.read()

                return discord.File(
                    io.BytesIO(data),
                    filename="image.jpg"
                )

    except Exception as e:
        print(
            "画像ダウンロードエラー:",
            e
        )
        return None





async def create_files(
    image_urls
):
    files = []

    for url in image_urls[:5]:
        file = await download_image(
            url
        )

        if file:
            files.append(
                file
            )

    return files





# =========================
# 投稿先取得
# =========================

def get_channels(
    member
):
    channels = []

    # 全体アーカイブ
    if ARCHIVE_ALL_CHANNEL:
        channel = bot.get_channel(
            ARCHIVE_ALL_CHANNEL
        )

        if channel:
            channels.append(
                channel
            )

    # メンバー別
    member_channel_id = (
        ARCHIVE_MEMBER_CHANNELS.get(
            member
        )
    )

    if member_channel_id:
        channel = bot.get_channel(
            member_channel_id
        )

        if channel:
            channels.append(
                channel
            )

    return channels





# =========================
# 起動
# =========================

@bot.event
async def on_ready():
    print(
        f"ログイン成功: {bot.user}"
    )

    # archive.db作成
    init_archive_db()

    if not archive_loop.is_running():
        archive_loop.start()





# =========================
# アーカイブ処理
# =========================

@tasks.loop(
    seconds=ARCHIVE_INTERVAL
)
async def archive_loop():
    print(
        "アーカイブ確認"
    )

    blogs = get_archive_targets()

    if not blogs:
        print(
            "対象なし"
        )
        return

    for blog in blogs:
        try:
            member = blog.get(
                "member",
                ""
            )

            channels = get_channels(
                member
            )

            if not channels:
                print(
                    "投稿先なし:",
                    member
                )
                continue

            # 画像取得
            image_urls = get_images(
                blog["url"]
            )

            # 💡 【カスタム】1枚目の画像をEmbed（埋め込み）内に大きく表示させるための設定
            first_image_url = image_urls[0] if image_urls else None

            # 💡 【カスタム】表示形式をリッチにデザイン
            embed = discord.Embed(
                title=blog.get("title", "無題"),
                url=blog.get("url", ""),
                color=0x00aaff
            )

            # グループ名、メンバー名、投稿日時（時間込み）を綺麗に並べる
            embed.add_field(name="🏷️ グループ", value=blog.get("group", "不明"), inline=True)
            embed.add_field(name="👤 メンバー", value=member if member else "不明", inline=True)
            embed.add_field(name="📅 投稿日時", value=blog.get("date", "不明"), inline=False)

            if first_image_url:
                embed.set_image(url=first_image_url)

            embed.set_footer(
                text=f"Archive BOT • 画像総数: {len(image_urls)}枚"
            )

            # 全体＋個別へ送信
            for channel in channels:
                # 2枚目以降の画像がある場合はファイルとして添付する準備
                other_files = []
                if len(image_urls) > 1:
                    other_files = await create_files(image_urls[1:])

                # 送信実行（Embedとファイルを一緒に送る）
                await channel.send(
                    embed=embed,
                    files=other_files
                )

                await asyncio.sleep(
                    SEND_DELAY
                )

            # archive.db保存
            save_archive(
                blog.get("group", ""),
                blog.get("member", ""),
                blog.get("title", ""),
                blog.get("date", ""),
                blog.get("url", "")
            )

            print(
                "アーカイブ完了:",
                blog.get(
                    "title",
                    ""
                )
            )

            await asyncio.sleep(
                SEND_DELAY
            )

        except Exception as e:
            print(
                "アーカイブエラー:",
                e
            )


bot.run(
    TOKEN
)
