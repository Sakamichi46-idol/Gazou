import asyncio
import io

import aiohttp
import discord

from blog_checker import get_latest_blog
from image_getter import get_images
from config import BLOG_CHANNELS
from database import is_notified, save_blog



async def send_images(channel, images):

    if not images:
        return


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

            return



        for start in range(
            0,
            len(files),
            10
        ):

            try:

                await channel.send(
                    files=files[start:start + 10]
                )


            except Exception as e:

                print(
                    "画像送信エラー:",
                    e
                )



async def check_blog(bot):

    while True:

        try:

            blogs = get_latest_blog()


            print(
                "監視取得:",
                blogs
            )



            if not blogs:

                await asyncio.sleep(
                    600
                )

                continue



            for blog in blogs:


                if not isinstance(
                    blog,
                    dict
                ):

                    continue



                url = blog.get(
                    "url"
                )


                if not url:

                    continue



                # =====================
                # DB確認
                # =====================

                if is_notified(url):

                    print(
                        "通知済み:",
                        url
                    )

                    continue



                group = blog.get(
                    "group",
                    ""
                )


                member = blog.get(
                    "member",
                    ""
                )


                title = blog.get(
                    "title",
                    ""
                )


                date = blog.get(
                    "date",
                    ""
                )



                # =====================
                # DB保存
                # ★ここで先に登録
                # =====================

                save_blog(
                    url,
                    group,
                    member,
                    title,
                    date
                )


                print(
                    "DB保存:",
                    url
                )



                # =====================
                # チャンネル取得
                # =====================

                channel_id = BLOG_CHANNELS.get(
                    group
                )


                if not channel_id:

                    print(
                        "チャンネルなし:",
                        group
                    )

                    continue



                channel = bot.get_channel(
                    channel_id
                )


                if not channel:

                    print(
                        "チャンネル取得失敗:",
                        channel_id
                    )

                    continue



                # =====================
                # 画像取得
                # =====================

                try:

                    detail = get_images(
                        url
                    )


                    images = detail.get(
                        "images",
                        []
                    )


                except Exception as e:

                    print(
                        "画像解析エラー:",
                        e
                    )

                    images = []



                # =====================
                # 通知文章
                # =====================

                message = (
                    f"🏷️ {group}\n"
                    f"👤 {member}\n"
                    f"📝 {title}\n"
                    f"📅 {date}\n"
                    f"🔗 {url}\n\n"
                    f"📷 ブログ画像 {len(images)}枚"
                )



                try:

                    await channel.send(
                        message,
                        suppress_embeds=True
                    )


                except Exception as e:

                    print(
                        "通知送信エラー:",
                        e
                    )



                # =====================
                # 画像送信
                # =====================

                if images:

                    await send_images(
                        channel,
                        images
                    )

                else:

                    print(
                        "画像なし:",
                        url
                    )



        except Exception as e:

            print(
                "ブログ監視エラー:",
                e
            )



        await asyncio.sleep(
            600
        )
