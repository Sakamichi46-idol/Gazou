import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


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
        "https://www.nogizaka46.com/"
        "s/n46/diary/MEMBER?ima=3331"
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
        "乃木坂 STATUS:",
        response.status_code
    )

    print(
        "乃木坂 URL:",
        response.url
    )


    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )
    print(
        "m--postone:",
        len(soup.find_all(class_="m--postone"))
    )

    print(
        "detail:",
        len(
            soup.find_all(
                href=True
            )
        )
    )
    
    print(
        "ba--all:",
        soup.find(class_="ba--all")
    )

    post = soup.find(
        "a",
        class_="m--postone__a"
    )


    print(
        "乃木坂 post:",
        post
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


    blog_url = post.get(
        "href"
    )


    if blog_url:
        blog_url = urljoin(
            url,
            blog_url
        )


    return {
        "group": "乃木坂46",
        "url": blog_url,
        "member": (
            member.get_text(strip=True)
            if member else ""
        ),
        "title": (
            title.get_text(strip=True)
            if title else ""
        ),
        "date": (
            date.get_text(strip=True)
            if date else ""
        )
    }



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
