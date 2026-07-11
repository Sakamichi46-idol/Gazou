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
    """メンバーリストからCt番号と名前の辞書を構築"""
    try:
        url = "https://www.nogizaka46.com/s/n46/diary/MEMBER/list"
        async with session.get(url, headers=HEADERS) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # クラス名に依存せず、select内のoptionを全取得して判定
            for option in soup.select("select option"):
                href = option.get("value", "")
                if "ct=" in href:
                    ct = parse_qs(urlparse(href).query).get("ct", [None])[0]
                    name = option.get_text().split("(")[0].strip()
                    if ct and name and "メンバー" not in name:
                        member_cache[ct] = name
        print(f"乃木坂46 メンバー辞書を更新: {len(member_cache)}名")
    except Exception as e:
        print(f"メンバー辞書更新エラー: {e}")

async def get_all_blog_urls(session):
    """全ブログ記事のURLを収集する"""
    urls = []
    # ここは、君の環境にある「乃木坂の全記事URLを取得するロジック」を記述してください
    # もし全URL取得関数が別にあるならそれを呼び出し、なければここで行う
    print("全ブログ記事URLを収集します...")
    # (例: 一覧ページを順次巡回して urls に追加する処理)
    return urls

async def get_blog_list(session):
    # 1. メンバー辞書を更新
    await update_member_cache(session)
    
    # 2. 全URLを取得 (get_member_pagesの代わり)
    urls = await get_all_blog_urls(session)
    
    blogs = []
    for url in urls:
        try:
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

            # ★URLのCt番号から辞書引き
            ct = parse_qs(urlparse(url).query).get("ct", [None])[0]
            member = member_cache.get(ct, "不明")

            # タイトルと日付
            title_tag = soup.select_one(".bd--hd__ttl")
            title = title_tag.get_text(strip=True) if title_tag else "タイトルなし"
            
            date_tag = soup.select_one(".bd--hd__date")
            date = normalize_datetime(date_tag.get_text(strip=True)) if date_tag else ""

            body = soup.select_one(".bd--article")
            text = str(body) if body else ""

            blogs.append({
                "group": "乃木坂46",
                "url": url,
                "member": member,
                "title": title,
                "date": date,
                "text": text
            })
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"記事取得エラー: {url} - {e}")
    return blogs

async def get_oldest_first():
    async with aiohttp.ClientSession() as session:
        blogs = await get_blog_list(session)
    blogs.sort(key=lambda x: x.get("date", ""))
    return blogs
