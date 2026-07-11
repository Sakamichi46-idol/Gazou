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

def format_sakurazaka_date(date_text):
    """
    櫻坂46ブログの日付文字列を 'YYYY年MM月DD日 HH:MM' に確実に整形する関数
    入力例: '2026.7.11 20:30' や '2026/07/11 20:30:15'、'2026年07月11日 20:30' などに対応
    """
    if not date_text:
        return "不明"
        
    # 余分な空白を削除
    clean_text = date_text.strip()
    
    # 数字をすべて抽出 (年, 月, 日, 時, 分)
    nums = re.findall(r'\d+', clean_text)
    
    if len(nums) >= 5:
        year = nums[0]
        month = nums[1].zfill(2)  # 1桁なら0埋め
        day = nums[2].zfill(2)
        hour = nums[3].zfill(2)
        minute = nums[4].zfill(2)
        return f"{year}年{month}月{day}日 {hour}:{minute}"
        
    return clean_text

def get_sakurazaka_images(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )
    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "lxml"
    )

    blog = {
        "group": "櫻坂46",
        "member": "",
        "title": "",
        "date": "",
        "url": url,
        "images": []
    }

    # =====================
    # メンバー名
    # =====================
    member_tag = soup.select_one(".name")
    if member_tag:
        blog["member"] = member_tag.get_text(strip=True)

    # =====================
    # タイトル
    # =====================
    title_tag = soup.select_one(".title")
    if title_tag:
        blog["title"] = title_tag.get_text(" ", strip=True)

    # =====================
    # 💡 日付・時間 (直接フォーマット整形関数を通すように修正)
    # =====================
    date_tag = soup.select_one(".date")
    if date_tag:
        raw_date = date_tag.get_text(strip=True)
        blog["date"] = format_sakurazaka_date(raw_date)

    # =====================
    # 本文（画像の抽出範囲）
    # =====================
    article = (
        soup.select_one(".box-article")
        or
        soup.select_one(".blog-body")
        or
        soup.find("article")
    )

    if article is None:
        article = soup

    # =====================
    # 画像取得
    # =====================
    seen = set()

    for img in article.find_all("img"):
        src = (
            img.get("src")
            or
            img.get("data-src")
            or
            img.get("data-original")
        )

        if not src:
            continue

        image_url = urljoin(url, src)

        # ロゴ・アイコン除外
        if any(
            x in image_url.lower()
            for x in ["logo", "icon", "header", "footer"]
        ):
            continue

        # 櫻坂ブログ画像判定
        if "/files/" not in image_url or "diary" not in image_url:
            continue

        if image_url in seen:
            continue

        seen.add(image_url)
        blog["images"].append(image_url)

    print(
        f"櫻坂ブログ解析完了: {blog['member']} - {blog['title']} [{blog['date']}] (画像: {len(blog['images'])}枚)"
    )

    return blog
