import os
import requests


def get_instagram(url):
    """
    Apify Instagram Post Scraperから
    Instagram投稿の画像・動画URLを取得
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

    if response.status_code != 200:
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
                        child["displayUrl"]
                    )

                # 動画
                if child.get("videoUrl"):
                    media.append(
                        child["videoUrl"]
                    )

        else:

            # 通常画像
            if item.get("displayUrl"):
                media.append(
                    item["displayUrl"]
                )

            # 通常動画
            if item.get("videoUrl"):
                media.append(
                    item["videoUrl"]
                )

    return media
