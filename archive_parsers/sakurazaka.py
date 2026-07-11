import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}

BASE_URL = "https://sakurazaka46.com"
BLOG_LIST_BASE_URL = "https://sakurazaka46.com/s/s46/diary/blog/list?ima=0000&page={page}"

def format_sakurazaka_date(date_text):
    if not date_text:
        return "不明"
    clean_text = date_text.strip()
    nums = re.findall(r'\d+', clean_text)
    if len(nums) >= 5:
        year = nums[0]
        month = nums[1].zfill(2)
        day = nums[2].zfill(2)
        hour = nums[3].zfill(2)
        minute = nums[4].zfill(2)
        return f"{year}年{month}月{day}日 {hour}:{minute}"
    return clean_text

# 💡 session を引数で受け取る非同期関数に変更
async def get_sakurazaka_images(session, url):
    try:
        # aiohttpでのタイムアウト指定（接続・読み込みの合計を10秒に制限）
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(url, headers=HEADERS, timeout=timeout) as response:
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(f"櫻坂個別ページ取得エラー: {url} {e}")
        return {"group": "櫻坂46", "member": "", "title": "", "date": "不明", "url": url, "images": []}

    blog = {
        "group": "櫻坂46",
        "member": "",
        "title": "",
        "date": "不明",
        "url": url,
        "images": []
    }

    title = soup.find("h1", class_="title")
    if not title:
        title = soup.find("h1")
    if title:
        blog["title"] = title.get_text(strip=True)

    blog_foot = soup.find(class_="blog-foot")
    if blog_foot:
        member = blog_foot.find("p", class_="name")
        if member:
            blog["member"] = member.get_text(strip=True)

        date = blog_foot.find("p", class_="date")
        if date:
            raw_date = date.get_text(" ", strip=True)
            blog["date"] = format_sakurazaka_date(raw_date)

    article = (
        soup.find(class_="box-article")
        or soup.find(class_="bd--edit")
        or soup.find("article")
        or soup.find("main")
    )
    if article is None:
        article = soup

    seen = set()
    for img in article.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        image_url = urljoin(url, src)
        if "/files/" not in image_url:
            continue
        if image_url in seen:
            continue
        seen.add(image_url)
        blog["images"].append(image_url)

    return blog

# 💡 非同期関数に変更
async def get_max_page(session):
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(BLOG_LIST_BASE_URL.format(page=0), headers=HEADERS, timeout=timeout) as response:
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
        
        max_page = 0
        for a in soup.select(".com-pager a[href]"):
            href = a.get("href")
            parsed = urlparse(href)
            queries = parse_qs(parsed.query)
            page_val = queries.get("page")
            if page_val:
                p_num = int(page_val[0])
                if p_num > max_page:
                    max_page = p_num
        
        return max_page if max_page > 0 else 381
    except Exception as e:
        print(f"最大ページ数取得エラー: {e}")
        return 381

# 💡 非同期関数に変更
async def get_blog_urls(session):
    urls = []
    
    # 💡 await をつけて呼び出す
    max_page = await get_max_page(session)
    print(f"櫻坂46ブログの最古ページ番号: {max_page} から遡り巡回を開始します。")

    for page in range(max_page, -1, -1):
        url = BLOG_LIST_BASE_URL.format(page=page)
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, headers=HEADERS, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
            
            page_urls = []
            for a in soup.find_all("a", href=True):
                href = a.get("href")
                if "/diary/detail/" in href:
                    target_url = urljoin(BASE_URL, href)
                    if target_url not in page_urls and target_url not in urls:
                        page_urls.append(target_url)
            
            page_urls.reverse()
            urls.extend(page_urls)
            
            # 💡 連続リクエストでサーバーに負荷をかけないよう、非同期の sleep を入れる
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"櫻坂一覧ページ(page={page})取得エラー: {e}")
            continue

    return urls

async def get_oldest_first():

    blogs = []


    async with aiohttp.ClientSession() as session:


        urls = await get_blog_urls(
            session
        )


        for url in urls:


            blog_data = await get_sakurazaka_images(
                session,
                url
            )


            blogs.append(
                {
                    "group": blog_data["group"],
                    "url": blog_data["url"],
                    "member": blog_data["member"],
                    "title": blog_data["title"],
                    "date": blog_data["date"]
                }
            )


            await asyncio.sleep(
                0.5
            )



    blogs.sort(
        key=lambda x: x.get(
            "date",
            ""
        )
    )


    return blogs
