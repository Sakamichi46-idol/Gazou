import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_images(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 記事本文を探す
    article = (
        soup.find("div", class_="bd--edit")
        or soup.find("article")
        or soup.find("main")
    )

    if article is None:
        article = soup

    images = []
    seen = set()

    for img in article.find_all("img"):
        src = img.get("src")

        if not src:
            continue

        src = urljoin(url, src)

        # ブログ画像以外を除外
        if "/files/46/diary/" not in src:
            continue

        if src in seen:
            continue

        seen.add(src)
        images.append(src)

    return images
