import requests
import json
import re

from bs4 import BeautifulSoup
from urllib.parse import urljoin



HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    ),
    "Referer": "https://www.nogizaka46.com/"
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

            "date": blog.get(
                "date",
                ""
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

    url = (
        "https://sakurazaka46.com"
        "/s/s46/diary/blog/list"
    )


    try:

        response = requests.get(
            url,
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
            url,
            link["href"]
        )



        member = article.select_one(
            ".name"
        )


        title = article.select_one(
            ".title"
        )


        date = article.select_one(
            ".date"
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

            "date": (
                date.get_text(
                    strip=True
                )
                if date else ""
            ),

            "text": ""

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

    url = (
        "https://www.hinatazaka46.com"
        "/s/official/diary/member/list"
        "?ima=0000"
    )


    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()


        soup = BeautifulSoup(
            response.text,
            "lxml"
        )


        item = soup.select_one(
            "li.p-blog-top__item"
        )


        if not item:

            print(
                "日向坂ブログ取得失敗"
            )

            return None



        link = item.find(
            "a",
            href=True
        )


        name = item.select_one(
            ".c-blog-top__name"
        )


        title = item.select_one(
            ".c-blog-top__title"
        )


        date = item.select_one(
            ".c-blog-top__date"
        )



        if not link:
            return None



        result = {

            "group": "日向坂46",

            "url":
                urljoin(
                    "https://www.hinatazaka46.com",
                    link["href"]
                ),

            "member":
                name.text.strip()
                if name else "",

            "title":
                title.text.strip()
                if title else "",

            "date":
                date.text.strip()
                if date else "",

            "text":
                ""

        }


        print(
            "日向坂取得:",
            result
        )


        return result



    except Exception as e:

        print(
            "日向坂取得エラー:",
            e
        )

        return None






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



    print(
        "最終取得:",
        results
    )


    return results
