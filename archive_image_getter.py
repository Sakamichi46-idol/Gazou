import requests

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



def get_images(url):

    """
    ブログ本文画像取得
    """

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()


        soup = BeautifulSoup(
            response.text,
            "lxml"
        )


        images = []


        for img in soup.select(
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



            lower_url = image_url.lower()



            if any(
                word in lower_url
                for word in NG_WORDS
            ):

                continue



            # jpg/png/webpだけ

            if not any(
                ext in lower_url
                for ext in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                ]
            ):

                continue



            if image_url not in images:

                images.append(
                    image_url
                )



        print(
            "取得画像数:",
            len(images)
        )


        return images



    except Exception as e:


        print(
            "画像取得エラー:",
            e
        )


        return []
