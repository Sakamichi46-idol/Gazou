import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import re


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.nogizaka46.com/"
}


def get_nogizaka_latest():

    url = (
        "https://www.nogizaka46.com"
        "/s/n46/api/list/blog"
    )


    session = requests.Session()

    session.headers.update(
        HEADERS
    )


    response = session.get(
        url,
        timeout=10
    )


    print(
        "乃木坂 API STATUS:",
        response.status_code
    )


    print(
        response.text[:500]
    )


    response.raise_for_status()


    text = response.text

    json_text = re.search(
        r"res\((.*)\)",
        text
    ).group(1)

    data = json.loads(json_text)


    print(data["data"][0])


    return None


def get_sakurazaka_latest():

    return None



def get_hinatazaka_latest():

    return None



def get_latest_blog():

    results = []


    blogs = [
        get_nogizaka_latest(),
        get_sakurazaka_latest(),
        get_hinatazaka_latest()
    ]


    for blog in blogs:

        if blog:
            results.append(
                blog
            )


    return results
