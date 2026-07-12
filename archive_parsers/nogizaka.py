import json
import re
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

import aiohttp

from archive_parsers.utils import normalize_datetime


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


# =========================
# URL正規化
# =========================

def normalize_blog_url(url: str) -> str:
    """
    imaの値が違うだけの同一記事を、
    同じURLとして扱える形へ変換する。

    例:
    detail/104608?ima=5638
    detail/104608?ima=5639
        ↓
    detail/104608
    """

    if not url:
        return ""

    parts = urlsplit(url)

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

def parse_api_response(text: str) -> dict | None:

    if not text:
        return None

    # JSONP形式: res({...})
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

    # 通常JSON形式にも対応
    try:
        return json.loads(text)

    except json.JSONDecodeError:

        print(
            "乃木坂APIレスポンス解析失敗:",
            text[:200]
        )

        return None


# =========================
# 1回分取得
# =========================

async def fetch_api_items(
    session,
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


    data = parse_api_response(text)

    if not data:
        return [], {}


    items = data.get(
        "data",
        []
    )

    if not isinstance(items, list):
        items = []


    return items, data


# =========================
# API記事を共通形式へ変換
# =========================

def convert_item(item: dict) -> dict | None:

    raw_url = item.get(
        "link",
        ""
    )

    url = normalize_blog_url(
        raw_url
    )

    if not url:
        return None


    date = normalize_datetime(
        item.get(
            "date",
            ""
        )
    )


    return {
        "group": "乃木坂46",
        "url": url,
        "member": item.get("name", "") or "",
        "title": item.get("title", "") or "",
        "date": date,
        "text": item.get("text", "") or ""
    }


# =========================
# APIページング確認
# =========================

async def test_pagination(session):

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
            item.get("link", "")
        )
        for item in first_items
    ]

    second_urls = [
        normalize_blog_url(
            item.get("link", "")
        )
        for item in second_items
    ]


    first_urls = [
        url
        for url in first_urls
        if url
    ]

    second_urls = [
        url
        for url in second_urls
        if url
    ]


    print(
        f"乃木坂 API1回目: {len(first_urls)}件"
    )

    print(
        f"乃木坂 page=2指定: {len(second_urls)}件"
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
        first_urls == second_urls
        and bool(first_urls)
    )


    if same_result:

        print(
            "⚠️ 乃木坂APIは page=2 を無視して、"
            "同じ一覧を返しています。"
        )

    else:

        print(
            "乃木坂APIのページ移動を確認できました。"
        )


    # APIが返すメタ情報を確認
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

        value = first_data.get(key)

        if isinstance(
            value,
            (str, int, float, bool, type(None))
        ):

            print(
                f"乃木坂API {key}: {value}"
            )


    return (
        first_items,
        second_items,
        same_result
    )


# =========================
# ブログ取得
# =========================

async def get_all_blog_urls(session):

    first_items, second_items, same_result = (
        await test_pagination(session)
    )


    # page指定が無視される状態で
    # 199回取得すると同じ100件が重複するため、
    # テスト中は最初のレスポンスだけ使う
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


        url = blog["url"]


        if url in seen_urls:
            continue


        seen_urls.add(
            url
        )

        blogs.append(
            blog
        )


    print(
        f"乃木坂 重複除去後: {len(blogs)}件"
    )


    return blogs


# =========================
# 日時ソート用
# =========================

def datetime_key(blog):

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
# archive_checker用
# =========================

async def get_oldest_first(session):

    blogs = await get_all_blog_urls(
        session
    )


    blogs.sort(
        key=datetime_key
    )


    if blogs:

        print(
            "乃木坂 最古:",
            blogs[0]["date"],
            blogs[0]["url"]
        )

        print(
            "乃木坂 最新:",
            blogs[-1]["date"],
            blogs[-1]["url"]
        )


    return blogs
