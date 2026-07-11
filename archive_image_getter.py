import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}

NG_WORDS = [
    "logo",
    "icon",
    "sprite",
    "favicon",
    "loading",
    "header",
    "footer",
    "banner"
]

# 💡 非同期関数に変更
async def get_images(url):
    """
    ブログ記事内画像取得
    """
    try:
        # 💡 aiohttpのセッションを作成し、タイムアウトを設定してリクエスト
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
                # 環境に合わせた一般的なパーサーに変更（lxmlのままでも動作します）
                soup = BeautifulSoup(html, "html.parser")

        images = []

        # 本文内画像優先
        article = (
            soup.select_one(".bd--article")
            or soup.select_one(".box-article")
            or soup.select_one(".c-blog-article__text")
        )

        target = article if article else soup

        for img in target.select("img"):
            src = img.get("src")
            if not src:
                continue

            image_url = urljoin(url, src)
            lower = image_url.lower()

            if any(word in lower for word in NG_WORDS):
                continue

            if not any(ext in lower for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                continue

            if image_url not in images:
                images.append(image_url)

        print("取得画像:", len(images), url)
        return images

    except Exception as e:
        print("画像取得エラー:", e)
        return []
