import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from parsers.utils import normalize_datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_hinatazaka_images(url):

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

    except Exception as e:
        print("日向坂取得エラー:", e)
        return {
            "group": "日向坂46",
            "member": "",
            "title": "",
            "date": "",
            "url": url,
            "images": []
        }


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    blog = {
        "group": "日向坂46",
        "member": "",
        "title": "",
        "date": "",
        "url": url,
        "images": []
    }


    # タイトル
    title = soup.find(
        "h1"
    )

    if title:
        blog["title"] = title.get_text(
            strip=True
        )


    # メンバー名
    member = soup.select_one(
        ".p-blog-article__name"
    )

    if not member:
        member = soup.select_one(
            ".c-blog-article__name"
        )


    if member:
        blog["member"] = member.get_text(
            strip=True
        )


    # 投稿日
    date = soup.find(
        "time"
    )

    if date:

        date_text = (
            date.get("datetime")
            or date.get_text(
                " ",
                strip=True
            )
        )

        blog["date"] = normalize_datetime(
            date_text
        )



    # 本文部分
    article = soup.select_one(
        ".c-blog-article__text"
    )


    if not article:
        article = soup


    seen = set()


    # 画像取得
    for img in article.find_all("img"):

        src = img.get("src")


        if not src:
            continue


        img_url = urljoin(
            url,
            src
        )


        # 日向坂ブログ画像のみ
        if "/files/14/diary/official/member/" not in img_url:
            continue


        # ロゴ除外
        if "logo" in img_url.lower():
            continue


        # 重複削除
        if img_url in seen:
            continue


        seen.add(img_url)


        blog["images"].append(
            img_url
        )


    print(
        f"日向坂画像数: {len(blog['images'])}"
    )


    return blog
