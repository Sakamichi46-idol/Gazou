import asyncio

from blog_checker import get_latest_blog
from config import BLOG_CHANNELS


last_urls = {}


async def check_blog(bot):

    while True:

        try:

            blogs = get_latest_blog()


            for blog in blogs:

                group = blog["group"]

                url = blog["url"]


                # 初回登録
                if group not in last_urls:

                    last_urls[group] = url
                    continue


                # 新記事の場合
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


        await asyncio.sleep(
            600
                    )
