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

BASE_URL = "https://www.nogizaka46.com"
MEMBER_LIST_URL = (
    "https://www.nogizaka46.com/"
    "s/n46/diary/MEMBER/list"
)

# 💡 session を受け取る非同期関数に変更
async def get_member_pages(session):
    """
    乃木坂46のメンバーブログ一覧URL取得
    """
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(MEMBER_LIST_URL, headers=HEADERS, timeout=timeout) as response:
        response.raise_for_status()
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")

    urls = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue

        if "/s/n46/diary/detail/" in href:
            url = urljoin(BASE_URL, href)
            if url not in urls:
                urls.append(url)

    return urls

# 💡 session を受け取る非同期関数に変更
async def get_blog_list(session):
    """
    乃木坂46ブログ記事URL一覧取得
    """
    # 💡 await をつけてURL一覧を取得
    urls = await get_member_pages(session)
    blogs = []

    for url in urls:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, headers=HEADERS, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

            title = ""
            title_tag = soup.select_one(".bd--hd__ttl")
            if title_tag:
                title = title_tag.get_text(strip=True)

            member = ""
            member_tag = soup.select_one(".bd--hd__name")
            if member_tag:
                member = member_tag.get_text(strip=True)

            date = ""
            date_tag = soup.select_one(".bd--hd__date")
            if date_tag:
                date = normalize_datetime(date_tag.get_text(strip=True))

            body = soup.select_one(".bd--article")
            text = str(body) if body else ""

            blogs.append(
                {
                    "group": "乃木坂46",
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
            print("乃木坂記事取得エラー:", url, e)

    return blogs

# 💡 非同期関数に変更
async def get_oldest_first():
    """
    古い記事順に並べ替える
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
