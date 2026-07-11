import re
import aiohttp

from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent":
        "Mozilla/5.0"
}


BASE_URL = "https://www.nogizaka46.com"


# =========================
# メンバー名一覧
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
    "小津玲奈",
    "海邉朱莉",
    "賀喜遥香",
    "金川紗耶",
    "川﨑桜",
    "川端晃菜",
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

    # 全角・半角スペース除去
    text = re.sub(
        r"\s+",
        "",
        text
    )

    return text



# =========================
# メンバー判定
# =========================

def detect_member(title):

    if not title:
        return None


    normalized = normalize_name(
        title
    )


    for name in MEMBER_NAMES:

        if name in normalized:
            return name


    return None



# =========================
# ブログURL取得
# =========================

async def get_all_blog_urls(session):

    blogs = []


    # 現在の乃木坂ブログ一覧
    for page in range(1, 10):

        url = (
            "https://www.nogizaka46.com/"
            f"s/n46/diary/MEMBER?ima=2155&page={page}"
        )


        try:

            async with session.get(
                url,
                headers=HEADERS
            ) as response:

                html = await response.text()



        except Exception as e:

            print(
                "乃木坂ページ取得エラー:",
                e
            )

            continue



        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        posts = soup.select(
            "a.bl--card"
        )


        print(
            f"乃木坂 page={page} 記事数:",
            len(posts)
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



            member = detect_member(
                title
            )



            # 判定不能は除外
            if not member:

                continue



            date = ""

            if date_tag:

                date = date_tag.get_text(
                    strip=True
                )



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
                "取得:",
                member,
                title
            )



    print(
        "乃木坂URL取得:",
        len(blogs)
    )


    return blogs



# =========================
# archive_checker用
# =========================

async def get_oldest_first():

    async with aiohttp.ClientSession() as session:

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
