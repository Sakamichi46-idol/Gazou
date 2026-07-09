import os

import discord
from discord.ext import commands

import re
from image_getter import get_images

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"{bot.user} が起動しました！")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


url_pattern = re.compile(r"https?://\S+")


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

            for image in images[:10]:
                await message.channel.send(image)

        except Exception as e:
            await message.channel.send(f"エラー: {e}")

    await bot.process_commands(message)


bot.run(TOKEN)
