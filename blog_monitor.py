import asyncio
import io

import aiohttp
import discord

from blog_checker import get_latest_blog
from image_getter import get_images
from config import BLOG_CHANNELS
from database import is_notified, save_blog



async def send_images(channel, images):

    async with aiohttp.ClientSession() as session:

        files = []


        for i, image_url in enumerate(
            images,
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
                    "画像取得エラー:",
                    e
                )


        if not files:

            return



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


            print(
                "取得ブログ:",
                blogs
            )


            if not blogs:

                print(
                    "ブログ取得なし"
                )

                await asyncio.sleep(600)

                continue



            for blog in blogs:


                if not isinstance(
                    blog,
                    dict
                ):

                    print(
                        "不正なブログデータ:",
                        blog
                    )

                    continue



                url = blog.get(
                    "url"
                )


                if not url:

                    print(
                        "URLなし:",
                        blog
                    )

                    continue



                # 通知済みならスキップ

                if is_notified(
                    url
                ):

                    continue



                group = blog.get(
                    "group",
                    ""
                )



                channel_id = BLOG_CHANNELS.get(
                    group
                )



                if not channel_id:

                    print(
                        f"{group} のチャンネル未設定"
                    )

                    continue



                channel = bot.get_channel(
                    channel_id
                )



                if channel is None:

                    print(
                        "チャンネル取得失敗:",
                        channel_id
                    )

                    continue



                # ブログ情報送信

                await channel.send(
                    f"🏷️ {group}\n"
                    f"👤 {blog.get('member','')}\n"
                    f"📝 {blog.get('title','')}\n"
                    f"📅 {blog.get('date','')}\n"
                    f"🔗 {url}"
                )



                # 画像取得

                detail = get_images(
                    url
                )


                images = detail.get(
                    "images",
                    []
                )



                if images:

                    await channel.send(
                        f"📷 ブログ画像 "
                        f"({len(images)}枚)"
                    )


                    await send_images(
                        channel,
                        images
                    )


                else:

                    print(
                        "画像なし:",
                        url
                    )



                # DB保存

                save_blog(
                    blog
                )



        except Exception as e:

            print(
                "ブログ監視エラー:",
                e
            )



        await asyncio.sleep(
            600
        )
