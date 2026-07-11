import aiohttp
import re
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}


# =========================
# メンバー対応表
# =========================

MEMBER_CT_MAP = {

    "55396": "五百城 茉央",
    "55397": "池田 瑛紗",
    "55390": "一ノ瀬 美空",

    "36749": "伊藤 理々杏",
    "55389": "井上 和",
    "36750": "岩本 蓮加",

    "48006": "遠藤 さくら",
    "63102": "大越 ひなの",

    "55401": "岡本 姫奈",
    "55392": "小川 彩",
    "55394": "奥田 いろは",

    "63103": "小津 玲奈",
    "63104": "海邉 朱莉",

    "48008": "賀喜 遥香",
    "48010": "金川 紗耶",

    "55400": "川﨑 桜",
    "63105": "川端 晃菜",

    "55383": "黒見 明香",

    "48013": "柴田 柚菜",

    "55391": "菅原 咲月",

    "63106": "鈴木 佑捺",
    "63107": "瀬戸口 心月",

    "48015": "田村 真佑",
    "48017": "筒井 あやめ",

    "55393": "冨里 奈央",
    "63108": "長嶋 凛桜",

    "55395": "中西 アルノ",

    "55385": "林 瑠奈",

    "63109": "増田 三莉音",
    "63110": "森平 麗心",

    "63111": "矢田 萌華",

    "55387": "弓木 奈於",

    "36759": "吉田 綾乃クリスティー"
}



# =========================
# 期生名
# =========================

GROUP_CT_MAP = {

    "40004": "３期生",
    "40005": "４期生",
    "40001": "新4期生",
    "40007": "5期生",
    "40008": "6期生"

}



# =========================
# 名前比較用
# =========================

def normalize_name(text):

    if not text:
        return ""

    # 空白類を全部削除
    return re.sub(
        r"\s+",
        "",
        text
    )



# =========================
# タイトルから本人判定
# =========================

def detect_member_from_title(title):

    normalized_title = normalize_name(title)


    for member in MEMBER_CT_MAP.values():

        normalized_member = normalize_name(member)


        if normalized_member in normalized_title:

            return member


    return None



# =========================
# 名前取得
# =========================

def get_member_name(display_name, title):


    # 運営スタッフは除外
    if "運営" in display_name:
        return None


    # 普通のメンバー名
    for member in MEMBER_CT_MAP.values():

        if normalize_name(member) == normalize_name(display_name):

            return member



    # 期生表示の場合
    if display_name in GROUP_CT_MAP.values():

        return detect_member_from_title(title)



    # 判定不能
    return None



# =========================
# ブログ取得
# =========================

async def get_all_blog_urls(session):


    print(
        "[デバッグ] 乃木坂46 記事収集開始..."
    )


    all_blogs = []


    for page in range(1, 3):


        url = (
            "https://www.nogizaka46.com/"
            f"s/n46/diary/MEMBER?page={page}"
        )


        try:

            async with session.get(
                url,
                headers=HEADERS
            ) as resp:


                html = await resp.text()


            soup = BeautifulSoup(
                html,
                "html.parser"
            )


            posts = soup.select(
                "div.m--postone"
            )


            if not posts:

                print(
                    f"{page}ページ目 記事なし"
                )

                continue



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
                    and name_tag
                    and title_tag
                    and time_tag
                ):

                    continue



                post_url = a_tag.get(
                    "href"
                )


                if post_url.startswith("/"):

                    post_url = (
                        "https://www.nogizaka46.com"
                        + post_url
                    )



                display_name = name_tag.get_text(
                    strip=True
                )


                title = title_tag.get_text(
                    strip=True
                )


                date = time_tag.get_text(
                    strip=True
                )



                member = get_member_name(
                    display_name,
                    title
                )


                # 運営スタッフや判定不能は除外
                if not member:

                    print(
                        f"除外: {display_name} - {title}"
                    )

                    continue



                all_blogs.append(
                    {
                        "group": "乃木坂46",
                        "url": post_url,
                        "date": date,
                        "title": title,
                        "member": member
                    }
                )


                print(
                    f"取得成功: {member} - {title}"
                )



        except Exception as e:

            print(
                "乃木坂取得エラー:",
                e
            )



    print(
        f"[デバッグ] 乃木坂46 収集完了 {len(all_blogs)}件"
    )


    return all_blogs
