import requests
import yt_dlp

from bs4 import BeautifulSoup


def get_media(url):

    result = []


    # まずyt-dlp
    try:

        result = get_ytdlp(url)

        if result:
            return result

    except Exception as e:

        print(
            "yt-dlp失敗:",
            e
        )


    # 次にHTML
    try:

        result = get_html(url)

        if result:
            return result

    except Exception as e:

        print(
            "HTML失敗:",
            e
        )


    return []



def get_ytdlp(url):

    options = {
        "quiet": True,
        "extract_flat": False,
        "skip_download": True,
    }


    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )


    medias = []


    # Instagramカルーセル
    if "entries" in info:

        for item in info["entries"]:

            if item.get("url"):

                medias.append(
                    item["url"]
                )


    # 単体投稿
    else:

        if info.get("url"):

            medias.append(
                info["url"]
            )


        if info.get("thumbnail"):

            medias.append(
                info["thumbnail"]
            )


    return medias



def get_html(url):

    headers = {

        "User-Agent":
        (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
        )

    }


    r = requests.get(
        url,
        headers=headers,
        timeout=15
    )


    soup = BeautifulSoup(
        r.text,
        "html.parser"
    )


    medias = []


    # Instagramでよく使われる
    meta_tags = [

        ("property", "og:image"),

        ("property", "og:image:url"),

        ("name", "twitter:image")

    ]


    for key, value in meta_tags:

        tag = soup.find(
            "meta",
            {key:value}
        )


        if tag and tag.get("content"):

            medias.append(
                tag["content"]
            )


    return list(
        dict.fromkeys(medias)
    )
