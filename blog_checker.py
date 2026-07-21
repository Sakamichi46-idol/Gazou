import json
import re
from urllib.parse import (
    parse_qsl,
    urlencode,
    urljoin,
    urlsplit,
    urlunsplit,
)

import requests
from bs4 import BeautifulSoup

from parsers.utils import normalize_datetime


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

REQUEST_TIMEOUT = 15

# 1回の巡回で各グループから確認する最大件数
MAX_POSTS_PER_GROUP = 20


# =========================
# 共通処理
# =========================

def clean_text(value):
    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def canonicalize_url(url):
    """
    ima=xxxx のようにアクセスごとに変わる
    パラメータを削除して、同じ記事を同一URLとして扱う。
    """

    if not url:
        return ""

    parts = urlsplit(url)

    query = [
        (key, value)
        for key, value in parse_qsl(
            parts.query,
            keep_blank_values=True,
        )
        if key.lower() not in {
            "ima",
        }
    ]

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            "",
        )
    )


def get_text_from_selectors(
    element,
    selectors,
):
    for selector in selectors:
        tag = element.select_one(selector)

        if tag:
            text = clean_text(
                tag.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                return text

    return ""


def remove_duplicate_blogs(blogs):
    results = []
    seen_urls = set()

    for blog in blogs:
        if not isinstance(blog, dict):
            continue

        url = canonicalize_url(
            blog.get("url", "")
        )

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)
        blog["url"] = url
        results.append(blog)

    return results


# =========================
# 乃木坂46
# =========================

