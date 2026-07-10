import requests
import json
import re

from bs4 import BeautifulSoup
from urllib.parse import urljoin

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


# =========================
# 乃木坂46
# =========================

def get_nogizaka_latest():

    url = (
        "https://www.nogizaka46.com"
        "/s/n46/api/list/blog"
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        print(
            "乃木坂 API STATUS:",
            response.status_code
        )

        response.raise_for_status()

        match = re.search(
            r"res\((.*)\)",
            response.text
        )

        if not match:
            print("乃木坂API解析失敗")
            return None

        data = json.loads(
            match.group(1)
        )

        if not data.get("data"):
            return None

        blog = data["data"][0]

        result = {

            "group": "乃木坂46",

            "url": blog.get(
                "link",
                ""
            ),

            "member": blog.get(
                "name",
                ""
            ),

            "title": blog.get(
                "title",
                ""
            ),

            "date": normalize_datetime(
                blog.get(
                    "date",
                    ""
                )
            ),

            "text": blog.get(
                "text",
                ""
            )
        }

        print(
            "乃木坂取得:",
            result
        )

        return result


    except Exception as e:

        print(
            "乃木坂取得エラー:",
            e
        )

        return None



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
            timeout=10
        )

        response.raise_for_status()


        soup = BeautifulSoup(
            response.text,
            "lxml"
        )


        article = soup.select_one(
            "ul.com-blog-part li.box"
        )


        if not article:

            print(
                "櫻坂ブログ取得失敗"
            )

            return None


        link = article.select_one(
            "a[href]"
        )


        if not link:

            return None


        blog_url = urljoin(
            list_url,
            link["href"]
        )


        detail = requests.get(
            blog_url,
            headers=HEADERS,
            timeout=10
        )

        detail.raise_for_status()


        detail_soup = BeautifulSoup(
            detail.text,
            "lxml"
        )


        date = ""

        date_tag = detail_soup.select_one(
            ".blog-foot .date"
        )

        if date_tag:

            date = normalize_datetime(
                date_tag.get_text(
                    strip=True
                )
            )


        member = article.select_one(
            ".name"
        )


        title = article.select_one(
            ".title"
        )


        body = detail_soup.select_one(
            ".box-article"
        )


        result = {

            "group": "櫻坂46",

            "url": blog_url,

            "member":
                member.get_text(
                    strip=True
                )
                if member else "",


            "title":
                title.get_text(
                    " ",
                    strip=True
                )
                if title else "",


            "date": date,


            "text":
                str(body)
                if body else ""

        }


        print(
            "櫻坂取得:",
            result
        )


        return result


    except Exception as e:

        print(
            "櫻坂取得エラー:",
            e
        )

        return None


# =========================
# 日向坂46
# =========================

def get_hinatazaka_latest():

    list_url = (
        "https://www.hinatazaka46.com"
        "/s/official/diary/member/list?ima=0000"
    )


    try:

        response = requests.get(
            list_url,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()


        soup = BeautifulSoup(
            response.text,
            "lxml"
        )


        links = soup.find_all(
            "a",
            href=re.compile(
                r"/s/official/diary/detail/"
            )
        )


        print(
            "日向坂リンク数:",
            len(links)
        )


        if not links:
            return []


        blog_url = urljoin(
            list_url,
            links[0]["href"]
        )


        print(
            "日向坂URL:",
            blog_url
        )


        detail = requests.get(
            blog_url,
            headers=HEADERS,
            timeout=10
        )

        detail.raise_for_status()


        detail_soup = BeautifulSoup(
            detail.text,
            "lxml"
        )


        # =====================
        # 本文
        # =====================

        body = None


        body_selectors = [

            ".p-blog-article",

            ".p-blog-detail",

            ".c-blog-detail",

            "article"

        ]


        for selector in body_selectors:

            body = detail_soup.select_one(
                selector
            )

            if body:
                print(
                    "日向坂本文:",
                    selector
                )
                break



        # =====================
        # メンバー
        # =====================

        member = ""


        member_selectors = [

            ".p-blog-detail__profile-name",

            ".p-blog-detail__name",

            ".profile-name",

            ".name"

        ]


        for selector in member_selectors:

            tag = detail_soup.select_one(
                selector
            )

            if tag:

                member = tag.get_text(
                    strip=True
                )

                break



        # OFFICIAL BLOG除外

        if (
            not member
            or "OFFICIAL" in member
        ):

            member = ""



        # =====================
        # タイトル
        # =====================

        title = ""


        title_selectors = [

            ".p-blog-detail__title",

            ".p-blog-detail__head h1",

            "h1"

        ]


        for selector in title_selectors:

            tag = detail_soup.select_one(
                selector
            )

            if tag:

                title = tag.get_text(
                    " ",
                    strip=True
                )

                break



        # =====================
        # 日付
        # =====================

        date = ""


        date_selectors = [

            "time",

            ".date",

            ".p-blog-detail__date"

        ]


        for selector in date_selectors:

            tag = detail_soup.select_one(
                selector
            )

            if tag:

                date = normalize_datetime(
                    tag.get_text(
                        strip=True
                    )
                )

                break



        result = {

            "group": "日向坂46",

            "url": blog_url,

            "member": member,

            "title": title,

            "date": date,

            "text":
                str(body)
                if body
                else ""

        }


        print(
            "日向坂取得:",
            result
        )


        return [result]



    except Exception as e:

        print(
            "日向坂取得エラー:",
            e
        )

        return []


# =========================
# 全グループ取得
# =========================

def get_latest_blog():

    results = []


    funcs = [

        get_nogizaka_latest,

        get_sakurazaka_latest,

        get_hinatazaka_latest

    ]


    for func in funcs:


        blog = func()


        if isinstance(
            blog,
            dict
        ):

            results.append(
                blog
            )


        elif isinstance(
            blog,
            list
        ):

            results.extend(
                blog
            )


    print(
        "最終取得:",
        results
    )


    return results
