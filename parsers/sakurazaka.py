import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0"
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
        "images": []
    }


    # タイトル
    title = soup.find("h1")

    if title:
        blog["title"] = title.get_text(strip=True)


    # メンバー名
    member = (
        soup.find(class_="name")
        or soup.find(class_="bd--prof__name")
    )

    if member:
        blog["member"] = member.get_text(strip=True)


    # 投稿日
    date = (
        soup.find(class_="date")
        or soup.find(class_="bd--hd__date")
    )

    if date:
        blog["date"] = date.get_text(strip=True)


    # 本文
    article = (
        soup.find(
            class_="box-article"
        )
        or soup.find(
            class_="bd--edit"
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


        # 櫻坂ブログ画像
        if "/files/" not in src:
            continue


        if src in seen:
            continue


        seen.add(src)

        blog["images"].append(src)


    return blog
