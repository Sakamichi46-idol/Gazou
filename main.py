import os
import re
import io

import aiohttp
import discord
from discord.ext import commands

from image_getter import get_images

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

url_pattern = re.compile(r"https?://\S+")


@bot.event
async def on_ready():
    print(f"{bot.user} が起動しました！")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    urls = url_pattern.findall(message.content)

    for url in urls:
        try:
            images = get_images(url)

            if not images:
                await message.channel.send("画像が見つかりませんでした。")
                continue

            await message.channel.send(f"{len(images)}枚の画像が見つかりました。")

            async with aiohttp.ClientSession() as session:
                for i, image_url in enumerate(images[:10], start=1):
                    try:
                        async with session.get(image_url) as resp:
                            if resp.status != 200:
                                continue

                            data = await resp.read()

                            file = discord.File(
                                io.BytesIO(data),
                                filename=f"image{i}.jpg"
                            )

                            await message.channel.send(file=file)

                    except Exception as e:
                        print(f"画像取得エラー: {e}")

        except Exception as e:
            await message.channel.send(f"エラー: {e}")

    await bot.process_commands(message)


bot.run(TOKEN)
