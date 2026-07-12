import asyncio
import traceback

import aiohttp

from archive_config import (
    ARCHIVE_TARGET_GROUP,
    ARCHIVE_TEST_LIMIT
)

from archive_database import (
    filter_not_archived
)

from archive_parsers.utils import (
    blog_datetime_key
)

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

ALL_PARSERS = {
    "乃木坂46": get_nogizaka,
    "櫻坂46": get_sakurazaka,
    "日向坂46": get_hinatazaka,
}


# =========================
# グループ指定
# =========================

GROUP_ALIASES = {
    "nogizaka": "乃木坂46",
    "nogizaka46": "乃木坂46",
    "乃木坂": "乃木坂46",
    "乃木坂46": "乃木坂46",

    "sakurazaka": "櫻坂46",
    "sakurazaka46": "櫻坂46",
    "櫻坂": "櫻坂46",
    "櫻坂46": "櫻坂46",

    "hinatazaka": "日向坂46",
    "hinatazaka46": "日向坂46",
    "日向坂": "日向坂46",
    "日向坂46": "日向坂46",
}


# =========================
# 使用するパーサーを選択
# =========================

def get_selected_parsers():

    target = (
        ARCHIVE_TARGET_GROUP
        or "all"
    ).strip().lower()


    if target == "all":

        return ALL_PARSERS.copy()


    group_name = GROUP_ALIASES.get(
        target
    )


    if not group_name:

        print(
            "⚠️ ARCHIVE_TARGET_GROUPの値が不正です:",
            ARCHIVE_TARGET_GROUP
        )

        print(
            "利用可能な値: "
            "all / nogizaka / sakurazaka / hinatazaka"
        )

        return {}


    parser = ALL_PARSERS.get(
        group_name
    )


    if not parser:

        return {}


    return {
        group_name: parser
    }


# =========================
# 1グループ取得
# =========================

async def run_parser(
    group,
    parser,
    session
):

    print("=" * 50)

    print(
        f"[{group}] 巡回開始"
    )


    try:

        result = await parser(
            session
        )


        if not result:

            print(
                f"[{group}] 記事なし"
            )

            return []


        valid_blogs = []


        for blog in result:

            if not isinstance(
                blog,
                dict
            ):

                continue


            url = blog.get(
                "url",
                ""
            )


            if not url:

                continue


            # groupが空の場合に補完
            if not blog.get("group"):

                blog["group"] = group


            valid_blogs.append(
                blog
            )


        print(
            f"[{group}] "
            f"{len(valid_blogs)}件取得"
        )


        return valid_blogs


    except asyncio.CancelledError:

        print(
            f"[{group}] 巡回が停止されました。"
        )

        raise


    except Exception as e:

        print(
            f"[{group}] 取得エラー:",
            e
        )

        traceback.print_exc()

        return []


# =========================
# 全対象グループ取得
# =========================

async def get_all_blogs():

    selected_parsers = get_selected_parsers()


    if not selected_parsers:

        print(
            "実行対象のグループがありません。"
        )

        return []


    print(
        "今回の対象グループ:",
        ", ".join(
            selected_parsers.keys()
        )
    )


    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=30,
        sock_read=60
    )


    connector = aiohttp.TCPConnector(
        limit=20,
        limit_per_host=8,
        ttl_dns_cache=300
    )


    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector
    ) as session:


        tasks = [
            run_parser(
                group,
                parser,
                session
            )
            for group, parser
            in selected_parsers.items()
        ]


        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )


    blogs = []


    for group, result in zip(
        selected_parsers.keys(),
        results
    ):


        if isinstance(
            result,
            asyncio.CancelledError
        ):

            raise result


        if isinstance(
            result,
            Exception
        ):

            print(
                f"[{group}] タスク実行エラー:",
                result
            )

            continue


        blogs.extend(
            result
        )


    print("=" * 50)

    print(
        f"取得合計: {len(blogs)}件"
    )


    return blogs


# =========================
# URL重複除去
# =========================

def remove_duplicate_urls(
    blogs
):

    unique_blogs = []

    seen_urls = set()


    for blog in blogs:

        url = blog.get(
            "url",
            ""
        )


        if not url:

            continue


        if url in seen_urls:

            continue


        seen_urls.add(
            url
        )

        unique_blogs.append(
            blog
        )


    return unique_blogs


# =========================
# archive_main用
# =========================

async def get_archive_targets():

    # -------------------------
    # ブログ一覧取得
    # -------------------------

    blogs = await get_all_blogs()


    if not blogs:

        print(
            "取得できたブログはありません。"
        )

        return []


    # -------------------------
    # URL重複除去
    # -------------------------

    before_duplicate_count = len(
        blogs
    )


    blogs = remove_duplicate_urls(
        blogs
    )


    print(
        "URL重複除去:",
        f"{before_duplicate_count}件",
        "→",
        f"{len(blogs)}件"
    )


    # -------------------------
    # 時系列順にソート
    # -------------------------

    blogs.sort(
        key=blog_datetime_key
    )


    if blogs:

        print(
            "取得記事の最古:",
            blogs[0].get(
                "date",
                "不明"
            ),
            blogs[0].get(
                "url",
                ""
            )
        )

        print(
            "取得記事の最新:",
            blogs[-1].get(
                "date",
                "不明"
            ),
            blogs[-1].get(
                "url",
                ""
            )
        )


    # -------------------------
    # DB登録済みを除外
    # -------------------------

    print(
        "DB登録済みURLを確認中..."
    )


    before_archive_filter = len(
        blogs
    )


    blogs = filter_not_archived(
        blogs
    )


    print(
        "未保存記事:",
        f"{before_archive_filter}件",
        "→",
        f"{len(blogs)}件"
    )


    # DB除外後も念のため再ソート
    blogs.sort(
        key=blog_datetime_key
    )


    # -------------------------
    # テスト件数制限
    # -------------------------

    if ARCHIVE_TEST_LIMIT > 0:

        original_count = len(
            blogs
        )


        blogs = blogs[
            :ARCHIVE_TEST_LIMIT
        ]


        print(
            "テスト件数制限:",
            f"{original_count}件",
            "→",
            f"{len(blogs)}件"
        )


    # -------------------------
    # 最終確認ログ
    # -------------------------

    print("=" * 50)

    print(
        f"今回の送信対象: "
        f"{len(blogs)}件"
    )


    for index, blog in enumerate(
        blogs,
        start=1
    ):

        print(
            f"{index}. "
            f"{blog.get('date', '不明')} / "
            f"{blog.get('group', '不明')} / "
            f"{blog.get('member', '不明')} / "
            f"{blog.get('title', '無題')}"
        )


    print("=" * 50)


    return blogs
