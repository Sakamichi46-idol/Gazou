import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.utils import normalize_datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_hinatazaka_images(url):
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
        "group": "日向坂46",
        "member": "",
        "title": "",
        "date": "",
        "images": []
    }


    # タイトル
    title = soup.find("h1")

    if title:
        blog["title"] = title.get_text(strip=True)


    # メンバー名
    member = (
        soup.find(
            class_="c-blog-article__name"
        )
        or soup.find(
            class_="name"
        )
        or soup.find(
            class_="bd--prof__name"
        )
    )

    if member:
        blog["member"] = member.get_text(
            strip=True
        )

    # 投稿日
    date = (
        soup.find("time")
        or soup.find(class_="date")
        or soup.find(class_="c-blog-article__date")
    )

    if date:
        blog["date"] = normalize_datetime(
            date.get_text(
                " ",
                strip=True
            )
        )


    # 本文
    article = (
        soup.find(
            class_="c-blog-article__text"
        )
        or soup.find(
            class_="box-article"
        )
        or soup.find("article")
        or soup.find("main")
    )


    if article is None:
        article = soup


    seen = set()


    for img in article.find_all("img"):

        src = img.get("src")

        if not src:
            continue


        src = urljoin(
            url,
            src
        )


        # 日向坂ブログ画像
        if "/files/14/diary/" not in src:
            continue


        if src in seen:
            continue


        seen.add(src)

        blog["images"].append(src)


    return blog
