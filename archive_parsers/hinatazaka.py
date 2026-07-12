import asyncio
from datetime import datetime
from urllib.parse import (
    parse_qs,
    urljoin,
    urlsplit,
    urlunsplit,
)

import aiohttp
from bs4 import BeautifulSoup

from archive_parsers.utils import (
    normalize_datetime,
    normalize_member_name,
)


# =========================
# 基本設定
# =========================

BASE_URL = "https://www.hinatazaka46.com"

BLOG_LIST_URL = (
    "https://www.hinatazaka46.com/"
    "s/official/diary/member/list"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Referer": "https://www.hinatazaka46.com/",
}


# =========================
# URL正規化
# =========================

def normalize_blog_url(url: str) -> str:
    """
    imaやcdなど、変化するクエリ文字列を削除する。

    例:
    https://www.hinatazaka46.com/s/official/diary/detail/70143
    ?ima=0000&cd=member

        ↓

    https://www.hinatazaka46.com/s/official/diary/detail/70143
    """

    if not url:
        return ""

    full_url = urljoin(
        BASE_URL,
        url
    )

    parts = urlsplit(
        full_url
    )

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            "",
            ""
        )
    )


# =========================
# 日時ソート用
# =========================

def datetime_key(blog: dict) -> datetime:
    """
    ブログのdateをdatetimeへ変換する。

    変換できない場合は最後に回す。
    """

    date_text = blog.get(
        "date",
        ""
    )

    formats = (
        "%Y年%m月%d日 %H:%M",
        "%Y年%m月%d日",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    )

    for fmt in formats:

        try:

            return datetime.strptime(
                date_text,
                fmt
            )

        except ValueError:

            continue

    return datetime.max


# =========================
# HTML取得
# =========================

async def fetch_html(
    session: aiohttp.ClientSession,
    url: str,
) -> str:

    timeout = aiohttp.ClientTimeout(
        total=20
    )

    async with session.get(
        url,
        headers=HEADERS,
        timeout=timeout
    ) as response:

        response.raise_for_status()

        return await response.text()


# =========================
# 最大ページ取得
# =========================

async def get_max_page(
    session: aiohttp.ClientSession
) -> int:

    url = (
        f"{BLOG_LIST_URL}"
        "?ima=0000&page=0"
    )

    try:

        html = await fetch_html(
            session,
            url
        )

    except Exception as e:

        print(
            "日向坂 最大ページ取得エラー:",
            e
        )

        # HTMLから取得できなかった場合の暫定値
        return 850


    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    max_page = 0


    pager_links = soup.select(
        ".c-pager__item a[href], "
        ".p-pager a[href], "
        ".c-pager a[href], "
        "a[href*='page=']"
    )


    for anchor in pager_links:

        href = anchor.get(
            "href",
            ""
        )

        if not href:
            continue


        query = parse_qs(
            urlsplit(href).query
        )

        page_values = query.get(
            "page"
        )

        if not page_values:
            continue


        try:

            page_number = int(
                page_values[0]
            )

        except (TypeError, ValueError):

            continue


        max_page = max(
            max_page,
            page_number
        )


    if max_page <= 0:

        print(
            "⚠️ 日向坂の最大ページを"
            "HTMLから取得できませんでした。"
            " 暫定値850を使用します。"
        )

        return 850


    print(
        f"日向坂 最大ページ: {max_page}"
    )

    return max_page


# =========================
# 記事カード解析
# =========================

def parse_blog_card(
    card
) -> dict | None:
    """
    一覧ページ上の記事カードから、

    ・URL
    ・メンバー
    ・タイトル
    ・日時

    を取得する。
    """

    link_tag = card.select_one(
        "a[href*='/diary/detail/']"
    )


    # card自体がaタグの場合
    if not link_tag:

        if (
            getattr(card, "name", None) == "a"
            and "/diary/detail/" in card.get("href", "")
        ):

            link_tag = card

        else:

            return None


    href = link_tag.get(
        "href",
        ""
    )

    blog_url = normalize_blog_url(
        href
    )

    if not blog_url:
        return None


    title_tag = (
        card.select_one(".c-blog-top__title")
        or card.select_one(".c-blog-article__title")
        or card.select_one(".p-blog-top__title")
        or card.select_one(".title")
        or card.select_one("h3")
        or card.select_one("h2")
    )


    member_tag = (
        card.select_one(".c-blog-top__name")
        or card.select_one(".c-blog-article__name")
        or card.select_one(".p-blog-top__name")
        or card.select_one(".name")
    )


    date_tag = (
        card.select_one(".c-blog-article__date time")
        or card.select_one(".c-blog-top__date time")
        or card.select_one(".p-blog-top__date time")
        or card.select_one("time")
        or card.select_one(".date")
    )


    title = (
        title_tag.get_text(
            " ",
            strip=True
        )
        if title_tag
        else ""
    )


    member = normalize_member_name(
        member_tag.get_text(
            " ",
            strip=True
        )
        if member_tag
        else ""
    )


    raw_date = (
        date_tag.get_text(
            " ",
            strip=True
        )
        if date_tag
        else ""
    )


    date = normalize_datetime(
        raw_date
    )


    return {
        "group": "日向坂46",
        "url": blog_url,
        "member": member,
        "title": title,
        "date": date,
        "text": ""
    }


# =========================
# 1ページ取得
# =========================

