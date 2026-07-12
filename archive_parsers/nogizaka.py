import asyncio
import json
import re

from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

import aiohttp
from bs4 import BeautifulSoup

from archive_parsers.utils import (
    normalize_datetime,
    normalize_member_name,
)


# =========================
# 基本設定
# =========================

API_URL = (
    "https://www.nogizaka46.com"
    "/s/n46/api/list/blog"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Referer": (
        "https://www.nogizaka46.com/"
        "s/n46/diary/MEMBER"
    ),
}


# 詳細ページの同時取得数
DETAIL_CONCURRENCY = 5

# 詳細ページ取得後の待機時間
DETAIL_DELAY = 0.2


# =========================
# URL正規化
# =========================

def normalize_blog_url(
    url: str
) -> str:
    """
    imaなど、記事内容と関係のない
    クエリ文字列を削除する。

    例:
    detail/104610?ima=5638
        ↓
    detail/104610
    """

    if not url:
        return ""

    parts = urlsplit(
        url
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
# APIレスポンス解析
# =========================

def parse_api_response(
    text: str
) -> dict | None:

    if not text:
        return None


    # JSONP形式
    # res({...})
    match = re.search(
        r"^\s*res\((.*)\)\s*;?\s*$",
        text,
        flags=re.DOTALL
    )


    if match:

        try:

            return json.loads(
                match.group(1)
            )

        except json.JSONDecodeError as e:

            print(
                "乃木坂API JSONP解析エラー:",
                e
            )

            return None


    # 通常のJSON形式にも対応
    try:

        return json.loads(
            text
        )

    except json.JSONDecodeError:

        print(
            "乃木坂APIレスポンス解析失敗:",
            text[:200]
        )

        return None


# =========================
# API取得
# =========================

async def fetch_api_items(
    session: aiohttp.ClientSession,
    params=None
):

    timeout = aiohttp.ClientTimeout(
        total=20
    )


    async with session.get(
        API_URL,
        params=params or {},
        headers=HEADERS,
        timeout=timeout
    ) as response:

        response.raise_for_status()

        text = await response.text()


    data = parse_api_response(
        text
    )


    if not data:

        return [], {}


    items = data.get(
        "data",
        []
    )


    if not isinstance(
        items,
        list
    ):

        items = []


    return items, data


# =========================
# API記事を共通形式へ変換
# =========================

def convert_item(
    item: dict
) -> dict | None:

    raw_url = item.get(
        "link",
        ""
    )


    blog_url = normalize_blog_url(
        raw_url
    )


    if not blog_url:

        return None


    member = normalize_member_name(
        item.get(
            "name",
            ""
        )
    )


    date = normalize_datetime(
        item.get(
            "date",
            ""
        )
    )


    return {

        "group":
            "乃木坂46",

        "url":
            blog_url,

        "member":
            member,

        "title":
            item.get(
                "title",
                ""
            ) or "",

        "date":
            date,

        "text":
            item.get(
                "text",
                ""
            ) or ""

    }


# =========================
# 詳細ページHTML取得
# =========================

async def fetch_detail_html(
    session: aiohttp.ClientSession,
    url: str
) -> str:

    timeout = aiohttp.ClientTimeout(
        total=20
    )


    request_headers = dict(
        HEADERS
    )

    request_headers["Accept"] = (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    )


    async with session.get(
        url,
        headers=request_headers,
        timeout=timeout,
        allow_redirects=True
    ) as response:

        response.raise_for_status()

        return await response.text(
            errors="replace"
        )


# =========================
# 詳細ページから情報取得
# =========================

async def enrich_blog_detail(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    blog: dict,
    index: int,
    total: int
) -> dict:
    """
    詳細ページから、

    ・時刻を含む投稿日
    ・メンバー名
    ・タイトル

    を補完する。
    """

    url = blog.get(
        "url",
        ""
    )


    if not url:

        return blog


    async with semaphore:

        try:

            html = await fetch_detail_html(
                session,
                url
            )


            soup = BeautifulSoup(
                html,
                "html.parser"
            )


            # -------------------------
            # 投稿日時
            # -------------------------

            date_tag = (
                soup.select_one(
                    ".bd--hd__date"
                )
                or soup.select_one(
                    ".bd--date"
                )
                or soup.select_one(
                    "time"
                )
            )


            if date_tag:

                raw_date = date_tag.get_text(
                    " ",
                    strip=True
                )


                detail_date = normalize_datetime(
                    raw_date
                )


                if detail_date:

                    blog["date"] = detail_date


            # -------------------------
            # メンバー
            # -------------------------

            member_tag = (
                soup.select_one(
                    ".bd--prof__name"
                )
                or soup.select_one(
                    ".bd--name"
                )
            )


            if member_tag:

                member = normalize_member_name(
                    member_tag.get_text(
                        " ",
                        strip=True
                    )
                )


                if member:

                    blog["member"] = member


            # -------------------------
            # タイトル
            # -------------------------

            title_tag = (
                soup.select_one(
                    ".bd--hd__ttl"
                )
                or soup.select_one(
                    "h1"
                )
            )


            if title_tag:

                title = title_tag.get_text(
                    " ",
                    strip=True
                )


                if title:

                    blog["title"] = title


            print(
                f"乃木坂 詳細取得 "
                f"{index}/{total}: "
                f"{blog.get('date', '不明')} / "
                f"{blog.get('member', '不明')} / "
                f"{url}"
            )


        except Exception as e:

            print(
                "乃木坂詳細ページ取得エラー:",
                url,
                e
            )


        await asyncio.sleep(
            DETAIL_DELAY
        )


    return blog


# =========================
# 全記事の詳細情報補完
# =========================

async def enrich_all_details(
    session: aiohttp.ClientSession,
    blogs: list[dict]
) -> list[dict]:

    if not blogs:

        return []


    print(
        f"乃木坂 詳細日時取得開始: "
        f"{len(blogs)}件"
    )


    semaphore = asyncio.Semaphore(
        DETAIL_CONCURRENCY
    )


    tasks = []


    for index, blog in enumerate(
        blogs,
        start=1
    ):

        tasks.append(

            enrich_blog_detail(

                session,

                semaphore,

                blog,

                index,

                len(blogs)

            )

        )


    results = await asyncio.gather(
        *tasks,
        return_exceptions=True
    )


    enriched_blogs = []


    for original_blog, result in zip(
        blogs,
        results
    ):

        if isinstance(
            result,
            Exception
        ):

            print(
                "乃木坂詳細補完タスクエラー:",
                result
            )

            enriched_blogs.append(
                original_blog
            )

        else:

            enriched_blogs.append(
                result
            )


    print(
        f"乃木坂 詳細日時取得完了: "
        f"{len(enriched_blogs)}件"
    )


    return enriched_blogs


# =========================
# ページング確認
# =========================

async def test_pagination(
    session: aiohttp.ClientSession
):

    first_items, first_data = await fetch_api_items(
        session
    )


    second_items, second_data = await fetch_api_items(
        session,
        params={
            "page": 2
        }
    )


    first_urls = [

        normalize_blog_url(
            item.get(
                "link",
                ""
            )
        )

        for item in first_items

        if item.get(
            "link"
        )

    ]


    second_urls = [

        normalize_blog_url(
            item.get(
                "link",
                ""
            )
        )

        for item in second_items

        if item.get(
            "link"
        )

    ]


    print(
        f"乃木坂 API1回目: "
        f"{len(first_urls)}件"
    )


    print(
        f"乃木坂 page=2指定: "
        f"{len(second_urls)}件"
    )


    if first_urls:

        print(
            "乃木坂 1回目先頭:",
            first_urls[0]
        )

        print(
            "乃木坂 1回目末尾:",
            first_urls[-1]
        )


    if second_urls:

        print(
            "乃木坂 page=2先頭:",
            second_urls[0]
        )

        print(
            "乃木坂 page=2末尾:",
            second_urls[-1]
        )


    same_result = (
        bool(first_urls)
        and first_urls == second_urls
    )


    if same_result:

        print(
            "⚠️ 乃木坂APIはpage指定を無視して、"
            "同じ一覧を返しています。"
        )

    else:

        print(
            "乃木坂APIのページ移動を確認できました。"
        )


    metadata_keys = [

        key

        for key in first_data.keys()

        if key != "data"

    ]


    print(
        "乃木坂APIメタ情報キー:",
        metadata_keys
    )


    for key in metadata_keys:

        value = first_data.get(
            key
        )


        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
                type(None)
            )
        ):

            print(
                f"乃木坂API {key}: "
                f"{value}"
            )


    return (
        first_items,
        second_items,
        same_result
    )


