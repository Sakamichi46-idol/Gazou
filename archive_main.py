import os
import asyncio

import discord
from discord.ext import commands, tasks


from archive_checker import (
    get_archive_targets,
    mark_archived
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
    # "山下葉留花": 123456789012345678,

}



# =========================
# 起動時
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


    print(
        "アーカイブ確認開始"
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
                embed=embed
            )



            mark_archived(
                blog
            )



            await asyncio.sleep(
                2
            )



        except Exception as e:


            print(
                "投稿エラー:",
                e
            )





# =========================
# 起動
# =========================


keep_alive()


bot.run(
    TOKEN
)
