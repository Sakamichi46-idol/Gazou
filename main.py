import os
import re

import discord
from discord.ext import commands

from media_getter import get_media
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(
        f"ログインしました: {bot.user}"
    )


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


        if "instagram.com" in url:

            await message.channel.send(
                "Instagram画像取得中..."
            )


            try:

                medias = get_media(url)


                if medias:

                    for media in medias[:10]:

                        await message.channel.send(
                            media
                        )

                else:

                    await message.channel.send(
                        "画像を取得できませんでした"
                    )


            except Exception as e:

                await message.channel.send(
                    f"エラー: {e}"
                )


    await bot.process_commands(message)



bot.run(
    os.environ["DISCORD_TOKEN"]
)
