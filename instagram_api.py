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

    # 通常画像
    if item.get("displayUrl"):
        images.append(item["displayUrl"])

    # 複数画像
    if item.get("images"):
        images.extend(item["images"])

    # カルーセル
    if item.get("childPosts"):
        for child in item["childPosts"]:
            if child.get("displayUrl"):
                images.append(child["displayUrl"])

            if child.get("videoUrl"):
                images.append(child["videoUrl"])

    # 動画
    if item.get("videoUrl"):
        images.append(item["videoUrl"])

return images
