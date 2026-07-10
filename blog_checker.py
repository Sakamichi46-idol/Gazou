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


    result = {
        "group": "乃木坂46",
        "url": blog.get("link", ""),
        "member": blog.get("name", ""),
        "title": blog.get("title", ""),
        "date": blog.get("date", ""),
        "text": blog.get("text", "")
    }


    print(
        "乃木坂取得:",
        result
    )


    return result





def get_sakurazaka_latest():

    return None





def get_hinatazaka_latest():

    return None





def get_latest_blog():

    results = []


    for func in [
        get_nogizaka_latest,
        get_sakurazaka_latest,
        get_hinatazaka_latest
    ]:

        blog = func()


        if isinstance(blog, dict):

            results.append(blog)


        else:

            if blog is not None:
                print(
                    "想定外データ:",
                    blog,
                    type(blog)
                )



    print(
        "最終取得:",
        results
    )


    return results
