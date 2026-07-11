import traceback

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



# =========================
# 全ブログ取得
# =========================

async def get_all_blogs():

    blogs = []


    parsers = {

        "乃木坂46": get_nogizaka,

        "櫻坂46": get_sakurazaka,

        "日向坂46": get_hinatazaka

    }



    for group_name, parser in parsers.items():

        try:

            print(
                f"[{group_name}] 巡回開始"
            )


            result = await parser(session)



            if result:


                for blog in result:


                    # groupが無い場合補完

                    if not blog.get(
                        "group"
                    ):

                        blog["group"] = group_name



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
                f"{group_name}取得エラー:",
                e
            )


            traceback.print_exc()



    return blogs





# =========================
# 未アーカイブ取得
# =========================

async def get_archive_targets():


    blogs = await get_all_blogs()



    # 古い順

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