async def get_page_blogs(
    session: aiohttp.ClientSession,
    page: int,
) -> list[dict]:

    url = (
        f"{BLOG_LIST_URL}"
        f"?ima=0000&page={page}"
    )


    try:

        html = await fetch_html(
            session,
            url
        )

    except Exception as e:

        print(
            f"日向坂 page={page} 取得エラー:",
            e
        )

        return []


    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    # 現行サイトの候補
    cards = soup.select(
        "li.p-blog-top__item"
    )


    # フォールバック
    if not cards:

        cards = soup.select(
            ".p-blog-top__item"
        )


    if not cards:

        cards = soup.select(
            "li.c-blog-top__item"
        )


    if not cards:

        cards = soup.select(
            "article"
        )


    # 最終フォールバック
    if not cards:

        cards = soup.select(
            "a[href*='/diary/detail/']"
        )


    page_blogs = []

    seen_urls = set()


    for card in cards:

        blog = parse_blog_card(
            card
        )

        if not blog:
            continue


        blog_url = blog.get(
            "url",
            ""
        )

        if not blog_url:
            continue


        if blog_url in seen_urls:
            continue


        seen_urls.add(
            blog_url
        )

        page_blogs.append(
            blog
        )


    # 一覧ページ内は新しい順なので反転
    page_blogs.reverse()


    print(
        f"日向坂 page={page}: "
        f"{len(page_blogs)}件"
    )


    return page_blogs


# =========================
# 全記事取得
# =========================

async def get_all_blogs(
    session: aiohttp.ClientSession
) -> list[dict]:

    max_page = await get_max_page(
        session
    )


    print(
        f"日向坂 page={max_page} から"
        "古い順に巡回します。"
    )


    blogs = []

    seen_urls = set()


    # 最大ページが最古側
    for page in range(
        max_page,
        -1,
        -1
    ):

        page_blogs = await get_page_blogs(
            session,
            page
        )


        for blog in page_blogs:

            blog_url = blog.get(
                "url",
                ""
            )

            if not blog_url:
                continue


            if blog_url in seen_urls:
                continue


            seen_urls.add(
                blog_url
            )

            blogs.append(
                blog
            )


        print(
            f"日向坂 進捗 page={page} / "
            f"合計{len(blogs)}件"
        )


        # 公式サイトへの連続アクセスを抑える
        await asyncio.sleep(
            0.5
        )


    print(
        f"日向坂 重複除去後: {len(blogs)}件"
    )


    return blogs


# =========================
# 詳細ページ補完
# =========================

async def fill_missing_metadata(
    session: aiohttp.ClientSession,
    blog: dict,
) -> dict:
    """
    一覧ページでタイトル・メンバー・日時が
    取得できなかった場合だけ詳細ページを開く。

    全記事の詳細ページを開かないため、
    通常より軽くなる。
    """

    if (
        blog.get("title")
        and blog.get("member")
        and blog.get("date")
    ):

        return blog


    url = blog.get(
        "url",
        ""
    )

    if not url:
        return blog


    try:

        html = await fetch_html(
            session,
            url
        )

    except Exception as e:

        print(
            "日向坂 詳細補完エラー:",
            url,
            e
        )

        return blog


    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    if not blog.get("title"):

        title_tag = soup.select_one(
            ".c-blog-article__title"
        )

        if title_tag:

            blog["title"] = title_tag.get_text(
                " ",
                strip=True
            )


    if not blog.get("member"):

        member_tag = (
            soup.select_one(
                ".c-blog-article__name a"
            )
            or soup.select_one(
                ".c-blog-article__name"
            )
        )

        if member_tag:

            blog["member"] = member_tag.get_text(
                " ",
                strip=True
            )


    if not blog.get("date"):

        date_tag = soup.select_one(
            ".c-blog-article__date time"
        )

        if date_tag:

            blog["date"] = normalize_datetime(
                date_tag.get_text(
                    " ",
                    strip=True
                )
            )


    return blog


# =========================
# archive_checker用
# =========================

async def get_oldest_first(
    session: aiohttp.ClientSession
) -> list[dict]:

    blogs = await get_all_blogs(
        session
    )


    # 一覧ページから情報を取れなかった記事だけ補完
    missing_count = sum(
        1
        for blog in blogs
        if (
            not blog.get("title")
            or not blog.get("member")
            or not blog.get("date")
        )
    )


    print(
        f"日向坂 詳細補完対象: "
        f"{missing_count}件"
    )


    for index, blog in enumerate(
        blogs,
        start=1
    ):

        if (
            blog.get("title")
            and blog.get("member")
            and blog.get("date")
        ):

            continue


        await fill_missing_metadata(
            session,
            blog
        )


        if index % 50 == 0:

            print(
                f"日向坂 詳細補完進捗 "
                f"{index}/{len(blogs)}"
            )


        await asyncio.sleep(
            0.3
        )


    # 最終的に日時で正確に並べる
    blogs.sort(
        key=datetime_key
    )


    if blogs:

        print(
            "日向坂 最古:",
            blogs[0].get(
                "date",
                ""
            ),
            blogs[0].get(
                "url",
                ""
            )
        )

        print(
            "日向坂 最新:",
            blogs[-1].get(
                "date",
                ""
            ),
            blogs[-1].get(
                "url",
                ""
            )
        )


    print(
        f"日向坂 最終取得: "
        f"{len(blogs)}件"
    )


    return blogs
