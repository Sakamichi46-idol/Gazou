import discord
from discord.ext import commands
import re

from image_getter import get_images


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

        try:
            images = get_images(url)

            if images:
                for img in images[:5]:
                    await message.channel.send(img)
            else:
                await message.channel.send(
                    "画像が見つかりませんでした"
                )

        except Exception as e:
            await message.channel.send(
                f"エラー: {e}"
            )

    await bot.process_commands(message)


bot.run("ここにDiscord Bot Token")
