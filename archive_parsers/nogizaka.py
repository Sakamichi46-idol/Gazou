import re
import aiohttp

from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0"
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


    title = normalize_name(
        title
    )


    for name in MEMBER_NAMES:

        if name in title:
            return name



    member_name = normalize_name(
        member_name
    )


    for name in MEMBER_NAMES:

        if name == member_name:
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
        10
    ):


        url = (
            "https://www.nogizaka46.com/"
            "s/n46/diary/MEMBER"
            f"?page={page}&ima=2155"
        )


        try:

            async with session.get(
                url,
                headers=HEADERS,
                timeout=15
            ) as response:


                html = await response.text()



        except Exception as e:

            print(
                f"乃木坂取得エラー page={page}: {e}"
            )

            continue



        soup = BeautifulSoup(
            html,
            "html.parser"
        )
        print(
            "乃木坂HTML blog確認:",
            "bl--card" in html
        )


        posts = soup.select(
            "a.bl--card"
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



            title_tag = post.select_one(
                "p.bl--card__ttl"
            )


            date_tag = post.select_one(
                "p.bl--card__date"
            )



            if not title_tag:

                continue



            title = title_tag.get_text(
                strip=True
            )


            date = (
                date_tag.get_text(
                    strip=True
                )
                if date_tag
                else ""
            )



            blog_url = urljoin(
                BASE_URL,
                href
            )



            member = detect_member(
                "",
                title
            )



            # タイトルから判定できない場合は後で詳細ページ解析用
            if not member:

                member = "不明"



            blogs.append(
                {

                    "group":
                        "乃木坂46",

                    "url":
                        blog_url,

                    "member":
                        member,

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
