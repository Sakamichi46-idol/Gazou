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
            blog = get_images(url)

            images = blog["images"]

            if not images:
                await message.channel.send("画像が見つかりませんでした。")
                continue

            files = []

            async with aiohttp.ClientSession() as session:
                for i, image_url in enumerate(images[:10], start=1):
                    try:
                        async with session.get(image_url) as resp:
                            if resp.status != 200:
                                continue

                            data = await resp.read()

                            files.append(
                                discord.File(
                                    io.BytesIO(data),
                                    filename=f"image{i}.jpg"
                                )
                            )

                    except Exception as e:
                        print(f"画像取得エラー: {e}")

            text = ""

            if blog["member"]:
                text += f"👤 {blog['member']}\n"

            if blog["title"]:
                text += f"📝 {blog['title']}\n"

            if blog["date"]:
                text += f"📅 {blog['date']}\n"

            text += f"\n📷 ブログ画像（{len(files)}枚）"

            if files:
                await message.channel.send(
                    content=text,
                    files=files
                )
            else:
                await message.channel.send("画像を取得できませんでした。")

        except Exception as e:
            print(e)
            await message.channel.send(f"エラー: {e}")

    await bot.process_commands(message)


bot.run(TOKEN)
