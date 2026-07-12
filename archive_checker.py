import traceback
import aiohttp

from archive_parsers.nogizaka import (
    get_oldest_first as get_nogizaka
)
from archive_parsers.sakurazaka import (
    get_oldest_first as get_sakurazaka
)
from archive_parsers.hinatazaka import (
    get_oldest_first as get_hinatazaka
)

# =========================
# パーサー一覧
# =========================

PARSERS = {
    "乃木坂46": get_nogizaka,
    "櫻坂46": get_sakurazaka,
    "日向坂46": get_hinatazaka,
}

# =========================
# 全ブログ取得
# =========================

async def get_all_blogs():

    blogs = []

    async with aiohttp.ClientSession() as session:

        for group, parser in PARSERS.items():

            print(f"[{group}] 巡回開始")

            try:

                result = await parser(session)

                if result:

                    blogs.extend(result)

                    print(f"[{group}] {len(result)}件取得")

                else:

                    print(f"[{group}] 記事なし")

            except Exception as e:

                print(f"{group}取得エラー: {e}")

                traceback.print_exc()

    # ===== 全グループまとめて時系列順 =====
    blogs.sort(
        key=lambda x: x.get("date", "")
    )

    print(f"全グループ合計: {len(blogs)}件")

    return blogs[:20]

# =========================
# archive_main用
# =========================

async def get_archive_targets():

    return await get_all_blogs()
