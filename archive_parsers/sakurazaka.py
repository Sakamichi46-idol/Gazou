import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from parsers.utils import normalize_datetime


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}


def get_sakurazaka_images(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "lxml"  # 💡 精度向上のため新着Botと同じくlxml（またはhtml.parser）を使用
    )


    blog = {
        "group": "櫻坂46",
        "member": "",
        "title": "",
        "date": "",
        "url": url,
        "images": []
    }


    # =====================
    # 💡 メンバー名（新着Botの構造に修正）
    # =====================
    member_tag = soup.select_one(".name")
    if member_tag:
        blog["member"] = member_tag.get_text(strip=True)


    # =====================
    # 💡 タイトル（新着Botの構造に修正）
    # =====================
    title_tag = soup.select_one(".title")
    if title_tag:
        blog["title"] = title_tag.get_text(" ", strip=True)


    # =====================
    # 💡 日付・時間（新着Botの構造に修正＋時間も含むよう対応）
    # =====================
    date_tag = soup.select_one(".date")
    if date_tag:
        blog["date"] = normalize_datetime(date_tag.get_text(strip=True))


    # =====================
    # 本文（画像の抽出範囲）
    # =====================
    article = (
        soup.select_one(".box-article")
        or
        soup.select_one(".blog-body")
        or
        soup.find("article")
    )

    if article is None:
        article = soup



    # =====================
    # 画像取得
    # =====================
    seen = set()

    for img in article.find_all("img"):

        src = (
            img.get("src")
            or
            img.get("data-src")
            or
            img.get("data-original")
        )

        if not src:
            continue

        image_url = urljoin(url, src)

        # ロゴ・アイコン除外
        if any(
            x in image_url.lower()
            for x in [
                "logo",
                "icon",
                "header",
                "footer"
            ]
        ):
            continue

        # 櫻坂ブログ画像判定
        if (
            "/files/" not in image_url
            or
            "diary" not in image_url
        ):
            continue

        if image_url in seen:
            continue

        seen.add(image_url)
        blog["images"].append(image_url)


    print(
        f"櫻坂ブログ解析完了: {blog['member']} - {blog['title']} (画像: {len(blog['images'])}枚)"
    )


    return blog
