import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from archive_parsers.utils import normalize_datetime


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}


BASE_URL = "https://www.hinatazaka46.com"


BLOG_LIST_URL = (
    "https://www.hinatazaka46.com/"
    "s/official/diary/member/list"
)



def get_blog_urls():

    """
    日向坂46ブログURL一覧取得
    """

    response = requests.get(
        BLOG_LIST_URL,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "lxml"
    )


    urls = []


    for a in soup.select(
        "a[href]"
    ):

        href = a.get(
            "href"
        )


        if not href:
            continue


        if "/diary/detail/" in href:

            url = urljoin(
                BASE_URL,
                href
            )


            if url not in urls:

                urls.append(url)


    return urls




def get_blog_list():

    """
    日向坂46ブログ一覧取得
    """


    urls = get_blog_urls()


    blogs = []


    for url in urls:


        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=10
            )


            response.raise_for_status()


            soup = BeautifulSoup(
                response.text,
                "lxml"
            )



            title = ""


            title_tag = soup.select_one(
                ".c-blog-article__title"
            )


            if title_tag:

                title = title_tag.get_text(
                    strip=True
                )



            member = ""


            member_tag = soup.select_one(
                ".c-blog-article__name"
            )


            if member_tag:

                member = member_tag.get_text(
                    strip=True
                )



            date = ""


            date_tag = soup.select_one(
                ".c-blog-article__date time"
            )


            if date_tag:

                date = normalize_datetime(
                    date_tag.get_text(
                        strip=True
                    )
                )



            body = soup.select_one(
                ".c-blog-article__text"
            )


            text = (
                str(body)
                if body
                else ""
            )



            blogs.append(
                {
                    "group": "日向坂46",
                    "url": url,
                    "member": member,
                    "title": title,
                    "date": date,
                    "text": text
                }
            )


        except Exception as e:

            print(
                "日向坂記事取得エラー:",
                url,
                e
            )



    return blogs




def get_oldest_first():

    """
    古い順に並び替え
    """


    blogs = get_blog_list()


    blogs.sort(
        key=lambda x: x.get(
            "date",
            ""
        )
    )


    return blogs
