import requests
import yt_dlp

from bs4 import BeautifulSoup
from urllib.parse import urljoin



def get_images(url):

    # SNS系
    if any(
        site in url
        for site in [
            "instagram.com",
            "x.com",
            "twitter.com",
            "tiktok.com"
        ]
    ):
        return get_social_images(url)

    # 普通のページ
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


    # 複数画像投稿
    if "entries" in info:

        for item in info["entries"]:

            if item.get("url"):
                images.append(
                    item["url"]
                )


    # 1枚投稿
    elif info.get("url"):

        images.append(
            info["url"]
        )


    return images



def get_html_images(url):

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }


    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )


    soup = BeautifulSoup(
        response.text,
        "lxml"
    )


    images = []


    # SNSや記事サイトでよく使われる画像
    og_image = soup.find(
        "meta",
        property="og:image"
    )


    if og_image:

        images.append(
            og_image["content"]
        )


    # imgタグ
    for img in soup.find_all("img"):

        src = img.get("src")

        if src:

            images.append(
                urljoin(url, src)
            )


    # 重複削除
    return list(dict.fromkeys(images))
