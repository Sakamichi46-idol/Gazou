import re
import aiohttp

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


BASE_URL = "https://www.nogizaka46.com"


# =========================
# メンバー辞書
# =========================

MEMBER_NAMES = [

    "五百城茉央",
    "池田瑛紗",
    "一ノ瀬美空",
    "伊藤理々杏",
    "井上和",
    "岩本蓮加",
    "遠藤さくら",
    "大越ひなの",
    "岡本姫奈",
    "小川彩",
    "奥田いろは",
    "賀喜遥香",
    "金川紗耶",
    "川﨑桜",
    "黒見明香",
    "柴田柚菜",
    "菅原咲月",
    "鈴木佑捺",
    "瀬戸口心月",
    "田村真佑",
    "筒井あやめ",
    "冨里奈央",
    "長嶋凛桜",
    "中西アルノ",
    "林瑠奈",
    "増田三莉音",
    "森平麗心",
    "矢田萌華",
    "弓木奈於",
    "吉田綾乃クリスティー"

]


# =========================
# 名前正規化
# =========================

def normalize_name(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        "",
        text
    )


# =========================
# メンバー判定
# =========================

def detect_member(
    member_name,
    title
):

    if "運営スタッフ" in member_name:
        return None


    title = normalize_name(title)


    for name in MEMBER_NAMES:

        if name in title:
            return name


    member_name = normalize_name(
        member_name
    )


    for name in MEMBER_NAMES:

        if name in member_name:
            return name


    return None



# =========================
# ブログ取得
# =========================

async def get_all_blog_urls(
    session
):

    blogs = []


    for page in range(
        1,
        143
    ):

        url = (
            "https://www.nogizaka46.com/"
            "s/n46/diary/MEMBER"
            f"?ima=1123&page={page}"
        )


        try:

            async with session.get(
                url,
                headers=HEADERS,
                timeout=20

            ) as response:

                html = await response.text()


        except Exception as e:

            print(
                f"乃木坂取得エラー page={page}: {e}"
            )

            continue



        # =====================
        # HTML確認
        # =====================

        print(
            "取得HTML m--postone数:",
            html.count(
                "m--postone__a"
            )
        )



        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        blog_area = soup.select_one(
            ".ba--all"
        )


        print(
            f"乃木坂HTML blog確認: {blog_area is not None}"
        )



        # =====================
        # 記事取得
        # =====================

        posts = soup.select(
            "a[href*='/diary/detail/']"
        )


        print(
            f"乃木坂 page={page} 記事数: {len(posts)}"
        )



        for post in posts:


            href = post.get(
                "href"
            )


            if not href:
                continue



            blog_url = urljoin(
                BASE_URL,
                href
            )



            title_tag = post.select_one(
                ".m--postone__ttl"
            )


            date_tag = post.select_one(
                ".m--postone__time"
            )


            member_tag = post.select_one(
                ".m--postone__name"
            )



            title = (
                title_tag.get_text(
                    strip=True
                )
                if title_tag
                else ""
            )



            date = (
                date_tag.get_text(
                    strip=True
                )
                if date_tag
                else ""
            )



            member = (
                member_tag.get_text(
                    strip=True
                )
                if member_tag
                else ""
            )



            detected_member = detect_member(
                member,
                title
            )



            if not detected_member:

                detected_member = (
                    normalize_name(member)
                    or
                    "不明"
                )



            blogs.append(
                {

                    "group":
                        "乃木坂46",

                    "url":
                        blog_url,

                    "member":
                        detected_member,

                    "title":
                        title,

                    "date":
                        date

                }
            )



    print(
        f"乃木坂URL取得: {len(blogs)}"
    )


    return blogs



# =========================
# archive_checker用
# =========================

async def get_oldest_first(
    session
):

    blogs = await get_all_blog_urls(
        session
    )


    blogs.sort(
        key=lambda x:
            x.get(
                "date",
                ""
            )
    )


    return blogs
