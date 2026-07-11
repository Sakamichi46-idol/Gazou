import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}

BASE_URL = "https://sakurazaka46.com"
BLOG_LIST_URL = "https://sakurazaka46.com/s/s46/diary/blog/list"

def format_sakurazaka_date(date_text):
    """
    日付文字列を 'YYYY年MM月DD日 HH:MM' に確実に整形する関数
    """
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

def get_sakurazaka_images(url):
    """
    【新着Bot準拠】指定されたURLのブログ詳細ページから、
    メンバー名、タイトル、正しい投稿日時、画像一覧を取得する
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
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

    # =====================
    # タイトル取得
    # =====================
    title = soup.find("h1", class_="title")
    if not title:
        title = soup.find("h1")
    if title:
        blog["title"] = title.get_text(strip=True)

    # =====================
    # メンバー名・投稿日時取得（.blog-foot から確実に取得）
    # =====================
    blog_foot = soup.find(class_="blog-foot")
    if blog_foot:
        # メンバー名
        member = blog_foot.find("p", class_="name")
        if member:
            blog["member"] = member.get_text(strip=True)

        # 投稿日時（ここが「11」になるのを防ぐため、詳細ページのフルな日時を取得）
        date = blog_foot.find("p", class_="date")
        if date:
            raw_date = date.get_text(" ", strip=True)
            blog["date"] = format_sakurazaka_date(raw_date)

    # =====================
    # 本文（画像抽出用）
    # =====================
    article = (
        soup.find(class_="box-article")
        or soup.find(class_="bd--edit")
        or soup.find("article")
        or soup.find("main")
    )
    if article is None:
        article = soup

    # =====================
    # 画像取得
    # =====================
    seen = set()
    for img in article.find_all("img"):
        src = img.get("src")
        if not src:
            continue

        image_url = urljoin(url, src)

        # 櫻坂ブログ画像判定
        if "/files/" not in image_url:
            continue

        if image_url in seen:
            continue

        seen.add(image_url)
        blog["images"].append(image_url)

    return blog

def get_blog_urls():
    """
    櫻坂46ブログの最新URL一覧を記事一覧ページから取得
    """
    try:
        response = requests.get(BLOG_LIST_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"櫻坂一覧取得エラー: {e}")
        return []

    urls = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if "/diary/detail/" in href:
            url = urljoin(BASE_URL, href)
            if url not in urls:
                urls.append(url)
    return urls

def get_oldest_first():
    """
    archive_checker.py から呼ばれるメイン関数。
    新着URLを洗い出し、それぞれ詳細ページを見に行って正しい日時を取得し、古い順に並び替える。
    """
    urls = get_blog_urls()
    blogs = []

    for url in urls:
        # 詳細ページを見に行って正しい日時やメンバー名を取得する
        blog_data = get_sakurazaka_images(url)
        blogs.append({
            "group": blog_data["group"],
            "url": blog_data["url"],
            "member": blog_data["member"],
            "title": blog_data["title"],
            "date": blog_data["date"]
        })

    # 正しい日時を使って古い順にソート
    blogs.sort(key=lambda x: x.get("date", ""))
    return blogs
