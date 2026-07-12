import asyncio
import traceback
from datetime import datetime

import aiohttp

from archive_database import filter_not_archived

from archive_parsers.nogizaka import (
    get_oldest_first as get_nogizaka
)

from archive_parsers.sakurazaka import (
    get_oldest_first as get_sakurazaka
)

from archive_parsers.hinatazaka import (
    get_oldest_first as get_hinatazaka
)


PARSERS = {

    "乃木坂46": get_nogizaka,

    "櫻坂46": get_sakurazaka,

    "日向坂46": get_hinatazaka

}


# =========================
# 日付変換
# =========================

def parse_datetime(date_str):

    try:

        return datetime.strptime(
            date_str,
            "%Y年%m月%d日 %H:%M"
        )

    except Exception:

        return datetime.min


# =========================
# 全取得
# =========================

async def get_all_blogs():

    async with aiohttp.ClientSession() as session:

        tasks = [

            parser(session)

            for parser in PARSERS.values()

        ]

        results = await asyncio.gather(

            *tasks,

            return_exceptions=True

        )

    blogs = []

    for group, result in zip(

        PARSERS.keys(),

        results

    ):

        if isinstance(result, Exception):

            print(f"{group}取得失敗")

            traceback.print_exception(result)

            continue

        print(f"{group}: {len(result)}件")

        blogs.extend(result)

    print(f"取得合計: {len(blogs)}件")

    return blogs


# =========================
# archive_main用
# =========================

async def get_archive_targets():

    blogs = await get_all_blogs()

    print("DB照合中...")

    blogs = filter_not_archived(blogs)

    print(f"未保存: {len(blogs)}件")

    blogs.sort(

        key=lambda x: parse_datetime(

            x["date"]

        )

    )

    return blogs
