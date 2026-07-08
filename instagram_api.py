import instaloader
import tempfile
import os
import glob


def get_instagram(url):

    temp_dir = tempfile.mkdtemp()

    # URLから投稿コードを取得
    shortcode = url.rstrip("/").split("/")[-1]

    loader = instaloader.Instaloader(
        dirname_pattern=temp_dir,
        save_metadata=False,
        download_comments=False
    )

    try:
        post = instaloader.Post.from_shortcode(
            loader.context,
            shortcode
        )

        files = []

        # 複数画像（カルーセル）対応
        if post.typename == "GraphSidecar":

            for node in post.get_sidecar_nodes():

                if node.is_video:
                    url = node.video_url
                else:
                    url = node.display_url

                files.append(url)

        # 動画投稿
        elif post.is_video:

            files.append(post.video_url)

        # 通常画像
        else:

            files.append(post.url)

        return files

    except Exception as e:

        raise Exception(
            f"Instagram取得失敗: {e}"
        )
