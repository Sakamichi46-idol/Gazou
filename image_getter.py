import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_images(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    images = []

    # まず記事本文を探す
    article = (
        soup.find("article")
        or soup.find(class_="box-article")
        or soup.find(class_="box-content")
        or soup.find(class_="entry-content")
        or soup.find(class_="post-content")
        or soup.find("main")
    )

    # 記事本文が見つかったらその中だけ検索
    target = article if article else soup

    # og:image（記事の代表画像）
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        images.append(og["content"])

    # 本文画像
    for img in target.find_all("img"):

        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
            or img.get("data-lazy-src")
        )

        if not src:
            continue

        full_url = urljoin(url, src)

        images.append(full_url)

    # 重複削除
    images = list(dict.fromkeys(images))

    print(f"取得画像数: {len(images)}")

    for image in images:
        print(image)

    return images
