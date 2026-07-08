import os
import re
import discord
from discord.ext import commands

from image_getter import get_images


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")


@bot.event
async def on_message(message):

    # Bot自身のメッセージは無視
    if message.author.bot:
        return

    # URLを探す
    urls = re.findall(
        r"https?://[^\s]+",
        message.content
    )

    if urls:

        url = urls[0]

        await message.channel.send(
            "画像を取得中..."
        )

        try:
            images = get_images(url)

            if images:

                for image in images[:5]:
                    await message.channel.send(image)

            else:
                await message.channel.send(
                    "画像が見つかりませんでした"
                )

        except Exception as e:

            await message.channel.send(
                f"取得エラー: {e}"
            )

    await bot.process_commands(message)


bot.run(
    os.environ["DISCORD_TOKEN"]
)