# =========================
# ブログ一覧取得
# =========================

async def get_all_blog_urls(
    session: aiohttp.ClientSession
) -> list[dict]:

    (
        first_items,
        second_items,
        same_result

    ) = await test_pagination(
        session
    )


    # page=2が同一内容の場合、
    # 重複取得を避けて最初の100件だけ使う
    if same_result:

        source_items = first_items

    else:

        source_items = (
            first_items
            +
            second_items
        )


    blogs = []

    seen_urls = set()


    for item in source_items:

        blog = convert_item(
            item
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


        blogs.append(
            blog
        )


    print(
        f"乃木坂 重複除去後: "
        f"{len(blogs)}件"
    )


    # 詳細ページを開いて時刻を取得
    blogs = await enrich_all_details(
        session,
        blogs
    )


    return blogs


# =========================
# 日時ソート
# =========================

def datetime_key(
    blog: dict
) -> datetime:

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


    for date_format in formats:

        try:

            return datetime.strptime(
                date_text,
                date_format
            )

        except ValueError:

            continue


    return datetime.max


# =========================
# archive_checker用
# =========================

async def get_oldest_first(
    session: aiohttp.ClientSession
) -> list[dict]:

    blogs = await get_all_blog_urls(
        session
    )


    blogs.sort(
        key=datetime_key
    )


    if blogs:

        print(
            "乃木坂 最古:",
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
            "乃木坂 最新:",
            blogs[-1].get(
                "date",
                ""
            ),
            blogs[-1].get(
                "url",
                ""
            )
        )


    return blogs
