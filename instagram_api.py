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

    images = []

    for item in result:

        # メイン画像
        if item.get("displayUrl"):
            images.append(
                item["displayUrl"]
            )

        # 複数画像
        if item.get("images"):
            images.extend(
                item["images"]
            )

        # カルーセル
        if item.get("childPosts"):
            for child in item["childPosts"]:
                if child.get("displayUrl"):
                    images.append(
                        child["displayUrl"]
                    )

                if child.get("videoUrl"):
                    images.append(
                        child["videoUrl"]
                    )

        # 動画
        if item.get("videoUrl"):
            images.append(
                item["videoUrl"]
            )

    return images
