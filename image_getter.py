import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_images(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    images = []

    for img in soup.find_all("img"):
        src = img.get("src")

        if not src:
            continue

        src = urljoin(url, src)

        if src not in images:
            images.append(src)

    return images
