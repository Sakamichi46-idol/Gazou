import os
import re
import io

import aiohttp
import discord
from discord.ext import commands

from image_getter import get_images
from blog_checker import get_latest_blog
from blog_monitor import check_blog

TOKEN = os.getenv("TOKEN")


intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


url_pattern = re.compile(
    r"https?://\S+"
)


@bot.event
async def on_ready():

    print(
        f"{bot.user} が起動しました！"
    )


@bot.command()
async def ping(ctx):

    await ctx.send(
        "Pong!"
    )


@bot.event
async def on_message(message):

    if message.author.bot:
        return


    urls = url_pattern.findall(
        message.content
    )


    for url in urls:

        try:

            blog = get_images(url)

            images = blog["images"]


            if not images:

                await message.channel.send(
                    "画像が見つかりませんでした。"
                )

                continue


            text = ""


            if blog.get("group"):

                text += (
                    f"🏷️ {blog['group']}\n"
                )


            if blog.get("member"):

                text += (
                    f"👤 {blog['member']}\n"
                )


            if blog.get("title"):

                text += (
                    f"📝 {blog['title']}\n"
                )


            if blog.get("date"):

                text += (
                    f"📅 {blog['date']}\n"
                )


            text += (
                f"\n📷 ブログ画像 "
                f"({len(images)}枚)"
            )


            # Discordは1回10枚まで
            for start in range(
                0,
                len(images),
                10
            ):

                batch = images[start:start + 10]


                files = []


                async with aiohttp.ClientSession() as session:

                    for i, image_url in enumerate(
                        batch,
                        start=1
                    ):

                        try:

                            async with session.get(
                                image_url
                            ) as resp:


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

                            print(
                                f"画像取得エラー: {e}"
                            )


                if files:

                    await message.channel.send(
                        content=text,
                        files=files
                    )


                    text = ""


        except Exception as e:

            print(
                e
            )

            await message.channel.send(
                f"エラー: {e}"
            )


    await bot.process_commands(
        message
    )



@bot.command()
async def latest(ctx):

    blogs = get_latest_blog()


    if not blogs:

        await ctx.send(
            "ブログ取得失敗"
        )

        return



    for blog in blogs:


        text = (
            f"🏷️ {blog.get('group', '')}\n"
            f"👤 {blog.get('member', '')}\n"
            f"📝 {blog.get('title', '')}\n"
            f"📅 {blog.get('date', '')}\n"
            f"🔗 {blog.get('url', '')}"
        )


        await ctx.send(
            text
        )



bot.run(TOKEN)
