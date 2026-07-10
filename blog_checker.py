import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_nogizaka_latest():

    url = "https://www.nogizaka46.com/s/n46/diary/MEMBER"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    post = soup.find(
        "a",
        class_="m--postone__a"
    )

    if not post:
        return None


    member = post.find(
        class_="m--postone__name"
    )

    title = post.find(
        class_="m--postone__ttl"
    )

    date = post.find(
        class_="m--postone__time"
    )


    return {
        "group": "乃木坂46",
        "url": post.get("href"),
        "member": member.get_text(strip=True)
            if member else "",
        "title": title.get_text(strip=True)
            if title else "",
        "date": date.get_text(strip=True)
            if date else ""
    }



def get_sakurazaka_latest():

    # ここに後で櫻坂用を書く

    return None



def get_hinatazaka_latest():

    # ここに後で日向坂用を書く

    return None
