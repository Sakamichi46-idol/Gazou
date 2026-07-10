import asyncio
import io

import aiohttp
import discord

from blog_checker import get_latest_blog
from image_getter import get_images
from config import BLOG_CHANNELS, ALL_BLOG_CHANNEL
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


        # Discord添付上限10枚対策

        for start in range(
            0,
            len(files),
            10
        ):

            await channel.send(
                files=files[start:start + 10]
            )



async def notify_channel(
    channel,
    blog,
    images
):

    text = (
        f"🏷️ {blog.get('group','')}\n"
        f"👤 {blog.get('member','')}\n"
        f"📝 {blog.get('title','')}\n"
        f"📅 {blog.get('date','')}\n"
        f"🔗 {blog.get('url','')}\n\n"
        f"📷 ブログ画像 ({len(images)}枚)"
    )


    await channel.send(
        text,
        suppress_embeds=True
    )


    if images:

        await send_images(
            channel,
            images
        )



async def check_blog(bot):

    while True:

        try:

            blogs = get_latest_blog()


            print(
                "監視取得:",
                len(blogs),
                "件"
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



                # DB確認

                if is_notified(
                    url
                ):

                    print(
                        "通知済み:",
                        url
                    )

                    continue



                group = blog.get(
                    "group",
                    ""
                )



                # =========================
                # 通知先作成
                # =========================

                channel_ids = list(
                    BLOG_CHANNELS.get(
                        group,
                        []
                    )
                )


                # 全体通知追加

                if ALL_BLOG_CHANNEL:

                    channel_ids.append(
                        ALL_BLOG_CHANNEL
                    )



                if not channel_ids:

                    print(
                        "通知先なし:",
                        group
                    )

                    continue



                # =========================
                # DB保存
                # =========================

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



                # =========================
                # 画像取得
                # =========================

                detail = get_images(
                    url
                )


                images = detail.get(
                    "images",
                    []
                )


                print(
                    "画像取得:",
                    len(images),
                    "枚"
                )



                # =========================
                # 複数チャンネル通知
                # =========================

                for channel_id in channel_ids:


                    channel = bot.get_channel(
                        channel_id
                    )


                    if not channel:

                        print(
                            "チャンネル取得失敗:",
                            channel_id
                        )

                        continue



                    await notify_channel(
                        channel,
                        blog,
                        images
                    )


                    print(
                        "通知完了:",
                        channel_id
                    )



        except Exception as e:

            print(
                "ブログ監視エラー:",
                e
            )



        await asyncio.sleep(
            600
        )
