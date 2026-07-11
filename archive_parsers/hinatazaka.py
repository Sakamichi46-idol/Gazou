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

BASE_URL = "https://www.hinatazaka46.com"
# 💡 ページ指定用のベースURL
BLOG_LIST_BASE_URL = "https://www.hinatazaka46.com/s/official/diary/member/list?page={page}"


async def get_max_page(session):
    """
    💡 日向坂46ブログの一覧から、一番最後のページ番号（最古のページ）を自動取得する関数
    """
    try:
        # 1ページ目（page=0）を読み込んで全体のページャーを確認する
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(BLOG_LIST_BASE_URL.format(page=0), headers=HEADERS, timeout=timeout) as response:
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
        
        max_page = 0
        # ページネーションのリンク（「最後へ」や数字のボタン）をすべて探す
        # 日向坂のUIは .c-pager__item a などが使われています
        for a in soup.select(".c-pager__item a[href]"):
            href = a.get("href")
            parsed = urlparse(href)
            queries = parse_qs(parsed.query)
            page_val = queries.get("page")
            if page_val:
                p_num = int(page_val[0])
                if p_num > max_page:
                    max_page = p_num
        
        # ページャーが見つかればそれを返す。見つからなければ安全のためデフォルト値を返す
        return max_page if max_page > 0 else 850
    except Exception as e:
        print(f"日向坂最大ページ数取得エラー: {e}")
        return 850


async def get_blog_urls(session):
    """
    💡 【過去の過去・本当の最古対応】最古のページから順に巡回して全URLを取得する
    """
    urls = []
    
    # 一番古いページ番号を自動取得（例: 850）
    max_page = await get_max_page(session)
    print(f"日向坂46ブログの最古ページ番号: {max_page} から遡り巡回を開始します。")

    # 💡 最大ページ（過去）から 0ページ（最新）に向かって逆順でループを回す
    for page in range(max_page, -1, -1):
        url = BLOG_LIST_BASE_URL.format(page=page)
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

                if "/diary/detail/" in href:
                    target_url = urljoin(BASE_URL, href)
                    if target_url not in page_urls and target_url not in urls:
                        page_urls.append(target_url)
            
            # 💡 1つのページ内は「新着順」で並んでいるため、
            # ページ内のURL一覧を逆順（古い順）にして全体のリストに追加する
            page_urls.reverse()
            urls.extend(page_urls)
            
            print(f"日向坂一覧ページ(page={page})のURL抽出完了（現在合計: {len(urls)}件）")
            
            # 💡 連続リクエストでサーバーに負荷をかけないよう、しっかり待機を入れる
            await asyncio.sleep(1.0)
            
        except Exception as e:
            print(f"日向坂一覧ページ(page={page})取得エラー: {e}")
            continue

    return urls


async def get_blog_list(session):
    """
    日向坂46ブログ全件取得（最古から順にページ内データを解析）
    """
    # 💡 過去から順に並んだ全URLを取得
    urls = await get_blog_urls(session)
    blogs = []

    print(f"日向坂46の全ブログ記事（計 {len(urls)} 件）の詳細データ取得を開始します。")

    for url in urls:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, headers=HEADERS, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

            title = ""
            title_tag = soup.select_one(".c-blog-article__title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            member = ""
            member_tag = soup.select_one(".c-blog-article__name")
            if member_tag:
                member = member_tag.get_text(strip=True)

            date = ""
            date_tag = soup.select_one(".c-blog-article__date time")
            if date_tag:
                date = normalize_datetime(date_tag.get_text(strip=True))

            body = soup.select_one(".c-blog-article__text")
            text = str(body) if body else ""

            blogs.append(
                {
                    "group": "日向坂46",
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
            print("日向坂記事取得エラー:", url, e)

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
