import yt_dlp
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_images(url):

    # InstagramなどSNS
    if (
        "instagram.com" in url
        or "twitter.com" in url
        or "x.com" in url
        or "tiktok.com" in url
    ):
        return get_social_images(url)

    # 普通のサイト
    return get_html_images(url)



def get_social_images(url):

    options = {
        "quiet": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

    images = []

    if "entries" in info:

        for item in info["entries"]:
            if item.get("url"):
                images.append(item["url"])

    elif info.get("url"):
        images.append(info["url"])

    return images



def get_html_images(url):

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    res = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    soup = BeautifulSoup(
        res.text,
        "html.parser"
    )

    images = []

    # og:image優先
    og = soup.find(
        "meta",
        property="og:image"
    )

    if og:
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

    return list(dict.fromkeys(images))
