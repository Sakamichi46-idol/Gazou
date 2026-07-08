import requests
import yt_dlp

from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0 Safari/537.36"
    )
}


def get_media(url):
    """
    URLから画像URL一覧を取得
    """

    images = []

    # InstagramなどSNSはyt-dlpを優先
    if any(site in url for site in [
        "instagram.com",
        "x.com",
        "twitter.com",
        "tiktok.com"
    ]):

        try:
            images = get_social_media(url)

            if images:
                return images

        except Exception as e:
            print(f"yt-dlp Error: {e}")

    # 通常サイト
    return get_html_images(url)


def get_social_media(url):

    options = {
        "quiet": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(url, download=False)

    images = []

    # カルーセル
    if info.get("entries"):

        for entry in info["entries"]:

            if entry.get("thumbnail"):
                images.append(entry["thumbnail"])

            elif entry.get("url"):
                images.append(entry["url"])

    else:

        if info.get("thumbnail"):
            images.append(info["thumbnail"])

        elif info.get("url"):
            images.append(info["url"])

    return list(dict.fromkeys(images))


def get_html_images(url):

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

    # ---------- og:image ----------
    for prop in [
        "og:image",
        "og:image:url",
        "twitter:image"
    ]:

        tag = soup.find(
            "meta",
            attrs={"property": prop}
        )

        if tag and tag.get("content"):
            images.append(tag["content"])

        tag = soup.find(
            "meta",
            attrs={"name": prop}
        )

        if tag and tag.get("content"):
            images.append(tag["content"])

    # ---------- imgタグ ----------
    for img in soup.find_all("img"):

        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
        )

        if src:
            images.append(
                urljoin(url, src)
            )

    # 重複削除
    images = list(dict.fromkeys(images))

    print("取得画像数:", len(images))

    return images
