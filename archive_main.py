import os
import asyncio
import io
import shutil  # 💡 リセット機能のために追加

import aiohttp
import discord
from discord.ext import commands, tasks

from archive_checker import get_archive_targets
from archive_database import init_archive_db, save_archive
from archive_image_getter import get_images
from archive_config import ARCHIVE_INTERVAL, SEND_DELAY

# =========================
# Discord設定
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# チャンネル設定
# =========================

ARCHIVE_ALL_CHANNEL = 1524064741016862883
ARCHIVE_MEMBER_CHANNELS = {
    # 必要に応じてここに追記
}

# =========================
# 共通処理（画像取得・投稿先）
# =========================

async def download_image(url, index):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as response:
                data = await response.read()
                return discord.File(io.BytesIO(data), filename=f"image_{index}.jpg")
    except Exception as e:
        print("画像ダウンロードエラー:", e)
        return None

def get_channels(member):
    channels = []
    if ARCHIVE_ALL_CHANNEL:
        channel = bot.get_channel(ARCHIVE_ALL_CHANNEL)
        if channel:
            channels.append(channel)
    member_channel_id = ARCHIVE_MEMBER_CHANNELS.get(member)
    if member_channel_id:
        channel = bot.get_channel(member_channel_id)
        if channel:
            channels.append(channel)
    return channels

# =========================
# 起動・管理コマンド
# =========================

@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")
    init_archive_db()
    print("準備完了。!archive_start で巡回を開始してください。")

@bot.command()
@commands.is_owner()
async def archive_stop(ctx):
    if archive_loop.is_running():
        archive_loop.cancel()
        await ctx.send("🛑 ブログアーカイブの自動巡回を【一時停止】しました。")
    else:
        await ctx.send("⚠️ アーカイブは既に停止しています。")

@bot.command()
@commands.is_owner()
async def archive_start(ctx):
    if not archive_loop.is_running():
        archive_loop.start()
        await ctx.send("▶️ ブログアーカイブの自動巡回を【再開】しました。")
    else:
        await ctx.send("⚠️ アーカイブは既に動作中です。")

@bot.command()
@commands.is_owner()
async def archive_reset(ctx):
    """💡 データベースを削除して記憶をリセットするコマンド"""
    if os.path.exists("data"):
        try:
            shutil.rmtree("data")
            os.makedirs("data", exist_ok=True)
            init_archive_db()
            await ctx.send("🧹 データベースを削除して記憶をリセットしました！最初からアーカイブ可能です。")
        except Exception as e:
            await ctx.send(f"⚠️ リセットに失敗しました: {e}")
    else:
        await ctx.send("⚠️ データフォルダが見つかりません。")

@bot.command()
async def archive_status(ctx):
    if archive_loop.is_running():
        await ctx.send("🟢 現在、アーカイブ自動監視は【稼働中】です。")
    else:
        await ctx.send("🔴 現在、アーカイブ自動監視は【停止中】です。")

@archive_stop.error
@archive_start.error
@archive_reset.error
async def archive_command_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.send("❌ このコマンドはBotの管理者のみ実行できます。")

# =========================
# アーカイブ処理
# =========================

@tasks.loop(seconds=ARCHIVE_INTERVAL)
async def archive_loop():
    print("アーカイブ確認")
    blogs = await get_archive_targets()

    if not blogs:
        print("対象なし")
        return

    blogs.sort(key=lambda x: x.get("date", ""))

    for blog in blogs:
        try:
            member = blog.get("member", "")
            channels = get_channels(member)
            if not channels:
                continue

            image_urls = await get_images(blog["url"])

            embed = discord.Embed(
                title=blog.get("title", "無題"),
                url=blog.get("url", ""),
                color=0x00aaff
            )
            embed.add_field(name="🏷️ グループ", value=blog.get("group", "不明"), inline=True)
            embed.add_field(name="👤 メンバー", value=member if member else "不明", inline=True)
            embed.add_field(name="📅 投稿日時", value=blog.get("date", "不明"), inline=False)
            embed.set_footer(text=f"Archive BOT • 画像総数: {len(image_urls)}枚")

            for channel in channels:
                await channel.send(embed=embed)
                await asyncio.sleep(SEND_DELAY)

                if image_urls:
                    files = []
                    for index, url in enumerate(image_urls, start=1):
                        file = await download_image(url, index)
                        if file:
                            files.append(file)
                        if len(files) == 10:
                            await channel.send(files=files)
                            files = []
                            await asyncio.sleep(SEND_DELAY)
                    if files:
                        await channel.send(files=files)
                        await asyncio.sleep(SEND_DELAY)

            save_archive(
                blog.get("group", ""),
                blog.get("member", ""),
                blog.get("title", ""),
                blog.get("date", ""),
                blog.get("url", "")
            )
            print("アーカイブ完了:", blog.get("title", ""))
            await asyncio.sleep(SEND_DELAY)

        except Exception as e:
            print("アーカイブエラー:", e)

bot.run(TOKEN)
