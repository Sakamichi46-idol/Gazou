import json
import re
import traceback

from urllib.parse import urljoin

import aiohttp


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
}



API_URL = (
    "https://www.nogizaka46.com"
    "/s/n46/api/list/blog"
)



# =========================
# 全記事取得
# =========================

async def get_all_blog_urls(
    session
):

    blogs = []


    for page in range(
        1,
        200
    ):

        url = (
            API_URL
            +
            f"?page={page}"
        )


        try:

            async with session.get(
                url,
                headers=HEADERS,
                timeout=20
            ) as response:

                text = await response.text()



        except Exception as e:

            print(
                "乃木坂API取得エラー:",
                e
            )

            continue



        match = re.search(
            r"res\((.*)\)",
            text
        )


        if not match:

            print(
                f"乃木坂 page={page} API解析失敗"
            )

            break



        try:

            data = json.loads(
                match.group(1)
            )


        except Exception:

            traceback.print_exc()
            break



        items = data.get(
            "data",
            []
        )


        print(
            f"乃木坂 page={page}: {len(items)}件"
        )



        if not items:

            break



        for blog in items:


            blogs.append(
                {

                    "group":
                        "乃木坂46",

                    "url":
                        blog.get(
                            "link",
                            ""
                        ),

                    "member":
                        blog.get(
                            "name",
                            ""
                        ),

                    "title":
                        blog.get(
                            "title",
                            ""
                        ),

                    "date":
                        blog.get(
                            "date",
                            ""
                        ),

                    "text":
                        blog.get(
                            "text",
                            ""
                        )

                }
            )



    print(
        "乃木坂総取得:",
        len(blogs)
    )


    return blogs



# =========================
# archive_checker用
# =========================

async def get_oldest_first(
    session
):

    blogs = await get_all_blog_urls(
        session
    )


    blogs.sort(
        key=lambda x:
            x.get(
                "date",
                ""
            )
    )


    return blogs
