import os
import asyncio
import io

import discord
from discord.ext import commands, tasks

import aiohttp


from archive_checker import (
    get_archive_targets,
    mark_archived
)

from archive_image_getter import (
    get_images
)

from keep_alive import keep_alive



TOKEN = os.getenv(
    "DISCORD_TOKEN"
)



intents = discord.Intents.default()


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)



# =========================
# メンバー別チャンネル設定
# =========================

ARCHIVE_CHANNELS = {

    # 例
    # "遠藤さくら": 123456789012345678,

}



# =========================
# 画像ダウンロード
# =========================


async def download_image(url):

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
            "画像DLエラー:",
            e
        )


        return None




# =========================
# 起動
# =========================


@bot.event
async def on_ready():

    print(
        f"ログイン成功: {bot.user}"
    )


    archive_loop.start()





# =========================
# アーカイブ処理
# =========================


@tasks.loop(
    minutes=1
)
async def archive_loop():


    blogs = get_archive_targets()



    if not blogs:

        print(
            "アーカイブ対象なし"
        )

        return



    for blog in blogs:


        try:


            member = blog.get(
                "member",
                ""
            )


            channel_id = ARCHIVE_CHANNELS.get(
                member
            )


            if not channel_id:

                print(
                    "チャンネル未設定:",
                    member
                )

                continue



            channel = bot.get_channel(
                channel_id
            )



            if not channel:

                continue



            images = get_images(
                blog["url"]
            )



            files = []



            for image_url in images[:5]:


                file = await download_image(
                    image_url
                )


                if file:

                    files.append(
                        file
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



            await channel.send(

                embed=embed,

                files=files

            )



            mark_archived(
                blog
            )



            await asyncio.sleep(
                2
            )



        except Exception as e:


            print(
                "アーカイブ処理エラー:",
                e
            )





# =========================
# 起動
# =========================


keep_alive()


bot.run(
    TOKEN
)
