import asyncio
from archive_parsers.utils import (
    normalize_datetime,
    normalize_member_name,
)
from urllib.parse import (
    parse_qs,
    urljoin,
    urlsplit,
    urlunsplit,
)

import aiohttp
from bs4 import BeautifulSoup

from archive_parsers.utils import normalize_datetime


BASE_URL = "https://sakurazaka46.com"

BLOG_LIST_URL = (
    "https://sakurazaka46.com/"
    "s/s46/diary/blog/list"
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
    "Referer": "https://sakurazaka46.com/",
}


# =========================
# URL正規化
# =========================

def normalize_blog_url(url: str) -> str:
    """
    imaなどの変動するクエリを取り除き、
    同じ記事を同一URLとして扱う。
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

    # 日付解析に失敗した記事は最後へ
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
            "櫻坂 最大ページ取得エラー:",
            e
        )

        # 取得できなかった場合の暫定値
        return 381


    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    max_page = 0


    # 一般的なページャー
    pager_links = soup.select(
        ".com-pager a[href], "
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
            "⚠️ 櫻坂 最大ページをHTMLから取得できませんでした。"
            " 暫定値381を使用します。"
        )

        return 381


    print(
        f"櫻坂 最大ページ: {max_page}"
    )

    return max_page


# =========================
# 記事カード解析
# =========================

def parse_blog_card(
    card
) -> dict | None:

    link_tag = card.select_one(
        "a[href*='/diary/detail/']"
    )


    if not link_tag:

        # card自体がaタグの場合にも対応
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
        card.select_one(".title")
        or card.select_one("h3")
        or card.select_one("h2")
    )


    member_tag = (
        card.select_one(".name")
        or card.select_one(".blog-name")
    )


    date_tag = (
        card.select_one(".date.wf-a")
        or card.select_one(".date")
        or card.select_one("time")
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
        "group": "櫻坂46",
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
            f"櫻坂 page={page} 取得エラー:",
            e
        )

        return []


    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    # 現行HTMLを優先
    cards = soup.select(
        "ul.com-blog-part li.box"
    )


    # サイト変更時のフォールバック
    if not cards:

        cards = soup.select(
            "li.box"
        )


    # さらにフォールバック
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


        blog_url = blog["url"]


        if blog_url in seen_urls:
            continue


        seen_urls.add(
            blog_url
        )

        page_blogs.append(
            blog
        )


    # 一覧は新しい順で表示されるため、
    # 古い記事から処理できるようページ内を反転
    page_blogs.reverse()


    print(
        f"櫻坂 page={page}: "
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
        f"櫻坂 page={max_page} から"
        "古い順に巡回します。"
    )


    blogs = []

    seen_urls = set()


    # 最大ページが最古側なので、
    # max_page → 0 の順で巡回
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
            f"櫻坂 進捗 page={page} / "
            f"合計{len(blogs)}件"
        )


        # サイトへ負荷をかけすぎない
        await asyncio.sleep(
            0.5
        )


    print(
        f"櫻坂 重複除去後: {len(blogs)}件"
    )


    return blogs


# =========================
# archive_checker用
# =========================

async def get_oldest_first(
    session: aiohttp.ClientSession
) -> list[dict]:

    blogs = await get_all_blogs(
        session
    )


    # 念のため日時で再ソート
    blogs.sort(
        key=datetime_key
    )


    if blogs:

        print(
            "櫻坂 最古:",
            blogs[0].get("date", ""),
            blogs[0].get("url", "")
        )

        print(
            "櫻坂 最新:",
            blogs[-1].get("date", ""),
            blogs[-1].get("url", "")
        )


    return blogs
