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
            print(
                "乃木坂API解析失敗"
            )
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

            "member": (
                member.get_text(
                    strip=True
                )
                if member else ""
            ),

            "title": (
                title.get_text(
                    " ",
                    strip=True
                )
                if title else ""
            ),

            "date": date,

            "text": (
                str(body)
                if body else ""
            )

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


        print(
            "日向坂HTML長:",
            len(response.text)
        )


        soup = BeautifulSoup(
            response.text,
            "lxml"
        )


        blogs = []


        # ブログ詳細URLを探す
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



        # 最新1件のみ
        link = links[0]


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


        # 本文
        body = detail_soup.select_one(
            ".p-blog-detail__text"
        )


        if not body:

            body = detail_soup.select_one(
                "article"
            )


        # メンバー名
        member = ""


        member_tag = detail_soup.select_one(
            ".p-blog-detail__name"
        )


        if member_tag:

            member = member_tag.get_text(
                strip=True
            )



        # タイトル
        title = ""


        title_tag = detail_soup.select_one(
            "h1"
        )


        if title_tag:

            title = title_tag.get_text(
                " ",
                strip=True
            )



        # 日付
        date = ""


        date_tag = detail_soup.select_one(
            "time"
        )


        if date_tag:

            date = normalize_datetime(
                date_tag.get_text(
                    strip=True
                )
            )



        result = {

            "group": "日向坂46",

            "url": blog_url,

            "member": member,

            "title": title,

            "date": date,

            "text": (
                str(body)
                if body else ""
            )

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
