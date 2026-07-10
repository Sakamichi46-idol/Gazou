import os
import re
import io
import asyncio

import aiohttp
import discord

from discord.ext import commands

from image_getter import get_images
from blog_checker import get_latest_blog
from blog_monitor import check_blog
from database import init_db


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


blog_task = None



@bot.event
async def on_ready():

    global blog_task


    init_db()


    print(
        f"{bot.user} が起動しました！"
    )


    if blog_task is None:

        blog_task = asyncio.create_task(
            check_blog(bot)
        )

        print(
            "ブログ監視開始"
        )



@bot.command()
async def ping(ctx):

    await ctx.send(
        "Pong!"
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

        await ctx.send(
            (
                f"🏷️ {blog.get('group','')}\n"
                f"👤 {blog.get('member','')}\n"
                f"📝 {blog.get('title','')}\n"
                f"📅 {blog.get('date','')}\n"
                f"🔗 {blog.get('url','')}"
            ),
            suppress_embeds=True
        )



async def send_image_files(channel, images, text):

    async with aiohttp.ClientSession() as session:

        files = []


        for i, image_url in enumerate(
            images,
            start=1
        ):

            try:

                async with session.get(
                    image_url,
                    timeout=20
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
                    "画像取得エラー:",
                    e
                )



        if not files:

            await channel.send(
                "画像を取得できませんでした。",
                suppress_embeds=True
            )

            return



        for start in range(
            0,
            len(files),
            10
        ):

            await channel.send(
                content=text,
                files=files[start:start+10],
                suppress_embeds=True
            )


            text = ""



@bot.event
async def on_message(message):

    if message.author.bot:

        return



    urls = url_pattern.findall(
        message.content
    )


    for url in urls:

        try:

            blog = get_images(
                url
            )


            images = blog.get(
                "images",
                []
            )


            if not images:

                await message.channel.send(
                    "画像が見つかりませんでした。",
                    suppress_embeds=True
                )

                continue



            text = (
                f"🏷️ {blog.get('group','')}\n"
                f"👤 {blog.get('member','')}\n"
                f"📝 {blog.get('title','')}\n"
                f"📅 {blog.get('date','')}\n"
                f"🔗 {blog.get('url','')}\n\n"
                f"📷 ブログ画像 ({len(images)}枚)"
            )


            await send_image_files(
                message.channel,
                images,
                text
            )


        except Exception as e:

            print(
                "画像処理エラー:",
                e
            )

            await message.channel.send(
                f"エラー: {e}",
                suppress_embeds=True
            )



    await bot.process_commands(
        message
    )



bot.run(
    TOKEN
)