def get_nogizaka_latest():
    api_url = (
        "https://www.nogizaka46.com"
        "/s/n46/api/list/blog"
    )

    try:
        response = requests.get(
            api_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        print(
            "乃木坂 API STATUS:",
            response.status_code,
        )

        response.raise_for_status()

        match = re.search(
            r"res\((.*)\)\s*;?\s*$",
            response.text,
            flags=re.DOTALL,
        )

        if not match:
            print("乃木坂API解析失敗")
            return []

        data = json.loads(
            match.group(1)
        )

        posts = data.get(
            "data",
            [],
        )

        if not isinstance(posts, list):
            print(
                "乃木坂APIのdataが"
                "リストではありません。"
            )
            return []

        results = []

        for post in posts[
            :MAX_POSTS_PER_GROUP
        ]:
            if not isinstance(post, dict):
                continue

            blog_url = canonicalize_url(
                urljoin(
                    "https://www.nogizaka46.com",
                    post.get("link", ""),
                )
            )

            if not blog_url:
                continue

            results.append(
                {
                    "group": "乃木坂46",
                    "url": blog_url,
                    "member": clean_text(
                        post.get(
                            "name",
                            "",
                        )
                    ),
                    "title": clean_text(
                        post.get(
                            "title",
                            "",
                        )
                    ),
                    "date": normalize_datetime(
                        post.get(
                            "date",
                            "",
                        )
                    ),
                    "text": post.get(
                        "text",
                        "",
                    ),
                }
            )

        results = remove_duplicate_blogs(
            results
        )

        print(
            "乃木坂取得件数:",
            len(results),
        )

        # 一覧は新しい順なので、
        # 古い記事から通知する順番に変える
        return list(
            reversed(results)
        )

    except Exception as error:
        print(
            "乃木坂取得エラー:",
            error,
        )
        return []


# =========================
# 櫻坂46
# =========================

def get_sakurazaka_latest():
    list_url = (
        "https://sakurazaka46.com"
        "/s/s46/diary/blog/list"
    )

    try:
        response = requests.get(
            list_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "lxml",
        )

        articles = soup.select(
            "ul.com-blog-part li.box"
        )

        if not articles:
            articles = soup.select(
                'li:has(a[href*="/diary/detail/"])'
            )

        results = []

        for article in articles[
            :MAX_POSTS_PER_GROUP
        ]:
            link = article.select_one(
                'a[href*="/diary/detail/"]'
            )

            if not link:
                continue

            blog_url = canonicalize_url(
                urljoin(
                    list_url,
                    link.get(
                        "href",
                        "",
                    ),
                )
            )

            if not blog_url:
                continue

            member = get_text_from_selectors(
                article,
                [
                    "p.name",
                    ".name",
                    ".blog-member",
                    ".member",
                ],
            )

            title = get_text_from_selectors(
                article,
                [
                    "h3.title",
                    ".title",
                    ".blog-title",
                ],
            )

            date_text = get_text_from_selectors(
                article,
                [
                    "p.date.wf-a",
                    "p.date",
                    ".date",
                    "time",
                ],
            )

            results.append(
                {
                    "group": "櫻坂46",
                    "url": blog_url,
                    "member": member,
                    "title": title,
                    "date": normalize_datetime(
                        date_text
                    ),
                    "text": "",
                }
            )

        results = remove_duplicate_blogs(
            results
        )

        print(
            "櫻坂取得件数:",
            len(results),
        )

        return list(
            reversed(results)
        )

    except Exception as error:
        print(
            "櫻坂取得エラー:",
            error,
        )
        return []


# =========================
# 日向坂46
# =========================

def get_hinatazaka_latest():
    list_url = (
        "https://www.hinatazaka46.com"
        "/s/official/diary/member/list"
        "?ima=0000"
    )

    try:
        response = requests.get(
            list_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "lxml",
        )

        articles = soup.select(
            "li.p-blog-top__item"
        )

        results = []

        if articles:
            for article in articles[
                :MAX_POSTS_PER_GROUP
            ]:
                link = article.select_one(
                    'a[href*="/diary/detail/"]'
                )

                if not link:
                    continue

                blog_url = canonicalize_url(
                    urljoin(
                        list_url,
                        link.get(
                            "href",
                            "",
                        ),
                    )
                )

                if not blog_url:
                    continue

                member = get_text_from_selectors(
                    article,
                    [
                        ".c-blog-top__name",
                        ".c-blog-article__name",
                        ".name",
                    ],
                )

                title = get_text_from_selectors(
                    article,
                    [
                        ".c-blog-top__title",
                        ".c-blog-article__title",
                        ".title",
                    ],
                )

                date_text = get_text_from_selectors(
                    article,
                    [
                        ".c-blog-article__date time",
                        ".c-blog-top__date time",
                        ".c-blog-article__date",
                        ".date",
                        "time",
                    ],
                )

                results.append(
                    {
                        "group": "日向坂46",
                        "url": blog_url,
                        "member": member,
                        "title": title,
                        "date": normalize_datetime(
                            date_text
                        ),
                        "text": "",
                    }
                )

        # 一覧のliが取得できなかった場合の予備処理
        if not results:
            links = []

            for link in soup.select(
                'a[href*="/diary/detail/"]'
            ):
                blog_url = canonicalize_url(
                    urljoin(
                        list_url,
                        link.get(
                            "href",
                            "",
                        ),
                    )
                )

                if (
                    blog_url
                    and blog_url not in links
                ):
                    links.append(
                        blog_url
                    )

                if (
                    len(links)
                    >= MAX_POSTS_PER_GROUP
                ):
                    break

            for blog_url in links:
                results.append(
                    {
                        "group": "日向坂46",
                        "url": blog_url,
                        "member": "",
                        "title": "",
                        "date": "",
                        "text": "",
                    }
                )

        results = remove_duplicate_blogs(
            results
        )

        print(
            "日向坂取得件数:",
            len(results),
        )

        return list(
            reversed(results)
        )

    except Exception as error:
        print(
            "日向坂取得エラー:",
            error,
        )
        return []


# =========================
# 全グループ取得
# =========================

def get_latest_blog():
    results = []

    functions = [
        get_nogizaka_latest,
        get_sakurazaka_latest,
        get_hinatazaka_latest,
    ]

    for function in functions:
        try:
            blogs = function()

            if isinstance(blogs, dict):
                results.append(
                    blogs
                )

            elif isinstance(blogs, list):
                results.extend(
                    blogs
                )

        except Exception as error:
            print(
                f"{function.__name__} 実行エラー:",
                error,
            )

    results = remove_duplicate_blogs(
        results
    )

    print(
        "最終取得件数:",
        len(results),
    )

    for blog in results:
        print(
            blog.get("group", ""),
            blog.get("member", ""),
            blog.get("title", ""),
            blog.get("url", ""),
        )

    return results
