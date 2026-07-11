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
    全グループのブログ取得（1つが失敗しても他を継続する）
    """
    blogs = []

    # グループ名と関数のペアで管理
    parsers = {
        "乃木坂46": get_nogizaka,
        "櫻坂46": get_sakurazaka,
        "日向坂46": get_hinatazaka
    }

    for group_name, parser in parsers.items():
        try:
            print(f"[{group_name}] 巡回を開始します...")
            # 各パーサーを非同期で実行
            result = await parser()

            if result:
                blogs.extend(result)
                print(f"[{group_name}] {len(result)} 件の記事を取得しました。")
            else:
                print(f"[{group_name}] 新しい記事は見つかりませんでした。")

        except Exception as e:
            # エラーが出てもここでキャッチしてログに出すので、次のグループの巡回は止まりません
            print(f"【重要エラー】{group_name} の取得中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc() # エラーの詳しい原因をログに出力

    return blogs


async def get_archive_targets():
    """
    未アーカイブ記事を取得（古い順で返す）
    """
    blogs = await get_all_blogs()

    # 日付順にソート
    blogs.sort(key=lambda x: x.get("date", ""))

    targets = []
    for blog in blogs:
        url = blog.get("url")
        if not url:
            continue

        if is_archived(url):
            continue

        targets.append(blog)

        if len(targets) >= ARCHIVE_BATCH_SIZE:
            break

    return targets
