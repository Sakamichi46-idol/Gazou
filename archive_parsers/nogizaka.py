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


BASE_URL = "https://www.nogizaka46.com"

BLOG_LIST_URL = (
    "https://www.nogizaka46.com/s/n46/diary/MEMBER?page={page}"
)


# ==========================
# メンバー対応表
# ==========================

MEMBER_CT_MAP = {

    "55396": "五百城茉央",
    "55397": "池田瑛紗",
    "55390": "一ノ瀬美空",

    "36749": "伊藤理々杏",
    "55389": "井上和",
    "36750": "岩本蓮加",

    "48006": "遠藤さくら",
    "63102": "大越ひなの",
    "55401": "岡本姫奈",

    "55392": "小川彩",
    "55394": "奥田いろは",
    "63103": "小津玲奈",

    "63104": "海邉朱莉",

    "48008": "賀喜遥香",
    "48010": "金川紗耶",

    "55400": "川﨑桜",
    "63105": "川端晃菜",

    "55383": "黒見明香",

    "48013": "柴田柚菜",
    "55391": "菅原咲月",

    "63106": "鈴木佑捺",
    "63107": "瀬戸口心月",

    "48015": "田村真佑",
    "48017": "筒井あやめ",

    "55393": "冨里奈央",
    "63108": "長嶋凛桜",

    "55395": "中西アルノ",

    "55385": "林瑠奈",

    "63109": "増田三莉音",
    "63110": "森平麗心",

    "63111": "矢田萌華",

    "55387": "弓木奈於",

    "36759": "吉田綾乃クリスティー"
}



# ==========================
# 期別
# ==========================

GROUP_CT_MAP = {

    "40004": "3期生",
    "40005": "4期生",
    "40001": "新4期生",
    "40007": "5期生",
    "40008": "6期生"

}



# ==========================
# 除外対象
# ==========================

STAFF_CT_LIST = {

    "40003"

}



# ==========================
# ct取得
# ==========================

def get_ct_from_url(url):

    parsed = urlparse(url)

    query = parse_qs(
        parsed.query
    )


    ct = query.get(
        "ct"
    )


    if ct:
        return ct[0]


    return None



# ==========================
# メンバー判定
# ==========================

def get_member_name(ct, title):


    if not ct:
        return "不明"



    # 運営スタッフ
    if ct in STAFF_CT_LIST:

        return None



    # 個人ブログ

    if ct in MEMBER_CT_MAP:

        return MEMBER_CT_MAP[ct]



    # 期別ブログ

    if ct in GROUP_CT_MAP:


        clean_title = (
            title
            .replace(" ", "")
            .replace("　", "")
        )


        for member in MEMBER_CT_MAP.values():


            clean_member = (
                member
                .replace(" ", "")
                .replace("　", "")
            )


            if clean_member in clean_title:

                return member



        # タイトルで特定できなかった場合
        return GROUP_CT_MAP[ct]



    return "不明"



# ==========================
# 詳細ページ取得
# ==========================

async def get_blog_detail(
    session,
    url
):

    blog = {

        "group": "乃木坂46",
        "url": url,
        "member": "不明",
        "title": "",
        "date": ""

    }


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



        title_tag = soup.select_one(
            "h1"
        )


        if title_tag:

            blog["title"] = (
                title_tag
                .get_text(strip=True)
            )



        date_tag = soup.select_one(
            "p.bd--hd__date"
        )


        if date_tag:

            blog["date"] = normalize_datetime(
                date_tag.get_text(strip=True)
            )



        ct = get_ct_from_url(
            url
        )


        member = get_member_name(
            ct,
            blog["title"]
        )


        # 運営スタッフ除外

        if member is None:

            return None



        blog["member"] = member



    except Exception as e:

        print(
            "乃木坂詳細取得エラー:",
            url,
            e
        )


    return blog



# ==========================
# URL取得
# ==========================

async def get_blog_urls(session):

    urls = []


    for page in range(1, 20):

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



            for a in soup.select(
                "a.m--postone__a"
            ):


                href = a.get(
                    "href"
                )


                if not href:

                    continue



                full_url = urljoin(
                    BASE_URL,
                    href
                )



                if full_url not in urls:

                    urls.append(
                        full_url
                    )



        except Exception as e:

            print(
                "乃木坂一覧取得エラー:",
                e
            )


    return urls



# ==========================
# 最古順取得
# ==========================

async def get_oldest_first():


    async with aiohttp.ClientSession() as session:


        urls = await get_blog_urls(
            session
        )


        blogs = []


        for url in urls:


            blog = await get_blog_detail(
                session,
                url
            )


            if blog:

                blogs.append(
                    blog
                )



    blogs.sort(
        key=lambda x: x.get(
            "date",
            ""
        )
    )


    print(
        f"乃木坂46取得件数: {len(blogs)}"
    )


    return blogs
