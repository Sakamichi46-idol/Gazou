import os
import asyncio
import io

import aiohttp
import discord
from discord.ext import commands, tasks


from archive_checker import (
    get_archive_targets
)


from archive_database import (
    init_archive_db,
    mark_archived
)


from archive_image_getter import (
    get_images
)


from keep_alive import keep_alive




# =========================
# Discord設定
# =========================

TOKEN = os.getenv(
    "DISCORD_TOKEN"
)


intents = discord.Intents.default()


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)




# =========================
# チャンネル設定
# =========================

# 全記事を保存するアーカイブチャンネル

ARCHIVE_ALL_CHANNEL = 1524064741016862883




# メンバー別アーカイブチャンネル

ARCHIVE_MEMBER_CHANNELS = {


    # 例
    #
    # "遠藤さくら":
    #     123456789012345678,
    #
    # "賀喜遥香":
    #     123456789012345678,


}




# =========================
# 画像取得
# =========================


async def download_image(
    url
):

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(
                url,
                timeout=20
            ) as response:


                data = await response.read()


                return discord.File(
                    io.BytesIO(data),
                    filename="image.jpg"
                )



    except Exception as e:


        print(
            "画像ダウンロードエラー:",
            e
        )


        return None





async def create_files(
    image_urls
):

    files = []


    for url in image_urls[:5]:


        file = await download_image(
            url
        )


        if file:

            files.append(
                file
            )


    return files





# =========================
# 投稿先取得
# =========================


def get_channels(
    member
):

    channels = []



    # 全体アーカイブ

    if ARCHIVE_ALL_CHANNEL:


        channel = bot.get_channel(
            ARCHIVE_ALL_CHANNEL
        )


        if channel:

            channels.append(
                channel
            )




    # メンバー別

    member_channel_id = (
        ARCHIVE_MEMBER_CHANNELS.get(
            member
        )
    )


    if member_channel_id:


        channel = bot.get_channel(
            member_channel_id
        )


        if channel:

            channels.append(
                channel
            )



    return channels





# =========================
# 起動
# =========================


@bot.event
async def on_ready():


    print(
        f"ログイン成功: {bot.user}"
    )



    # archive.db作成

    init_archive_db()



    if not archive_loop.is_running():

        archive_loop.start()





# =========================
# アーカイブ処理
# =========================


@tasks.loop(
    minutes=1
)
async def archive_loop():


    print(
        "アーカイブ確認"
    )



    blogs = get_archive_targets()



    if not blogs:


        print(
            "対象なし"
        )


        return




    for blog in blogs:


        try:


            member = blog.get(
                "member",
                ""
            )



            channels = get_channels(
                member
            )



            if not channels:


                print(
                    "投稿先なし:",
                    member
                )


                continue





            # 画像取得

            image_urls = get_images(
                blog["url"]
            )



            files = await create_files(
                image_urls
            )




            embed = discord.Embed(

                title=blog.get(
                    "title",
                    ""
                ),

                description=(
                    blog.get(
                        "date",
                        ""
                    )
                    + "\n"
                    + blog.get(
                        "url",
                        ""
                    )
                ),

                color=0x00aaff

            )



            embed.set_author(
                name=member
            )



            embed.set_footer(
                text="Archive BOT"
            )





            # 全体＋個別へ送信

            for channel in channels:


                await channel.send(

                    embed=embed,

                    files=files.copy()

                )


                await asyncio.sleep(
                    1
                )





            # archive.db保存

            mark_archived(
                blog
            )



            print(
                "アーカイブ完了:",
                blog.get(
                    "title",
                    ""
                )
            )



            await asyncio.sleep(
                2
            )




        except Exception as e:


            print(
                "アーカイブエラー:",
                e
            )






# =========================
# 起動
# =========================


keep_alive()


bot.run(
    TOKEN
)
