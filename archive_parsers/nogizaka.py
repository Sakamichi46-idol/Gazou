import asyncio
from urllib.parse import urlparse, parse_qs

# メンバー辞書（ハードコード）
MEMBER_CT_MAP = {
    "55396": "五百城 茉央", "55397": "池田 瑛紗", "55390": "一ノ瀬 美空",
    "36749": "伊藤 理々杏", "55389": "井上 和", "36750": "岩本 蓮加",
    "48006": "遠藤 さくら", "63102": "大越 ひなの", "55401": "岡本 姫奈",
    "55392": "小川 彩", "55394": "奥田 いろは", "63103": "小津 玲奈",
    "63104": "海邉 朱莉", "48008": "賀喜 遥香", "48010": "金川 紗耶",
    "55400": "川﨑 桜", "63105": "川端 晃菜", "55383": "黒見 明香",
    "48013": "柴田 柚菜", "55391": "菅原 咲月", "63106": "鈴木 佑捺",
    "63107": "瀬戸口 心月", "48015": "田村 真佑", "48017": "筒井 あやめ",
    "55393": "冨里 奈央", "63108": "長嶋 凛桜", "55395": "中西 アルノ",
    "55385": "林 瑠奈", "63109": "増田 三莉音", "63110": "森平 麗心",
    "63111": "矢田 萌華", "55387": "弓木 奈於", "36759": "吉田 綾乃クリスティー"
}

# 期生グループID
GROUP_CT_MAP = {
    "40004": "３期生", "40005": "４期生", 
    "40001": "新4期生", "40007": "5期生", "40008": "6期生"
}

member_cache = {}

async def update_member_cache(session=None):
    """固定の辞書データでキャッシュを更新"""
    member_cache.clear()
    member_cache.update(MEMBER_CT_MAP)
    member_cache.update(GROUP_CT_MAP)
    print(f"乃木坂46 辞書を固定値で更新: {len(member_cache)}件")

def get_member_name_from_blog(ct, title):
    """
    ctに基づきメンバー名を判定。
    期生グループの場合はタイトルから名前を抽出する。
    """
    # 運営スタッフ(40003)は除外
    if ct == "40003":
        return None
    
    # 個人ブログの場合
    if ct in MEMBER_CT_MAP:
        return MEMBER_CT_MAP[ct]
    
    # 期生ブログの場合、タイトルからメンバー名を検索
    if ct in GROUP_CT_MAP:
        for name in MEMBER_CT_MAP.values():
            if name in title:
                return name
                
    return None

async def get_blog_list(session):
    await update_member_cache(session)
    # 記事取得の巡回ロジックをここに実装
    blogs = []
    # 例: 記事を取得した際に以下のように判定する
    # name = get_member_name_from_blog(ct, blog_title)
    # if name: ...
    return blogs

async def get_oldest_first():
    # 実行用メイン関数
    return []
