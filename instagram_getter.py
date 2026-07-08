import glob
import os
import tempfile

import yt_dlp


def get_instagram(url):

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "outtmpl": os.path.join(temp_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    files = glob.glob(os.path.join(temp_dir, "*"))

    print("ダウンロードしたファイル")

    for file in files:
        print(file)

    return files
