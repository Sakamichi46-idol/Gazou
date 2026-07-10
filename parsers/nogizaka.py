import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from parsers.utils import normalize_datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0"
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
        "html.parser"
    )


    blog = {
        "group": "乃木坂46",
        "member": "",
        "title": "",
        "date": "",
        "url": url,
        "images": []
    }


    # タイトル取得
    title = soup.find("h1")

    if title:
        blog["title"] = title.get_text(
            strip=True
        )


    # メンバー名取得
    member = soup.find(
        class_="bd--prof__name"
    )

    if member:
        blog["member"] = member.get_text(
            strip=True
        )


    # 投稿日取得
    date = soup.find(
        class_="bd--hd__date"
    )

    if date:
        blog["date"] = normalize_datetime(
            date.get_text(
                " ",
                strip=True
            )
        )


    # 本文エリア取得
    article = (
        soup.find(
            "div",
            class_="bd--edit"
        )
        or soup.find(
            "article"
        )
        or soup.find(
            "main"
        )
    )


    if article is None:
        article = soup



    seen = set()


    # 画像取得
    for img in article.find_all("img"):

        src = img.get("src")


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


        seen.add(image_url)


        blog["images"].append(
            image_url
        )


    return blog
