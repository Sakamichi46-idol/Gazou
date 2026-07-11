import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from archive_parsers.utils import normalize_datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# メンバーID(ct)と名前のキャッシュ
member_cache = {}

async def update_member_cache(session):
    """
    ブログ一覧ページを読み込み、メンバー選択のプルダウンからCt番号と名前の辞書を構築する
    """
    try:
        url = "https://www.nogizaka46.com/s/n46/diary/MEMBER/list"
        async with session.get(url, headers=HEADERS) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # メンバー選択セレクトボックスの option を全取得
            for option in soup.select("select.ba--mmsel__sel option"):
                href = option.get("value", "")
                if "ct=" in href:
                    ct = parse_qs(urlparse(href).query).get("ct", [None])[0]
                    # 名前の抽出（「名前(更新日)」の形式から名前だけ抜き出す）
                    raw_text = option.get_text().strip()
                    name = raw_text.split("(")[0].strip()
                    
                    if ct and name and "メンバー" not in name:
                        member_cache[ct] = name
            print(f"乃木坂46 メンバー辞書を更新: {len(member_cache)}名")
    except Exception as e:
        print(f"メンバー辞書更新エラー: {e}")

def get_member_from_url(url):
    """URLからCt番号を抽出し、辞書からメンバー名を返す"""
    # 記事URL自体に ct が含まれている場合と、そうでない場合の考慮
    parsed = urlparse(url)
    queries = parse_qs(parsed.query)
    ct = queries.get("ct", [None])[0]
    
    # ct が見つからない場合は、記事ページから別途取得するロジックが必要だが
    # 乃木坂のブログ一覧から取得する記事リストに ct が含まれているはず
    return member_cache.get(ct, "不明")

# --- 以下、既存のロジックに組み込む部分 ---

async def get_blog_list(session):
    # (既存のページ取得処理で urls を取得した後)
    urls = await get_member_pages(session) 
    blogs = []

    for url in urls:
        try:
            # 記事の詳細を取得
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

            # ★ここが重要：辞書からメンバー名を特定
            member = get_member_from_url(url)
            
            # 万が一「不明」だった場合のフォールバック（タイトルからの抽出）
            if member == "不明":
                title_tag = soup.select_one(".bd--hd__ttl")
                title = title_tag.get_text(strip=True) if title_tag else "タイトルなし"
                # ここに簡易的なタイトル末尾抽出を入れるのはアリ
                print(f"警告: {url} のメンバーが辞書に見つかりません。タイトル: {title}")

            # (以下、date, title, text の取得処理はそのまま)
            # ...

            blogs.append({
                "group": "乃木坂46",
                "url": url,
                "member": member,
                "title": title,
                "date": date,
                "text": text
            })
            await asyncio.sleep(0.8)
        except Exception as e:
            print("乃木坂記事取得エラー:", url, e)
    return blogs

async def get_oldest_first():
    async with aiohttp.ClientSession() as session:
        # 最初に辞書を自動生成
        await update_member_cache(session)
        blogs = await get_blog_list(session)

    blogs.sort(key=lambda x: x.get("date", ""))
    return blogs
