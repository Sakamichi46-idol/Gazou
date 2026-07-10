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



def get_nogizaka_images(url):

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


    blog = {

        "group": "乃木坂46",

        "member": "",

        "title": "",

        "date": "",

        "url": url,

        "images": []

    }



    # =========================
    # タイトル
    # =========================

    title = soup.select_one(
        "h1"
    )

    if title:

        blog["title"] = title.get_text(
            " ",
            strip=True
        )



    # =========================
    # メンバー名
    # =========================

    member = soup.select_one(
        ".bd--prof__name"
    )

    if member:

        blog["member"] = member.get_text(
            " ",
            strip=True
        )



    # =========================
    # 投稿日
    # =========================

    date = soup.select_one(
        ".bd--hd__date"
    )

    if date:

        blog["date"] = normalize_datetime(
            date.get_text(
                " ",
                strip=True
            )
        )



    # =========================
    # 本文取得
    # =========================

    article = (

        soup.select_one(
            ".bd--edit"
        )

        or soup.select_one(
            ".bd--article"
        )

        or soup.select_one(
            ".bd--body"
        )

        or soup.select_one(
            ".blog-body"
        )

        or soup.find(
            "article"
        )

    )


    # 最終手段
    if article is None:

        article = soup



    # =========================
    # 画像取得
    # =========================

    seen = set()


    for img in article.find_all(
        "img"
    ):


        src = img.get(
            "src"
        )


        if not src:

            continue



        image_url = urljoin(
            url,
            src
        )



        # 乃木坂ブログ画像のみ

        if "/files/46/diary/" not in image_url:

            continue



        # 重複削除

        if image_url in seen:

            continue



        seen.add(
            image_url
        )


        blog["images"].append(
            image_url
        )



    print(
        "乃木坂画像取得:",
        len(blog["images"]),
        "枚"
    )


    return blog
