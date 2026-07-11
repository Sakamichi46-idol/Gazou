import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from archive_parsers.utils import normalize_datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

member_cache = {}

async def update_member_cache(session):
    """メンバー一覧ページから全メンバー情報を抽出して辞書を構築"""
    try:
        url = "https://www.nogizaka46.com/s/n46/artist"
        async with session.get(url, headers=HEADERS) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # 乃木坂のメンバー詳細（ブログ）へのリンクをすべて取得
            # リンクのhrefに '/diary/MEMBER/list?' が含まれるものを全抽出
            links = soup.find_all("a", href=lambda x: x and "/diary/MEMBER/list?" in x)
            
            for link in links:
                href = link.get("href", "")
                # リンク内のテキストを名前として取得（タグが入れ子の場合を考慮）
                name = link.get_text(strip=True)
                
                # ctパラメータを抽出
                query = urlparse(href).query
                ct = parse_qs(query).get("ct", [None])[0]
                
                # ctがあり、かつ名前が空でない場合のみ登録
                if ct and name and "HANDSHAKE" not in href:
                    member_cache[ct] = name
                    
        print(f"乃木坂46 メンバー辞書を更新: {len(member_cache)}名")
        # 登録された全メンバーを確認用に出力
        for ct, name in member_cache.items():
            print(f"  - {name} (ct={ct})")
            
    except Exception as e:
        print(f"メンバー辞書更新エラー: {e}")

async def get_all_blog_urls(session):
    """全ブログ記事のURLを収集する"""
    print("乃木坂46 全ブログ記事URLを収集します...")
    return []

async def get_blog_list(session):
    await update_member_cache(session)
    urls = await get_all_blog_urls(session)
    return []

async def get_oldest_first():
    async with aiohttp.ClientSession() as session:
        blogs = await get_blog_list(session)
    return blogs
