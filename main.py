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

    title = ""
    member = ""
    date = ""

    # タイトル
    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # メンバー
    member_tag = soup.find(class_="bd--prof__name")
    if member_tag:
        member = member_tag.get_text(strip=True)

    # 投稿日
    date_tag = soup.find(class_="bd--hd__date")
    if date_tag:
        date = date_tag.get_text(strip=True)

    # 本文
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

        if "/files/46/diary/" not in src:
            continue

        if src in seen:
            continue

        seen.add(src)
        images.append(src)

    return {
        "title": title,
        "member": member,
        "date": date,
        "images": images
    }
