import asyncio
import aiohttp
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

# 💡 session を受け取る非同期関数に変更
async def get_blog_urls(session):
    """
    日向坂46ブログURL一覧取得
    """
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(BLOG_LIST_URL, headers=HEADERS, timeout=timeout) as response:
        response.raise_for_status()
        html = await response.text()
        # 環境によってlxmlがない場合を考慮しhtml.parserにしてありますが、lxmlのままで良ければ戻してください
        soup = BeautifulSoup(html, "html.parser")

    urls = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue

        if "/diary/detail/" in href:
            url = urljoin(BASE_URL, href)
            if url not in urls:
                urls.append(url)

    return urls

# 💡 session を受け取る非同期関数に変更
async def get_blog_list(session):
    """
    日向坂46ブログ一覧取得
    """
    # 💡 await をつけてURL一覧を取得
    urls = await get_blog_urls(session)
    blogs = []

    for url in urls:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, headers=HEADERS, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

            title = ""
            title_tag = soup.select_one(".c-blog-article__title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            member = ""
            member_tag = soup.select_one(".c-blog-article__name")
            if member_tag:
                member = member_tag.get_text(strip=True)

            date = ""
            date_tag = soup.select_one(".c-blog-article__date time")
            if date_tag:
                date = normalize_datetime(date_tag.get_text(strip=True))

            body = soup.select_one(".c-blog-article__text")
            text = str(body) if body else ""

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

            # 💡 サーバー負荷軽減のためのウェイト
            await asyncio.sleep(0.5)

        except Exception as e:
            print("日向坂記事取得エラー:", url, e)

    return blogs

# 💡 非同期関数に変更
async def get_oldest_first():
    """
    古い順に並び替え
    """
    # 💡 セッションを作成して使い回す
    async with aiohttp.ClientSession() as session:
        blogs = await get_blog_list(session)

    blogs.sort(
        key=lambda x: x.get(
            "date",
            ""
        )
    )

    return blogs
