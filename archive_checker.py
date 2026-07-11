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
    is_archived,
    save_archive
)


from archive_config import (
    ARCHIVE_BATCH_SIZE
)



def get_all_blogs():

    """
    全グループのブログ取得
    """

    blogs = []


    parsers = [

        get_nogizaka,
        get_sakurazaka,
        get_hinatazaka

    ]


    for parser in parsers:

        try:

            result = parser()

            if result:

                blogs.extend(
                    result
                )


        except Exception as e:

            print(
                "取得エラー:",
                e
            )


    return blogs



def get_archive_targets():

    """
    未アーカイブ記事を取得

    古い順で
    ARCHIVE_BATCH_SIZE件返す
    """


    blogs = get_all_blogs()


    # 古い順

    blogs.sort(
        key=lambda x:
            x.get(
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



        if is_archived(url):

            continue



        targets.append(
            blog
        )


        if len(targets) >= ARCHIVE_BATCH_SIZE:

            break



    return targets



def mark_archived(blog):

    """
    アーカイブ済み登録
    """


    save_archive(
        blog["url"]
    )
