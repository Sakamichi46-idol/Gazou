import os
import re

import discord
from discord.ext import commands

from image_getter import get_images
from instagram_api import get_instagram
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    urls = re.findall(
        r"https?://\S+",
        message.content
    )

    if urls:

        url = urls[0]

        await message.channel.send("画像取得中...")

        try:

            # InstagramならInstagram専用処理
            if "instagram.com" in url:

                images = get_instagram(url)

            # それ以外はブログなど
            else:

                images = get_images(url)

            if images:

                for image in images:
                    await message.channel.send(image)

            else:

                await message.channel.send(
                    "画像が見つかりませんでした。"
                )

        except Exception as e:

            await message.channel.send(
                f"取得エラー: {e}"
            )

    await bot.process_commands(message)


keep_alive()

bot.run(
    os.environ["DISCORD_TOKEN"]
)
