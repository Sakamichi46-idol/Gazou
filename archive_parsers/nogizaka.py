import aiohttp
from bs4 import BeautifulSoup

# 定数設定
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

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

GROUP_CT_MAP = {
    "40004": "３期生", "40005": "４期生", 
    "40001": "新4期生", "40007": "5期生", "40008": "6期生"
}

member_cache = {}

async def update_member_cache(session=None):
    member_cache.clear()
    member_cache.update(MEMBER_CT_MAP)
    member_cache.update(GROUP_CT_MAP)
    print(f"[デバッグ] 乃木坂46 辞書更新完了。全{len(member_cache)}件")

def get_member_name_from_blog(ct, title):
    if ct == "40003": return None
    if ct in MEMBER_CT_MAP: return MEMBER_CT_MAP[ct]
    if ct in GROUP_CT_MAP:
        for name in MEMBER_CT_MAP.values():
            if name in title: return name
    return None

async def get_all_blog_urls(session):
    print("[デバッグ] 乃木坂46 記事収集開始...")
    all_blogs = []
    
    # ページングを考慮（必要に応じて範囲を調整してください）
    for page in range(1, 3): 
        url = f"https://www.nogizaka46.com/s/n46/diary/MEMBER?page={page}"
        try:
            async with session.get(url, headers=HEADERS) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                
                # [重要] js-apiblog-list に依存せず、ページ全体から直接記事ブロックを探す
                posts = soup.select("div.m--postone")
                
                if not posts:
                    print(f"[デバッグ] {page}ページ目で記事が見つかりませんでした。")
                    continue
                
                for post in posts:
                    # 各要素を確実に取得
                    a_tag = post.select_one("a.m--postone__a")
                    name_tag = post.select_one("p.m--postone__name")
                    title_tag = post.select_one("p.m--postone__ttl")
                    time_tag = post.select_one("p.m--postone__time")
                    
                    if a_tag and name_tag and title_tag and time_tag:
                        post_url = a_tag.get("href")
                        # 相対パスなら補完
                        if post_url.startswith("/"):
                            post_url = "https://www.nogizaka46.com" + post_url
                            
                        member_name = name_tag.get_text(strip=True)
                        post_title = title_tag.get_text(strip=True)
                        post_time = time_tag.get_text(strip=True)
                        
                        all_blogs.append({
                            "url": post_url,
                            "date": post_time,
                            "title": post_title,
                            "member": member_name
                        })
                        
                        # ログで確認用
                        print(f"取得成功: {member_name} - {post_title}")
                        
        except Exception as e:
            print(f"エラー発生: {e}")
            
    print(f"[デバッグ] 乃木坂46 収集完了。総数: {len(all_blogs)}件")
    return all_blogs
