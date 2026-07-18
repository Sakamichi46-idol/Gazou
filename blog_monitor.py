import asyncio

from blog_checker import get_latest_blog
from config import ALL_BLOG_CHANNEL, BLOG_CHANNELS
from database import is_notified, save_blog
from image_getter import get_images
from media_converter import send_blog_media


CHECK_INTERVAL = 600


def build_notification_text(blog, image_count):
    return (
        f"๐ท๏ธ {blog.get('group', '')}\n"
        f"๐ค {blog.get('member', '')}\n"
        f"๐ {blog.get('title', '')}\n"
        f"๐ {blog.get('date', '')}\n"
        f"๐ {blog.get('url', '')}\n\n"
        f"๐ท ใใญใฐ็ปๅ ({image_count}ๆ)"
    )


async def notify_channel(channel, blog, images):
    text = build_notification_text(blog, len(images))

    await send_blog_media(
        channel=channel,
        text=text,
        image_urls=images,
        send_delay=1.0,
    )


async def check_blog(bot):
    while not bot.is_closed():
        try:
            blogs = await asyncio.to_thread(get_latest_blog)
            print("็ฃ่ฆๅๅพ:", len(blogs), "ไปถ")

            for blog in blogs:
                if not isinstance(blog, dict):
                    print("ไธๆญฃใใผใฟ:", blog)
                    continue

                url = blog.get("url")
                if not url:
                    continue

                if is_notified(url):
                    print("้็ฅๆธใฟ:", url)
                    continue

                group = blog.get("group", "")
                channel_ids = list(BLOG_CHANNELS.get(group, []))

                if ALL_BLOG_CHANNEL:
                    channel_ids.append(ALL_BLOG_CHANNEL)

                # ๅใIDใ้่คใใฆใใฆใ1ๅใ ใ้็ฅใใ
                channel_ids = list(dict.fromkeys(channel_ids))

                if not channel_ids:
                    print("้็ฅๅใชใ:", group)
                    continue

                detail = await asyncio.to_thread(get_images, url)
                images = (
                    detail.get("images", [])
                    if isinstance(detail, dict)
                    else []
                )

                print("็ปๅๅๅพ:", len(images), "ๆ")

                all_succeeded = True
                notified_count = 0

                for channel_id in channel_ids:
                    channel = bot.get_channel(channel_id)

                    if not channel:
                        print("ใใฃใณใใซๅๅพๅคฑๆ:", channel_id)
                        all_succeeded = False
                        continue

                    try:
                        await notify_channel(channel, blog, images)
                        notified_count += 1
                        print("้็ฅๅฎไบ:", channel_id)
                    except Exception as error:
                        all_succeeded = False
                        print(
                            f"้็ฅใจใฉใผ channel={channel_id} url={url}:",
                            error,
                        )

                # ๅฐใชใใจใ1ใๆใธ้็ฅใงใใๅจ้็ฅๅใๆๅใใๅ ดๅใ ใไฟๅญ
                if notified_count > 0 and all_succeeded:
                    save_blog(
                        url,
                        group,
                        blog.get("member", ""),
                        blog.get("title", ""),
                        blog.get("date", ""),
                    )
                    print("้็ฅๆธใฟDBไฟๅญ:", url)
                else:
                    print("้็ฅใซๅคฑๆใใใใDBไฟๅญใ่ฆ้ใใพใ:", url)

        except asyncio.CancelledError:
            print("ใใญใฐ็ฃ่ฆใฟในใฏใ็ตไบใใพใใ")
            raise
        except Exception as error:
            print("ใใญใฐ็ฃ่ฆใจใฉใผ:", error)

        await asyncio.sleep(CHECK_INTERVAL)
