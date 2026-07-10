import asyncio
import io

import aiohttp
import discord

from blog_checker import get_latest_blog
from image_getter import get_images
from config import BLOG_CHANNELS
from database import (
    is_notified,
    save_blog
)





async def send_images(channel, images):

    async with aiohttp.ClientSession() as session:

        files = []

        for i, image_url in enumerate(images, start=1):

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
                    "画像取得エラー:",
                    e
                )


        if files:

            for start in range(
                0,
                len(files),
                10
            ):

                await channel.send(
                    files=files[start:start+10]
                )



async def check_blog(bot):

    while True:

        try:

            blogs = get_latest_blog()


            for blog in blogs:

                group = blog["group"]

                url = blog["url"]


                # 初回起動時は通知しない
                if group not in last_urls:

                    last_urls[group] = url
                    continue



                # 新しい記事
                if url != last_urls[group]:

                    last_urls[group] = url



                    channel_id = BLOG_CHANNELS.get(
                        group
                    )


                    if not channel_id:
                        continue


                    channel = bot.get_channel(
                        channel_id
                    )


                    if not channel:
                        continue



                    # 通知
                    await channel.send(
                        f"🏷️ {blog['group']}\n"
                        f"👤 {blog['member']}\n"
                        f"📝 {blog['title']}\n"
                        f"📅 {blog['date']}\n"
                        f"🔗 {blog['url']}"
                    )



                    # 画像取得

                    detail = get_images(
                        blog["url"]
                    )


                    images = detail["images"]


                    if images:

                        await channel.send(
                            f"📷 ブログ画像 "
                            f"({len(images)}枚)"
                        )


                        await send_images(
                            channel,
                            images
                        )



        except Exception as e:

            print(
                "ブログ監視エラー:",
                e
            )


        await asyncio.sleep(
            600
        )
