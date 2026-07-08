import yt_dlp


def get_instagram(url):

    ydl_opts = {
        "quiet": False,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    print("========== Instagram ==========")
    print("type:", info.get("_type"))
    print("id:", info.get("id"))
    print("title:", info.get("title"))
    print("thumbnail:", info.get("thumbnail"))
    print("keys:", list(info.keys()))
    print("===============================")

    return []
