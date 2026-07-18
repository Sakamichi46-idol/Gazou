import asyncio

from blog_checker import get_latest_blog
from config import ALL_BLOG_CHANNEL, BLOG_CHANNELS
from database import is_notified, save_blog
from image_getter import get_images
from media_converter import send_blog_media


CHECK_INTERVAL = 600


def build_notification_text(blog, image_count):
    return (
        f"🏷️ {blog.get('group', '')}\n"
        f"👤 {blog.get('member', '')}\n"
        f"📝 {blog.get('title', '')}\n"
        f"📅 {blog.get('date', '')}\n"
        f"🔗 {blog.get('url', '')}\n\n"
        f"📷 ブログ画像 ({image_count}枚)"
    )


async def notify_channel(channel, blog, images):
    text = build_notification_text(
        blog,
        len(images),
    )

    await send_blog_media(
        channel=channel,
        text=text,
        image_urls=images,
        send_delay=1.0,
    )


async def check_blog(bot):
    while not bot.is_closed():
        try:
            blogs = await asyncio.to_thread(
                get_latest_blog
            )

            print(
                "新着取得:",
                len(blogs),
                "件",
            )

            for blog in blogs:
                if not isinstance(blog, dict):
                    print(
                        "不正データ:",
                        blog,
                    )
                    continue

                url = blog.get("url")

                if not url:
                    continue

                if is_notified(url):
                    print(
                        "通知済み:",
                        url,
                    )
                    continue

                group = blog.get(
                    "group",
                    "",
                )

                channel_ids = list(
                    BLOG_CHANNELS.get(
                        group,
                        [],
                    )
                )

                if ALL_BLOG_CHANNEL:
                    channel_ids.append(
                        ALL_BLOG_CHANNEL
                    )

                # 同じチャンネルIDが重複していても
                # 1回だけ通知する
                channel_ids = list(
                    dict.fromkeys(
                        channel_ids
                    )
                )

                if not channel_ids:
                    print(
                        "通知先なし:",
                        group,
                    )
                    continue

                detail = await asyncio.to_thread(
                    get_images,
                    url,
                )

                images = (
                    detail.get(
                        "images",
                        [],
                    )
                    if isinstance(
                        detail,
                        dict,
                    )
                    else []
                )

                print(
                    "画像取得:",
                    len(images),
                    "枚",
                )

                all_succeeded = True
                notified_count = 0

                for channel_id in channel_ids:
                    channel = bot.get_channel(
                        channel_id
                    )

                    if not channel:
                        print(
                            "チャンネル取得失敗:",
                            channel_id,
                        )

                        all_succeeded = False
                        continue

                    try:
                        await notify_channel(
                            channel,
                            blog,
                            images,
                        )

                        notified_count += 1

                        print(
                            "通知完了:",
                            channel_id,
                        )

                    except Exception as error:
                        all_succeeded = False

                        print(
                            (
                                "通知エラー "
                                f"channel={channel_id} "
                                f"url={url}:"
                            ),
                            error,
                        )

                # 少なくとも1か所へ通知でき、
                # 全通知先が成功した場合だけ保存
                if (
                    notified_count > 0
                    and all_succeeded
                ):
                    save_blog(
                        url,
                        group,
                        blog.get(
                            "member",
                            "",
                        ),
                        blog.get(
                            "title",
                            "",
                        ),
                        blog.get(
                            "date",
                            "",
                        ),
                    )

                    print(
                        "通知済みDB保存:",
                        url,
                    )

                else:
                    print(
                        (
                            "通知に失敗したため"
                            "DB保存を見送ります:"
                        ),
                        url,
                    )

        except asyncio.CancelledError:
            print(
                "ブログ監視タスクを終了します。"
            )
            raise

        except Exception as error:
            print(
                "ブログ監視エラー:",
                error,
            )

        await asyncio.sleep(
            CHECK_INTERVAL
        )
