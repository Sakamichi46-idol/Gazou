import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# 定数設定
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

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
    print(f"[デバッグ] 乃木坂46 辞書更新完了。全{len(member_cache)}件")

def get_member_name_from_blog(ct, title):
    """ctとタイトルからメンバー名を判定"""
    if ct == "40003": return None  # 運営は除外
    
    # 個人ブログの場合
    if ct in MEMBER_CT_MAP:
        return MEMBER_CT_MAP[ct]
    
    # 期生ブログの場合、タイトルからメンバー名を検索
    if ct in GROUP_CT_MAP:
        for name in MEMBER_CT_MAP.values():
            if name in title:
                return name
    return None

async def get_all_blog_urls(session):
    """全ブログ記事のURLを収集する"""
    print("[デバッグ] 乃木坂46 記事収集開始...")
    all_blogs = []
    
    for ct, name in member_cache.items():
        if ct == "40003": continue # 運営除外
            
        url = f"https://www.nogizaka46.com/s/n46/diary/MEMBER/list?ct={ct}"
        try:
            async with session.get(url, headers=HEADERS) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                
                # 記事一覧の取得
                posts = soup.select("div.m--postone")
                for post in posts:
                    a_tag = post.select_one("a.m--postone__a")
                    time_tag = post.select_one("p.m--postone__time")
                    title_tag = post.select_one("p.m--postone__ttl")
                    
                    if a_tag and time_tag and title_tag:
                        post_url = a_tag.get("href")
                        post_time = time_tag.get_text(strip=True)
                        post_title = title_tag.get_text(strip=True)
                        
                        target_name = get_member_name_from_blog(ct, post_title)
                        if target_name:
                            all_blogs.append({
                                "url": post_url,
                                "date": post_time,
                                "title": post_title,
                                "member": target_name
                            })
        except Exception as e:
            print(f"エラー: {name} の取得中にエラー発生: {e}")
            
    return all_blogs

async def get_blog_list(session):
    """辞書更新と記事取得を実行"""
    await update_member_cache(session)
    return await get_all_blog_urls(session)

async def get_oldest_first():
    """他モジュールから呼び出されるエントリーポイント"""
    async with aiohttp.ClientSession() as session:
        return await get_blog_list(session)
