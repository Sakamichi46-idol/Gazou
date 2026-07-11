import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
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
    指定されたURLのブログから詳細情報と画像一覧を取得する（アーカイブ用）
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
    except Exception as e:
        print(f"櫻坂個別ページ取得エラー: {url} {e}")
        return {"group": "櫻坂46", "member": "", "title": "", "date": "", "url": url, "images": []}

    blog = {
        "group": "櫻坂46",
        "member": "",
        "title": "",
        "date": "",
        "url": url,
        "images": []
    }

    # メンバー名
    member_tag = soup.select_one(".name")
    if member_tag:
        blog["member"] = member_tag.get_text(strip=True)

    # タイトル
    title_tag = soup.select_one(".title")
    if title_tag:
        blog["title"] = title_tag.get_text(" ", strip=True)

    # 日付・時間 (〇〇年〇〇月〇〇日 〇〇:◯◯ に整形)
    date_tag = soup.select_one(".date")
    if date_tag:
        blog["date"] = format_sakurazaka_date(date_tag.get_text(strip=True))

    # 本文（画像抽出用）
    article = soup.select_one(".box-article") or soup.select_one(".blog-body") or soup.find("article")
    if article is None:
        article = soup

    # 画像取得
    seen = set()
    for img in article.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src:
            continue

        image_url = urljoin(url, src)

        if any(x in image_url.lower() for x in ["logo", "icon", "header", "footer"]):
            continue

        if "/files/" not in image_url or "diary" not in image_url:
            continue

        if image_url in seen:
            continue

        seen.add(image_url)
        blog["images"].append(image_url)

    return blog

def get_blog_urls():
    """
    櫻坂46ブログURL一覧取得
    """
    try:
        response = requests.get(BLOG_LIST_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
    except Exception as e:
        print(f"櫻坂一覧取得エラー: {e}")
        return []

    urls = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue

        if "/diary/detail/" in href:
            url = urljoin(BASE_URL, href)
            if url not in urls:
                urls.append(url)
    return urls

# 💡 【重要】archive_checker.py が呼び出している関数を復活させました！
def get_oldest_first():
    """
    ブログ一覧を取得し、古い順に並び替えて返す（archive_checker用）
    """
    urls = get_blog_urls()
    blogs = []

    for url in urls:
        blog_data = get_sakurazaka_images(url)
        # 必要なキー構造を担保して追加
        blogs.append({
            "group": blog_data["group"],
            "url": blog_data["url"],
            "member": blog_data["member"],
            "title": blog_data["title"],
            "date": blog_data["date"]
        })

    # 古い順にソート
    blogs.sort(key=lambda x: x.get("date", ""))
    return blogs
