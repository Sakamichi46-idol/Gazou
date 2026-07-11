import asyncio

from archive_checker import get_oldest_not_archived


async def run_archive(bot):
    """
    アーカイブBOT本体

    現時点では、
    ・archive_checkerから次に処理するURLを取得
    ・URLが無ければ待機
    まで実装する。

    Discordへの送信処理は後のStepで追加する。
    """

    while True:

        blog_url = get_oldest_not_archived()

        if blog_url is None:
            print("アーカイブ対象はありません。60秒後に再確認します。")
            await asyncio.sleep(60)
            continue

        print(f"次にアーカイブするブログ: {blog_url}")

        # 次のStepでここに
        # ・記事取得
        # ・画像取得
        # ・Discord送信
        # ・DB保存
        # を追加する

        await asyncio.sleep(5)
