import re
import asyncio
import aiohttp

from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9"
}

BASE_URL = "https://www.nogizaka46.com"

BLOG_LIST_URL = (
    "https://www.nogizaka46.com/"
    "s/n46/diary/MEMBER?page={page}"
)


# =========================
# メンバー一覧
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

    return re.sub(
        r"\s+",
        "",
        text
    )



# =========================
# 作者判定
# =========================

def detect_member(text):

    normalized = normalize_name(
        text
    )


    for name in MEMBER_NAMES:

        if name in normalized:

            return name


    return None



# =========================
# 個別記事から作者取得
# =========================

async def get_blog_detail(
    session,
    url
):

    try:

        async with session.get(
            url,
            headers=HEADERS,
            timeout=10
        ) as response:

            html = await response.text()
            
            print(html[:500])


        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        # タイトル

        title = ""

        title_tag = soup.select_one(
            "h1"
        )

        if title_tag:

            title = title_tag.get_text(
                strip=True
            )



        # 作者取得

        member = None


        # 現在の乃木坂ブログ構造

        for selector in [
            ".bd--hd__name",
            ".m--blog__name",
            ".name",
            "p.name"
        ]:


            tag = soup.select_one(
                selector
            )

            if tag:

                member = detect_member(
                    tag.get_text(
                        " ",
                        strip=True
                    )
                )

                if member:
                    break



        # 作者欄で取れない場合
        # タイトルから判定

        if not member:

            member = detect_member(
                title
            )



        # 運営スタッフ除外

        if "運営スタッフ" in title:

            return None



        return {

            "group":
                "乃木坂46",

            "url":
                url,

            "member":
                member,

            "title":
                title,

        }


    except Exception as e:

        print(
            "乃木坂個別取得エラー:",
            url,
            e
        )

        return None



# =========================
# URL一覧取得
# =========================

async def get_blog_urls(
    session
):

    urls = []


    for page in range(
        1,
        1000
    ):


        url = BLOG_LIST_URL.format(
            page=page
        )


        try:

            async with session.get(
                url,
                headers=HEADERS,
                timeout=10
            ) as response:

                html = await response.text()



            soup = BeautifulSoup(
                html,
                "html.parser"
            )


            cards = soup.select(
                "a.bl--card"
            )


            print(
                f"乃木坂 page={page} 記事数:",
                len(cards)
            )


            if not cards:

                break



            for card in cards:


                href = card.get(
                    "href"
                )


                if not href:
                    continue



                blog_url = urljoin(
                    BASE_URL,
                    href
                )


                if blog_url not in urls:

                    urls.append(
                        blog_url
                    )



            await asyncio.sleep(
                0.5
            )


        except Exception as e:

            print(
                "乃木坂一覧取得エラー:",
                e
            )


    print(
        "乃木坂URL取得:",
        len(urls)
    )


    return urls



# =========================
# archive_checker用
# =========================

async def get_oldest_first():


    blogs = []


    async with aiohttp.ClientSession() as session:


        urls = await get_blog_urls(
            session
        )


        for url in urls:


            blog = await get_blog_detail(
                session,
                url
            )


            if blog:

                blogs.append(
                    blog
                )


            await asyncio.sleep(
                0.5
            )



    blogs.sort(
        key=lambda x:
            x.get(
                "date",
                ""
            )
    )


    return blogs
