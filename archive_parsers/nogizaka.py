import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

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
# 💡 乃木坂用のカウント指定ベースURL（ct=0, 20, 40... と20刻みで過去に遡る）
MEMBER_LIST_BASE_URL = "https://www.nogizaka46.com/s/n46/diary/MEMBER/list?ct={ct}"


async def get_max_ct(session):
    """
    💡 乃木坂46ブログの一覧から、一番最後のページ位置（最古のctカウント）を自動取得・計算する関数
    """
    try:
        # 1ページ目（ct=0）を読み込んで全体のページャーを確認する
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(MEMBER_LIST_BASE_URL.format(ct=0), headers=HEADERS, timeout=timeout) as response:
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
        
        max_ct = 0
        # 乃木坂のページャー要素（.pos a など）から最大の ct パラメータを探す
        for a in soup.select(".pos a[href]"):
            href = a.get("href")
            parsed = urlparse(href)
            queries = parse_qs(parsed.query)
            ct_val = queries.get("ct")
            if ct_val:
                c_num = int(ct_val[0])
                if c_num > max_ct:
                    max_ct = c_num
        
        # 20の倍数に丸めて安全なデフォルト値を設定（見つからない場合は仮で 55000 など）
        if max_ct > 0:
            return (max_ct // 20) * 20
        return 55000
    except Exception as e:
        print(f"乃木坂最大カウント数取得エラー: {e}")
        return 55000


async def get_member_pages(session):
    """
    💡 【過去の過去・本当の最古対応】最古のct位置から順に20刻みで遡り全URLを取得する
    """
    urls = []
    
    # 一番古いカウント数を自動計算（例: 56240）
    max_ct = await get_max_ct(session)
    print(f"乃木坂46ブログの最古カウント: ct={max_ct} から遡り巡回を開始します。")

    # 💡 最大カウント（過去）から 0（最新）に向かって 20 ずつ減らしながらループを回す
    for ct in range(max_ct, -1, -20):
        url = MEMBER_LIST_BASE_URL.format(ct=ct)
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, headers=HEADERS, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
            
            page_urls = []
            for a in soup.select("a[href]"):
                href = a.get("href")
                if not href:
                    continue

                if "/s/n46/diary/detail/" in href:
                    target_url = urljoin(BASE_URL, href)
                    if target_url not in page_urls and target_url not in urls:
                        page_urls.append(target_url)
            
            # 💡 ページ内は「新着順」で上から並んでいるため、
            # ページ内のURL一覧を逆順（古い順）にして全体のリストに追加する
            page_urls.reverse()
            urls.extend(page_urls)
            
            print(f"乃木坂一覧ページ(ct={ct})のURL抽出完了（現在合計: {len(urls)}件）")
            
            # 💡 連続リクエストでサーバーに負荷をかけないよう、しっかり待機を入れる
            await asyncio.sleep(1.0)
            
        except Exception as e:
            print(f"乃木坂一覧ページ(ct={ct})取得エラー: {e}")
            continue

    return urls


async def get_blog_list(session):
    """
    乃木坂46ブログ全件取得（最古から順にページ内データを解析）
    """
    # 💡 過去から順に並んだ全URLを取得
    urls = await get_member_pages(session)
    blogs = []

    print(f"乃木坂46の全ブログ記事（計 {len(urls)} 件）の詳細データ取得を開始します。")

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

            # 💡 サーバー負荷軽減のために1件ごとにしっかり待つ
            await asyncio.sleep(0.8)

        except Exception as e:
            print("乃木坂記事取得エラー:", url, e)

    return blogs


async def get_oldest_first():
    """
    完全に最古から順に並んだブログデータのリストを返す
    """
    async with aiohttp.ClientSession() as session:
        blogs = await get_blog_list(session)

    # 日付文字列ベースでも昇順（古い順）ソートをかけて安全性を担保
    blogs.sort(key=lambda x: x.get("date", ""))
    return blogs
