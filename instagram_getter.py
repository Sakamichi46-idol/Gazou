import yt_dlp


def get_instagram(url):

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

    print("====== Instagram情報 ======")

    for key in info.keys():
        print(key)

    print("===========================")

    return []
