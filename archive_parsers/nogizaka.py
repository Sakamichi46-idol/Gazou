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
    """HTML構造に最適化したメンバー辞書構築ロジック"""
    try:
        url = "https://www.nogizaka46.com/s/n46/diary/MEMBER/list"
        async with session.get(url, headers=HEADERS) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # ご提示いただいた構造に基づき div.ba--mmsel__pc__one を抽出
            member_divs = soup.select("div.ba--mmsel__pc__one")
            
            # 除外対象のリスト
            exclude_names = ["運営スタッフ", "３期生", "４期生", "新4期生", "5期生", "6期生"]
            
            for div in member_divs:
                a_tag = div.select_one("a.ba--mmsel__pc__a")
                p_tag = div.select_one("p.ba--mmsel__pc__neme")
                
                if a_tag and p_tag:
                    href = a_tag.get("href", "")
                    name = p_tag.get_text(strip=True)
                    
                    # ct番号を抽出
                    query = urlparse(href).query
                    ct = parse_qs(query).get("ct", [None])[0]
                    
                    # メンバーのみを辞書に登録
                    if ct and name and name not in exclude_names:
                        member_cache[ct] = name
            
            print(f"乃木坂46 メンバー辞書を更新: {len(member_cache)}名")
            for ct, name in member_cache.items():
                print(f"  [登録] {name} (ct={ct})")
                
    except Exception as e:
        print(f"メンバー辞書更新エラー: {e}")

async def get_all_blog_urls(session):
    """全ブログ記事のURLを収集する"""
    # 実際にはここに各メンバーのブログリストを巡回するロジックが入ります
    return []

async def get_blog_list(session):
    await update_member_cache(session)
    urls = await get_all_blog_urls(session)
    return []

async def get_oldest_first():
    async with aiohttp.ClientSession() as session:
        return await get_blog_list(session)
