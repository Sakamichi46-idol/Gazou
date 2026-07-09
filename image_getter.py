from parsers.nogizaka import get_nogizaka_images
from parsers.sakurazaka import get_sakurazaka_images
from parsers.hinatazaka import get_hinatazaka_images


def get_images(url):
    if "nogizaka46.com" in url:
        return get_nogizaka_images(url)

    elif "sakurazaka46.com" in url:
        return get_sakurazaka_images(url)

    elif "hinatazaka46.com" in url:
        return get_hinatazaka_images(url)

    raise ValueError("対応していないURLです。")
