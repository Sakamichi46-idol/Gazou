import instaloader


def get_instagram(url):

    print("Instagramアクセス開始")

    L = instaloader.Instaloader()

    shortcode = url.split("/p/")[1].split("/")[0]

    print("Shortcode:", shortcode)

    post = instaloader.Post.from_shortcode(
        L.context,
        shortcode
    )

    print("取得成功")
    print(post)

    return []
