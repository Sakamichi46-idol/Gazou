import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


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
        print("日向坂画像取得エラー:", e)
        return []


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    # 本文部分
    article = soup.select_one(
        ".c-blog-article__text"
    )

    if not article:
        print("日向坂本文が見つかりません")
        return []


    images = []

    for img in article.find_all("img"):

        src = img.get("src")

        if not src:
            continue


        # 相対URL対応
        img_url = urljoin(
            url,
            src
        )


        # ロゴなど除外
        if "logo" in img_url.lower():
            continue


        images.append(img_url)


    # 重複削除
    images = list(
        dict.fromkeys(images)
    )


    print(
        f"日向坂画像数: {len(images)}"
    )

    for i in images:
        print(i)


    return images
