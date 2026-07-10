import requests
import json
import re


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    ),
    "Referer": "https://www.nogizaka46.com/"
}


def get_nogizaka_latest():

    url = (
        "https://www.nogizaka46.com"
        "/s/n46/api/list/blog"
    )


    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )


    print(
        "乃木坂 API STATUS:",
        response.status_code
    )


    response.raise_for_status()


    # JSONP → JSONへ変換
    text = response.text


    match = re.search(
        r"res\((.*)\)",
        text
    )


    if not match:
        print(
            "乃木坂API解析失敗"
        )
        return None


    data = json.loads(
        match.group(1)
    )


    if not data.get("data"):
        return None


    blog = data["data"][0]


    return {
        "group": "乃木坂46",
        "url": blog.get("link", ""),
        "member": blog.get("name", ""),
        "title": blog.get("title", ""),
        "date": blog.get("date", ""),
        "text": blog.get("text", "")
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
            results.append(blog)


    print("取得ブログ:", results)

    return results
