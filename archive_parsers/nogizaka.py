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
    """メンバー一覧ページからブログURLに絞ってメンバー辞書を構築"""
    try:
        # メンバー一覧ページ
        url = "https://www.nogizaka46.com/s/n46/artist"
        async with session.get(url, headers=HEADERS) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # 絞り込み: "/diary/MEMBER/list?ct=" を含み、かつ "HANDSHAKE" を含まないリンクのみ
            # これでミーグリ等のイベント系リンクを除外してメンバーだけを抽出します
            links = soup.select("a[href*='/diary/MEMBER/list?ct=']")
            
            count = 0
            for link in links:
                href = link.get("href", "")
                if "HANDSHAKE" in href:
                    continue
                
                query = urlparse(href).query
                ct = parse_qs(query).get("ct", [None])[0]
                
                # リンクテキストをメンバー名として取得
                name = link.get_text(strip=True)
                
                if ct and name:
                    member_cache[ct] = name
                    count += 1
                    # デバッグ用に最初の数名だけ表示
                    if count <= 5:
                        print(f"[デバッグ] メンバーを登録: {name} (ct={ct})")
        
        print(f"乃木坂46 メンバー辞書を更新: {len(member_cache)}名")
    except Exception as e:
        print(f"メンバー辞書更新エラー: {e}")

async def get_all_blog_urls(session):
    """全ブログ記事のURLを収集する"""
    print("乃木坂46 全ブログ記事URLを収集します...")
    # ここに各メンバーのctを使って記事一覧を叩くロジックが必要です
    urls = []
    return urls

async def get_blog_list(session):
    # 1. メンバー辞書を更新
    await update_member_cache(session)
    
    # 2. 全URLを取得
    urls = await get_all_blog_urls(session)
    
    blogs = []
    for url in urls:
        try:
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

            ct = parse_qs(urlparse(url).query).get("ct", [None])[0]
            member = member_cache.get(ct, "不明")

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
