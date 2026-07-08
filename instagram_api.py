import os
import requests


def get_instagram(url):
    """
    Apify Instagram Post Scraperから
    Instagram投稿の画像・動画情報を取得
    """

    token = os.environ.get("APIFY_TOKEN")

    if not token:
        raise Exception(
            "APIFY_TOKENが設定されていません"
        )

    api_url = (
        "https://api.apify.com/v2/acts/"
        "nH2AHrwxeTRJoN5hX/"
        "run-sync-get-dataset-items"
    )

    payload = {
        "dataDetailLevel": "basicData",
        "resultsLimit": 1,
        "skipPinnedPosts": False,
        "username": [
            url
        ]
    }

    response = requests.post(
        api_url,
        params={
            "token": token
        },
        json=payload,
        timeout=120
    )

    if response.status_code not in [200, 201]:
        raise Exception(
            f"Apify APIエラー: {response.text}"
        )

    result = response.json()

    media = []

    for item in result:

        # カルーセル投稿
        if item.get("childPosts"):

            for child in item["childPosts"]:

                # 画像
                if child.get("displayUrl"):
                    media.append(
                        {
                            "type": "image",
                            "url": child["displayUrl"]
                        }
                    )

                # 動画
                if child.get("videoUrl"):
                    media.append(
                        {
                            "type": "video",
                            "url": child["videoUrl"]
                        }
                    )

        # images形式
        if item.get("images"):

            for image in item["images"]:
                media.append(
                    {
                        "type": "image",
                        "url": image
                    }
                )

        # 通常画像
        if (
            not item.get("childPosts")
            and not item.get("images")
            and item.get("displayUrl")
        ):
            media.append(
                {
                    "type": "image",
                    "url": item["displayUrl"]
                }
            )

        # 通常動画
        if item.get("videoUrl"):
            media.append(
                {
                    "type": "video",
                    "url": item["videoUrl"]
                }
            )

    return media
