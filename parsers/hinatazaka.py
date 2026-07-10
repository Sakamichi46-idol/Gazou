import requests

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
    )
}


def get_hinatazaka_images(url):

    blog = {
        "group": "日向坂46",
        "member": "",
        "title": "",
        "date": "",
        "url": url,
        "images": []
    }


    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()


    except Exception as e:

        print(
            "日向坂取得エラー:",
            e
        )

        return blog



    soup = BeautifulSoup(
        response.text,
        "lxml"
    )


    # =====================
    # タイトル
    # =====================

    title = soup.select_one(
        ".c-blog-article__title"
    )


    if not title:

        title = soup.find(
            "h1"
        )


    if title:

        blog["title"] = title.get_text(
            " ",
            strip=True
        )



    # =====================
    # メンバー
    # =====================

    member = soup.select_one(
        ".c-blog-article__name"
    )


    if not member:

        member = soup.select_one(
            ".p-blog-article__name"
        )


    if member:

        blog["member"] = member.get_text(
            " ",
            strip=True
        )



    # =====================
    # 日付
    # =====================

    date = soup.select_one(
        ".c-blog-article__date time"
    )


    if not date:

        date = soup.find(
            "time"
        )


    if date:

        date_text = (
            date.get("datetime")
            or date.get_text(
                " ",
                strip=True
            )
        )


        blog["date"] = normalize_datetime(
            date_text
        )



    # =====================
    # 本文
    # =====================

    article = soup.select_one(
        ".c-blog-article__text"
    )


    if not article:

        article = soup.select_one(
            ".p-blog-article__text"
        )


    if not article:

        article = soup



    # =====================
    # 画像取得
    # =====================

    seen = set()


    for img in article.find_all("img"):


        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
        )


        if not src:
            continue



        image_url = urljoin(
            url,
            src
        )



        # 画像判定
        if (
            "/files/" not in image_url
            and
            "hinatazaka46" not in image_url
        ):
            continue



        # 不要画像除外

        lower = image_url.lower()


        if any(
            x in lower
            for x in [
                "logo",
                "icon",
                "header",
                "footer"
            ]
        ):
            continue



        if image_url in seen:
            continue



        seen.add(
            image_url
        )


        blog["images"].append(
            image_url
        )



    print(
        "日向坂画像数:",
        len(blog["images"])
    )


    return blog
