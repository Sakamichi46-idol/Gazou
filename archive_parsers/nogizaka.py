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
    """メンバー一覧ページからリンクを全走査して辞書を構築（デバッグ用）"""
    try:
        url = "https://www.nogizaka46.com/s/n46/artist"
        print(f"[デバッグ] 接続先: {url}")
        async with session.get(url, headers=HEADERS) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # 全リンクを抽出して「ct=」が含まれるものを確認
            all_links = soup.find_all("a", href=True)
            ct_links = [a for a in all_links if "ct=" in a.get("href", "")]
            
            print(f"[デバッグ] ページ内のリンク総数: {len(all_links)}")
            print(f"[デバッグ] ct=を含むリンク数: {len(ct_links)}")
            
            for link in ct_links:
                href = link.get("href", "")
                name = link.get_text(strip=True)
                
                # ミーグリや無関係なリンクを除外
                if "HANDSHAKE" in href or "ticket" in href or not name:
                    continue
                
                query = urlparse(href).query
                ct = parse_qs(query).get("ct", [None])[0]
                
                if ct:
                    member_cache[ct] = name
            
            # デバッグ用に全件表示してみる
            for ct, name in member_cache.items():
                print(f"[デバッグ] 辞書登録: {name} (ct={ct})")
        
        print(f"乃木坂46 メンバー辞書を更新: {len(member_cache)}名")
    except Exception as e:
        print(f"メンバー辞書更新エラー: {e}")

async def get_all_blog_urls(session):
    """全ブログ記事のURLを収集する"""
    print("乃木坂46 全ブログ記事URLを収集します...")
    return []

async def get_blog_list(session):
    await update_member_cache(session)
    urls = await get_all_blog_urls(session)
    blogs = []
    for url in urls:
        # ... (既存ロジック)
        pass
    return blogs

async def get_oldest_first():
    async with aiohttp.ClientSession() as session:
        blogs = await get_blog_list(session)
    blogs.sort(key=lambda x: x.get("date", ""))
    return blogs
