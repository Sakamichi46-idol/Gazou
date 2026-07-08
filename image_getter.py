import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
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

    # 記事本文のみを対象にする
    target = (
        soup.find("div", class_="box-article")
        or soup.find("article")
        or soup.find("main")
        or soup
    )

    # 本文内の画像だけ取得
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
