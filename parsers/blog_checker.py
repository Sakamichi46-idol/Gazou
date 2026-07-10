import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


BLOG_LISTS = {
    "乃木坂46": "https://www.nogizaka46.com/s/n46/diary/member/list",
    "櫻坂46": "https://sakurazaka46.com/s/s46/diary/member/list",
    "日向坂46": "https://www.hinatazaka46.com/s/official/diary/member/list"
}


def get_latest_blog():

    results = []


    for group, url in BLOG_LISTS.items():

        try:
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


            link = soup.find(
                "a",
                href=True
            )


            if link:

                blog_url = urljoin(
                    url,
                    link["href"]
                )

                results.append({
                    "group": group,
                    "url": blog_url
                })


        except Exception as e:

            print(
                group,
                "取得エラー:",
                e
            )


    return results
