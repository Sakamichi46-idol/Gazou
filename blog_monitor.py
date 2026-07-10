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
                    image_url,
                    timeout=15
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
                    "画像ダウンロードエラー:",
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
                files=files[start:start + 10]
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


                try:


                    if not isinstance(
                        blog,
                        dict
                    ):

                        print(
                            "不正データ:",
                            blog
                        )

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



                    # =====================
                    # DB保存
                    # （最初に登録）
                    # =====================

                    save_blog(
                        url,
                        group,
                        blog.get(
                            "member",
                            ""
                        ),
                        blog.get(
                            "title",
                            ""
                        ),
                        blog.get(
                            "date",
                            ""
                        )
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



                    try:

                        channel = bot.get_channel(
                            channel_id
                        )


                        if channel is None:

                            channel = await bot.fetch_channel(
                                channel_id
                            )


                    except Exception as e:

                        print(
                            "チャンネル取得エラー:",
                            e
                        )

                        continue



                    # =====================
                    # 画像取得
                    # =====================

                    try:

                        detail = get_images(
                            url
                        )


                    except Exception as e:

                        print(
                            "画像取得処理エラー:",
                            e
                        )

                        detail = {
                            "images": []
                        }



                    images = detail.get(
                        "images",
                        []
                    )



                    # =====================
                    # 通知文章
                    # =====================

                    text = (
                        f"🏷️ {group}\n"
                        f"👤 {blog.get('member','')}\n"
                        f"📝 {blog.get('title','')}\n"
                        f"📅 {blog.get('date','')}\n"
                        f"🔗 {url}\n\n"
                        f"📷 ブログ画像 ({len(images)}枚)"
                    )



                    await channel.send(
                        text,
                        suppress_embeds=True
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
                        "ブログ1件処理エラー:",
                        e
                    )



        except Exception as e:

            print(
                "ブログ監視エラー:",
                e
            )



        await asyncio.sleep(
            600
        )
