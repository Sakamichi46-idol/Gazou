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

    # 全ての空白を削除
    text = re.sub(
        r"\s+",
        "",
        text
    )

    return text



# =========================
# メンバー判定
# =========================

def detect_member(
    member_name,
    title
):

    # 運営スタッフ除外

    if "運営スタッフ" in member_name:
        return None


    normalized_title = normalize_name(
        title
    )


    # タイトルから判定

    for name in MEMBER_NAMES:

        if name in normalized_title:
            return name



    # 表示名から判定

    normalized_member = normalize_name(
        member_name
    )


    for name in MEMBER_NAMES:

        if normalized_member == name:
            return name



    return None



# =========================
# ブログ取得
# =========================

async def get_all_blog_urls(
    session
):

    blogs = []


    # ページ数拡大
    for page in range(
        1,
        10
    ):


        url = (
            f"https://www.nogizaka46.com/"
            f"s/n46/diary/MEMBER?page={page}"
        )


        try:

            async with session.get(
                url,
                headers=HEADERS
            ) as response:


                html = await response.text()


        except Exception as e:

            print(
                "乃木坂一覧取得エラー:",
                e
            )

            continue



        soup = BeautifulSoup(
            html,
            "html.parser"
        )



        posts = soup.select(
            "div.m--postone"
        )


        print(
            f"乃木坂 page={page} 記事数:",
            len(posts)
        )



        for post in posts:


            a_tag = post.select_one(
                "a.m--postone__a"
            )


            name_tag = post.select_one(
                "p.m--postone__name"
            )


            title_tag = post.select_one(
                "p.m--postone__ttl"
            )


            time_tag = post.select_one(
                "p.m--postone__time"
            )



            if not (
                a_tag
                and title_tag
                and time_tag
            ):
                continue



            blog_url = urljoin(
                BASE_URL,
                a_tag["href"]
            )



            raw_member = (
                name_tag.get_text(strip=True)
                if name_tag
                else ""
            )



            title = title_tag.get_text(
                strip=True
            )



            # デバッグ確認

            print(
                "DEBUG:",
                raw_member,
                "|",
                title
            )



            member = detect_member(
                raw_member,
                title
            )



            if not member:

                print(
                    "判定失敗:",
                    raw_member,
                    "|",
                    title
                )

                continue



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
                        time_tag.get_text(
                            strip=True
                        )
                }
            )



    print(
        "乃木坂取得件数:",
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
