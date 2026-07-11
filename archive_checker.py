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

from archive_database import (
    is_archived
)

from archive_config import (
    ARCHIVE_BATCH_SIZE
)


async def get_all_blogs():
    """
    全グループのブログ取得
    1グループが失敗しても他は継続
    """

    blogs = []


    parsers = {
        "乃木坂46": get_nogizaka,
        "櫻坂46": get_sakurazaka,
        "日向坂46": get_hinatazaka
    }


    timeout = aiohttp.ClientTimeout(
        total=30
    )


    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:


        for group_name, parser in parsers.items():

            try:

                print(
                    f"[{group_name}] 巡回開始"
                )


                result = await parser(
                    session
                )


                if result:

                    blogs.extend(
                        result
                    )

                    print(
                        f"[{group_name}] {len(result)}件取得"
                    )

                else:

                    print(
                        f"[{group_name}] 記事なし"
                    )


            except Exception as e:

                print(
                    f"[{group_name}] 取得エラー: {e}"
                )

                import traceback
                traceback.print_exc()



    return blogs



async def get_archive_targets():

    """
    未アーカイブ記事のみ取得
    古い順で返す
    """

    blogs = await get_all_blogs()


    blogs.sort(
        key=lambda x: x.get(
            "date",
            ""
        )
    )


    targets = []


    for blog in blogs:

        url = blog.get(
            "url"
        )


        if not url:
            continue


        if is_archived(
            url
        ):
            continue


        targets.append(
            blog
        )


        if len(targets) >= ARCHIVE_BATCH_SIZE:
            break



    return targets
