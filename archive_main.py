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
# 起動・管理コマンド
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


# 💡 【カスタム】アーカイブを一時停止するコマンド
@bot.command()
@commands.is_owner()  # コマンド作成者（あなた）だけが実行可能
async def archive_stop(ctx):
    if archive_loop.is_running():
        archive_loop.cancel()
        await ctx.send("🛑 ブログアーカイブの自動巡回を【一時停止】しました。")
    else:
        await ctx.send("⚠️ アーカイブは既に停止しています。")


# 💡 【カスタム】アーカイブを再開するコマンド
@bot.command()
@commands.is_owner()
async def archive_start(ctx):
    if not archive_loop.is_running():
        archive_loop.start()
        await ctx.send("▶️ ブログアーカイブの自動巡回を【再開】しました。")
    else:
        await ctx.send("⚠️ アーカイブは既に動作中です。")


# 💡 【カスタム】現在の動作状態を確認するコマンド
@bot.command()
async def archive_status(ctx):
    if archive_loop.is_running():
        await ctx.send("🟢 現在、アーカイブ自動監視は【稼働中】です。")
    else:
        await ctx.send("🔴 現在、アーカイブ自動監視は【停止中】です。")


# エラーハンドリング（管理者以外の実行を弾いたときのメッセージ）
@archive_stop.error
@archive_start.error
async def archive_command_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.send("❌ このコマンドはBotの管理者のみ実行できます。")




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

            # テキスト情報（グループ、メンバー、日時、タイトル）をEmbedに整理
            embed = discord.Embed(
                title=blog.get("title", "無題"),
                url=blog.get("url", ""),
                color=0x00aaff
            )

            embed.add_field(name="🏷️ グループ", value=blog.get("group", "不明"), inline=True)
            embed.add_field(name="👤 メンバー", value=member if member else "不明", inline=True)
            embed.add_field(name="📅 投稿日時", value=blog.get("date", "不明"), inline=False)

            embed.set_footer(
                text=f"Archive BOT • 画像総数: {len(image_urls)}枚"
            )

            # 全体＋個別へ送信
            for channel in channels:
                send_files = []
                if image_urls:
                    send_files = await create_files(image_urls)

                await channel.send(
                    embed=embed,
                    files=send_files
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
