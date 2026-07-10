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


def get_sakurazaka_images(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    blog = {

        "group": "櫻坂46",

        "member": "",

        "title": "",

        "date": "",

        "url": url,

        "images": []

    }


    # =====================
    # タイトル
    # =====================

    title = soup.select_one(
        "h1.title"
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
    # メンバー・日付
    # =====================

    blog_foot = soup.select_one(
        ".blog-foot"
    )


    if blog_foot:


        member = blog_foot.select_one(
            ".name"
        )


        if member:

            blog["member"] = member.get_text(
                " ",
                strip=True
            )



        date = blog_foot.select_one(
            ".date"
        )


        if date:

            blog["date"] = normalize_datetime(
                date.get_text(
                    " ",
                    strip=True
                )
            )



    # =====================
    # 本文
    # =====================

    article = (

        soup.select_one(
            ".box-article"
        )

        or

        soup.select_one(
            ".blog-body"
        )

        or

        soup.find(
            "article"
        )

        or

        soup.find(
            "main"
        )

    )


    if article is None:

        article = soup



    # =====================
    # 画像取得
    # =====================

    seen = set()


    for img in article.find_all(
        "img"
    ):


        src = (

            img.get("src")

            or

            img.get("data-src")

            or

            img.get("data-original")

        )


        if not src:

            continue



        image_url = urljoin(
            url,
            src
        )



        # ロゴ・アイコン除外
        if any(
            x in image_url.lower()
            for x in [
                "logo",
                "icon",
                "header",
                "footer"
            ]
        ):

            continue



        # 櫻坂ブログ画像判定
        if (
            "/files/" not in image_url
            or
            "diary" not in image_url
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
        "櫻坂画像取得:",
        len(blog["images"]),
        "枚"
    )


    return blog
