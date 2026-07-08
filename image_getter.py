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

    # og:image
    og = soup.find(
        "meta",
        property="og:image"
    )

    if og and og.get("content"):

        images.append(
            og["content"]
        )

    # imgタグ
    for img in soup.find_all("img"):

        src = img.get("src")

        if src:

            images.append(
                urljoin(url, src)
            )

    # 重複削除
    images = list(dict.fromkeys(images))

    print(f"取得画像数: {len(images)}")

    return images
