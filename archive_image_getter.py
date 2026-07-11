import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin



HEADERS = {

    "User-Agent":
        "Mozilla/5.0"

}



def get_images(url):

    """
    ブログ記事から画像URL取得
    """


    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
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



            # ロゴなど除外

            if any(
                x in image_url.lower()
                for x in [
                    "logo",
                    "icon",
                    "sprite"
                ]
            ):

                continue



            if image_url not in images:

                images.append(
                    image_url
                )



        return images



    except Exception as e:


        print(
            "画像取得エラー:",
            e
        )


        return []
