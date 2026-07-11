import aiohttp

from bs4 import BeautifulSoup
from urllib.parse import urljoin



HEADERS = {

    "User-Agent":
        (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36"
        )

}




# =========================
# 除外ワード
# =========================

NG_WORDS = [

    "logo",
    "icon",
    "sprite",
    "favicon",
    "loading",
    "header",
    "footer",
    "banner"

]




# =========================
# 画像取得
# =========================

async def get_images(url):


    try:

        timeout = aiohttp.ClientTimeout(
            total=15
        )


        async with aiohttp.ClientSession() as session:


            async with session.get(
                url,
                headers=HEADERS,
                timeout=timeout
            ) as response:


                response.raise_for_status()


                html = await response.text()



        soup = BeautifulSoup(
            html,
            "html.parser"
        )



    except Exception as e:


        print(
            "画像ページ取得エラー:",
            e
        )


        return []




    images = []



    # =========================
    # 本文エリア優先
    # =========================

    article = (

        soup.select_one(
            ".bd--article"
        )

        or

        soup.select_one(
            ".box-article"
        )

        or

        soup.select_one(
            ".c-blog-article__text"
        )

    )



    target = article or soup




    seen = set()



    for img in target.select(
        "img"
    ):


        src = img.get(
            "src"
        )


        if not src:

            continue



        image_url = urljoin(
            url,
            src
        )


        lower = image_url.lower()



        # 除外

        if any(
            word in lower
            for word in NG_WORDS
        ):

            continue



        # 画像以外除外

        if not any(
            ext in lower
            for ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            ]
        ):

            continue




        if image_url in seen:

            continue



        seen.add(
            image_url
        )


        images.append(
            image_url
        )



    print(
        f"取得画像数: {len(images)}",
        url
    )


    return images
