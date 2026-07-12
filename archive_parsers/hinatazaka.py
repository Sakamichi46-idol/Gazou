import asyncio
import aiohttp

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

from archive_parsers.utils import normalize_datetime


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}


BASE_URL = "https://www.hinatazaka46.com"

BLOG_LIST_BASE_URL = (
    "https://www.hinatazaka46.com/"
    "s/official/diary/member/list?page={page}"
)



# =========================
# 最古ページ取得
# =========================

async def get_max_page(session):

    try:

        timeout = aiohttp.ClientTimeout(
            total=10
        )

        async with session.get(
            BLOG_LIST_BASE_URL.format(page=0),
            headers=HEADERS,
            timeout=timeout
        ) as response:

            response.raise_for_status()

            html = await response.text()


        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        max_page = 0


        for a in soup.select(
            ".c-pager__item a[href]"
        ):

            href = a.get(
                "href"
            )

            parsed = urlparse(
                href
            )

            queries = parse_qs(
                parsed.query
            )


            page_value = queries.get(
                "page"
            )


            if page_value:

                page_number = int(
                    page_value[0]
                )

                max_page = max(
                    max_page,
                    page_number
                )


        if max_page > 0:
            return max_page


        return 850


    except Exception as e:

        print(
            "日向坂最大ページ取得エラー:",
            e
        )

        return 850




# =========================
# URL一覧取得
# =========================

async def get_blog_urls(session):

    urls = []


    max_page = await get_max_page(
        session
    )


    print(
        f"日向坂46 最古ページ {max_page} から巡回開始"
    )


    for page in range(
        max_page,
        -1,
        -1
    ):

        url = BLOG_LIST_BASE_URL.format(
            page=page
        )


        try:

            timeout = aiohttp.ClientTimeout(
                total=10
            )


            async with session.get(
                url,
                headers=HEADERS,
                timeout=timeout
            ) as response:

                response.raise_for_status()

                html = await response.text()


            soup = BeautifulSoup(
                html,
                "html.parser"
            )


            page_urls = []


            for a in soup.select(
                "a[href]"
            ):

                href = a.get(
                    "href"
                )


                if not href:
                    continue


                if "/diary/detail/" not in href:
                    continue


                target_url = urljoin(
                    BASE_URL,
                    href
                )


                if target_url not in page_urls:

                    page_urls.append(
                        target_url
                    )


            # ページ内は新しい順なので反転
            page_urls.reverse()


            for item in page_urls:

                if item not in urls:

                    urls.append(
                        item
                    )


            print(
                f"日向坂 page={page} "
                f"取得 現在{len(urls)}件"
            )


            await asyncio.sleep(
                1
            )


        except Exception as e:

            print(
                f"日向坂一覧取得エラー page={page}:",
                e
            )

            continue



    return urls




# =========================
# 個別記事取得
# =========================

async def get_blog_list(session):

    urls = await get_blog_urls(
        session
    )


    blogs = []


    print(
        f"日向坂 詳細取得開始 {len(urls)}件"
    )



    for url in urls:


        try:

            timeout = aiohttp.ClientTimeout(
                total=10
            )


            async with session.get(
                url,
                headers=HEADERS,
                timeout=timeout
            ) as response:

                response.raise_for_status()

                html = await response.text()



            soup = BeautifulSoup(
                html,
                "html.parser"
            )



            title = ""

            title_tag = soup.select_one(
                ".c-blog-article__title"
            )

            if title_tag:

                title = title_tag.get_text(
                    strip=True
                )



            member = ""

            member_tag = soup.select_one(
                ".c-blog-article__name"
            )


            if member_tag:

                member = member_tag.get_text(
                    strip=True
                )



            date = ""

            date_tag = soup.select_one(
                ".c-blog-article__date time"
            )


            if date_tag:

                date = normalize_datetime(
                    date_tag.get_text(
                        strip=True
                    )
                )



            body = soup.select_one(
                ".c-blog-article__text"
            )


            text = ""

            if body:

                text = str(
                    body
                )



            blogs.append(
                {
                    "group": "日向坂46",
                    "url": url,
                    "member": member,
                    "title": title,
                    "date": date,
                    "text": text
                }
            )



            await asyncio.sleep(
                0.8
            )


        except Exception as e:

            print(
                "日向坂記事取得エラー:",
                url,
                e
            )



    return blogs

async def get_hinatazaka_images(session, url):

    timeout = aiohttp.ClientTimeout(total=10)

    try:

        async with session.get(
            url,
            headers=HEADERS,
            timeout=timeout
        ) as response:

            response.raise_for_status()
            html = await response.text()

    except Exception as e:

        print(
            "日向坂記事取得エラー:",
            url,
            e
        )

        return {
            "group": "日向坂46",
            "member": "",
            "title": "",
            "date": "不明",
            "url": url,
            "images": []
        }

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    blog = {
        "group": "日向坂46",
        "member": "",
        "title": "",
        "date": "不明",
        "url": url,
        "images": []
    }

    title = soup.select_one(
        ".c-blog-article__title"
    )

    if title:

        blog["title"] = title.get_text(
            strip=True
        )

    member = soup.select_one(
        ".c-blog-article__name"
    )

    if member:

        blog["member"] = member.get_text(
            strip=True
        )

    date = soup.select_one(
        ".c-blog-article__date time"
    )

    if date:

        blog["date"] = normalize_datetime(
            date.get_text(strip=True)
        )

    body = (
        soup.select_one(".c-blog-article__text")
        or soup
    )

    seen = set()

    for img in body.find_all("img"):

        src = img.get("src")

        if not src:
            continue

        image_url = urljoin(
            url,
            src
        )

        if "/files/" not in image_url:
            continue

        if image_url in seen:
            continue

        seen.add(image_url)

        blog["images"].append(
            image_url
        )

    print(
        f"取得画像数: {len(blog['images'])} {url}"
    )

    return blog


# =========================
# 外部呼び出し
# =========================

async def get_oldest_first(session):

    blogs = []

    urls = await get_blog_urls(
        session
    )


    for url in urls:

        blog_data = await get_hinatazaka_images(
            session,
            url
        )


        blogs.append(
            {
                "group": blog_data["group"],
                "url": blog_data["url"],
                "member": blog_data["member"],
                "title": blog_data["title"],
                "date": blog_data["date"]
            }
        )


        await asyncio.sleep(
            0.5
        )


    blogs.sort(
        key=lambda x: x.get(
            "date",
            ""
        )
    )


    return blogs
