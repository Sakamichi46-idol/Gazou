import asyncio

from blog_checker import get_latest_blog


last_blog = None


async def check_blog(bot, channel_id):

    global last_blog


    while True:

        try:

            blogs = get_latest_blog()


            if blogs:

                blog = blogs[0]


                current_url = blog["url"]


                if current_url != last_blog:

                    last_blog = current_url


                    channel = bot.get_channel(
                        channel_id
                    )


                    if channel:

                        await channel.send(
                            f"🏷️ {blog['group']}\n"
                            f"👤 {blog['member']}\n"
                            f"📝 {blog['title']}\n"
                            f"📅 {blog['date']}\n"
                            f"🔗 {blog['url']}"
                        )


        except Exception as e:

            print(
                "ブログ監視エラー:",
                e
            )


        # 10分ごと
        await asyncio.sleep(
            600
)
