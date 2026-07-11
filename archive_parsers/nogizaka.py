import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from archive_parsers.utils import normalize_datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

member_cache = {}

async def update_member_cache(session):
    """メンバー一覧ページから全メンバーのCt番号と名前の辞書を構築（デバッグログ付き）"""
    try:
        url = "https://www.nogizaka46.com/s/n46/artist"
        async with session.get(url, headers=HEADERS) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # すべてのリンクを走査
            all_links = soup.select("a")
            count = 0
            for link in all_links:
                href = link.get("href", "")
                if "ct=" in href:
                    ct = parse_qs(urlparse(href).query).get("ct", [None])[0]
                    name = link.get_text(strip=True)
                    
                    # 最初の20件をログに出して構造を確認
                    if count < 20:
                        print(f"[デバッグ] 検出リンク: 名前='{name}', href='{href}'")
                    
                    if ct and name and len(name) < 20:
                        member_cache[ct] = name
                    count += 1
        
        print(f"乃木坂46 メンバー辞書を更新: {len(member_cache)}名")
    except Exception as e:
        print(f"メンバー辞書更新エラー: {e}")

async def get_all_blog_urls(session):
    print("乃木坂46 全ブログ記事URLを収集します...")
    return []

async def get_blog_list(session):
    await update_member_cache(session)
    urls = await get_all_blog_urls(session)
    blogs = []
    for url in urls:
        # ... (既存の取得ロジック)
        pass
    return blogs

async def get_oldest_first():
    async with aiohttp.ClientSession() as session:
        blogs = await get_blog_list(session)
    blogs.sort(key=lambda x: x.get("date", ""))
    return blogs
