import os
import requests


def get_instagram(url):
    """
    Apifyを使ってInstagram投稿から画像・動画URLを取得
    """

    token = os.environ.get("APIFY_TOKEN")

    if not token:
        raise Exception(
            "APIFY_TOKENが設定されていません"
        )

    api_url = (
        "https://api.apify.com/v2/acts/"
        "apify~instagram-scraper/runs"
    )

    payload = {
        "directUrls": [
            url
        ],
        "resultsLimit": 1
    }

    response = requests.post(
        api_url,
        params={
            "token": token
        },
        json=payload
    )

    if response.status_code != 201:
        raise Exception(
            f"Apify APIエラー: {response.text}"
        )

    run = response.json()

    dataset_id = run["data"]["defaultDatasetId"]

    # 結果取得
    dataset_url = (
        f"https://api.apify.com/v2/datasets/"
        f"{dataset_id}/items"
    )

    result = requests.get(
        dataset_url,
        params={
            "token": token
        }
    ).json()

    images = []

    for item in result:

        # 画像
        if "displayUrl" in item:
            images.append(
                item["displayUrl"]
            )

        # カルーセル
        if "images" in item:
            images.extend(
                item["images"]
            )

        # 動画
        if "videoUrl" in item:
            images.append(
                item["videoUrl"]
            )

    return images
