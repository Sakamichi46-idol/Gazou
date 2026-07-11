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
    """ブログリストページのプルダウンからメンバー辞書を構築"""
    try:
        # メンバーブログ一覧ページ
        url = "https://www.nogizaka46.com/s/n46/diary/MEMBER/list"
        async with session.get(url, headers=HEADERS) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # ページ内のすべてのoptionタグを抽出
            options = soup.select("select option")
            print(f"[デバッグ] 見つかったoptionタグの数: {len(options)}")
            
            for opt in options:
                val = opt.get("value", "")
                name = opt.get_text(strip=True)
                
                # ログに出力して中身を確認
                print(f"[デバッグ] option解析: name='{name}', value='{val}'")
                
                # ctパラメータを持ち、かつ無効な選択肢を除外して辞書に登録
                if "ct=" in val:
                    ct = parse_qs(urlparse(val).query).get("ct", [None])[0]
                    # 除外条件：グループ名そのものや「選択してください」などを排除
                    if ct and "メンバー" not in name and "選択" not in name and "乃木坂" not in name:
                        member_cache[ct] = name
        
        print(f"乃木坂46 メンバー辞書を更新: {len(member_cache)}名")
    except Exception as e:
        print(f"メンバー辞書更新エラー: {e}")

async def get_all_blog_urls(session):
    """全ブログ記事のURLを収集する"""
    print("乃木坂46 全ブログ記事URLを収集します...")
    # ここにメンバーごとのページを回るロジックが必要です
    return []

async def get_blog_list(session):
    await update_member_cache(session)
    urls = await get_all_blog_urls(session)
    blogs = []
    # 記事取得ロジック
    return blogs

async def get_oldest_first():
    async with aiohttp.ClientSession() as session:
        blogs = await get_blog_list(session)
    blogs.sort(key=lambda x: x.get("date", ""))
    return blogs
