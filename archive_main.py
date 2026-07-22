import os
import shutil
import asyncio
import aiohttp

import discord
from discord.ext import commands, tasks

from archive_checker import get_archive_targets
from archive_database import (
    init_archive_db,
    save_archive,
    reset_archive,
)
from photo_database import (
    init_photo_db,
    get_photo_db_counts,
    save_photo_blog,
    save_photo_image,
)
from photo_image_downloader import (
    download_blog_images,
    get_photo_storage_path,
)
from archive_image_getter import get_images
from archive_config import (
    ARCHIVE_INTERVAL,
    SEND_DELAY
)

from archive_media import (
    download_attachment
)

from archive_parsers.utils import (
    normalize_member_name
)

# =========================
# Discord設定
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# =========================
# チャンネル設定
# =========================

ARCHIVE_ALL_CHANNEL = 1527929665480556635

ARCHIVE_GROUP_CHANNELS = {

    "乃木坂46": 1527929694220193812,
    "櫻坂46": 1527929780891160696,
    "日向坂46": 1527929807986364556

}





# =========================
# メンバー別
# =========================

ARCHIVE_MEMBER_CHANNELS = {


    # 乃木坂46

    "伊藤理々杏": 1527930403518812170,

    "岩本蓮加": 1527930443612033024,

    "吉田綾乃クリスティー": 1527930466496155658,

    "遠藤さくら": 1527930489233473607,

    "賀喜遥香": 1527930520850137107,

    "金川紗耶": 1527930862715404289,

    "黒見明香": 1527930918457708574,

    "柴田柚菜": 1527931048263028827,

    "田村真佑": 1527931130471518349,

    "筒井あやめ": 1527931187488755823,

    "林瑠奈": 1527931233911308338,

    "弓木奈於": 1527931294929916045,


    "五百城茉央": 1527931357546938368,

    "池田瑛紗": 1527931417827479582,

    "一ノ瀬美空": 1527931501210112040,

    "井上和": 1527931556411211947,

    "岡本姫奈": 1527931609045536818,

    "小川彩": 1527931658936783028,

    "奥田いろは": 1527931702859665438,

    "川﨑桜": 1527931748330242108,

    "菅原咲月": 1527931809097060463,

    "冨里奈央": 1527931859898597527,

    "中西アルノ": 1527931911287214140,


    # 乃木坂6期生

    "愛宕心響": 1527931959962112080,

    "大越ひなの": 1527932018355077175,

    "小津玲奈": 1527932077205618698,

    "海邉朱莉": 1527932192095731832,

    "川端晃菜": 1527932323860058202,

    "鈴木佑捺": 1527932379316883537,

    "瀬戸口心月": 1527932423181041754,

    "長嶋凛桜": 1527932466906665002,

    "増田三莉音": 1527932511156568164,

    "森平麗心": 1527932554429206580,

    "矢田萌華": 1527932598284845168,

    # =========================
    # 櫻坂46
    # =========================

    "遠藤光莉": 1527934512791683165,

    "大園玲": 1527934565002383502,

    "大沼晶保": 1527934615514513538,

    "幸阪茉里乃": 1527934682229116968,

    "田村保乃": 1527934735563755580,

    "藤吉夏鈴": 1527934782183571626,

    "増本綺良": 1527934840035348480,

    "松田里奈": 1527934887456407793,

    "森田ひかる": 1527934948332408903,

    "守屋麗奈": 1527935003214872636,

    "山﨑天": 1527935052036571156,

    "石森璃花": 1527935110538596483,

    "遠藤理子": 1527935160077520936,

    "小田倉麗奈": 1527935206940737556,

    "小島凪紗": 1527935254197833779,

    "谷口愛季": 1527935315816353842,

    "中嶋優月": 1527935370669461636,

    "的野美青": 1527935423903698945,

    "向井純葉": 1527935468921032784,

    "村井優": 1527935517788999680,

    "村山美羽": 1527935561006972948,

    "山下瞳月": 1527935621283450930,


    # =========================
    # 櫻坂46 4期生
    # =========================

    "浅井恋乃未": 1527935664300097636,

    "稲熊ひな": 1527935720944042034,

    "勝又春": 1527935775604477993,

    "佐藤愛桜": 1527935838401466368,

    "中川智尋": 1527935892184891524,

    "松本和子": 1527935942734774293,

    "目黒陽色": 1527935996291846204,

    "山川宇衣": 1527936046854180994,

    "山田桃実": 1527936102722306068,



    # =========================
    # 日向坂46
    # =========================

    "金村美玖": 1527937333377237143,

    "小坂菜緒": 1527937391648837733,

    "上村ひなの": 1527937465405673523,

    "髙橋未来虹": 1527937516609601636,

    "森本茉莉": 1527937567268536430,

    "山口陽世": 1527937615720874034,

    "石塚瑶季": 1527937664681119894,

    "小西夏菜実": 1527937713343434843,

    "清水理央": 1527937766573215834,

    "正源司陽子": 1527937810902810685,

    "竹内希来里": 1527937861339451556,

    "平尾帆夏": 1527937938216714412,

    "平岡海月": 1527938000330428476,

    "藤嶌果歩": 1527938049181220954,

    "宮地すみれ": 1527938101484453908,

    "山下葉留花": 1527938150880772096,

    "渡辺莉奈": 1527938196829376674,


    # 日向坂46 5期生

    "大田美月": 1527938246846320762,

    "大野愛実": 1527938290831851691,

    "片山紗希": 1527938341402579185,

    "蔵盛妃那乃": 1527938389024702465,

    "坂井新奈": 1527938431651414066,

    "佐藤優羽": 1527938483669303296,

    "下田衣珠季": 1527938588367650817,

    "高井俐香": 1527938644201963642,

    "鶴崎仁香": 1527938689055854635,

    "松尾桜": 1527938740738064434,


    # =========================
    # その他
    # =========================

    "ポカ": 1527938802826477589

}

# =========================
# 投稿先取得
# =========================

def get_channels(blog):

    channels = []
    seen = set()

    # -------------------------
    # 1. 全体チャンネル
    # -------------------------

    if ARCHIVE_ALL_CHANNEL:

        channel = bot.get_channel(
            ARCHIVE_ALL_CHANNEL
        )

        if channel:

            channels.append(
                channel
            )

            seen.add(
                channel.id
            )


    # -------------------------
    # 2. グループチャンネル
    # -------------------------

    group = blog.get(
        "group",
        ""
    )

    group_channel_id = ARCHIVE_GROUP_CHANNELS.get(
        group
    )

    if group_channel_id:

        channel = bot.get_channel(
            group_channel_id
        )

        if (
            channel
            and channel.id not in seen
        ):

            channels.append(
                channel
            )

            seen.add(
                channel.id
            )


    # -------------------------
    # 3. メンバーチャンネル
    # -------------------------

    member = normalize_member_name(
        blog.get(
            "member",
            ""
        )
    )

    member_channel_id = ARCHIVE_MEMBER_CHANNELS.get(
        member
    )

    if member_channel_id:

        channel = bot.get_channel(
            member_channel_id
        )

        if (
            channel
            and channel.id not in seen
        ):

            channels.append(
                channel
            )

            seen.add(
                channel.id
            )

            print(
                f"メンバー別チャンネル取得成功: "
                f"{member} / {channel.id}"
            )

        else:

            print(
                f"メンバー別チャンネル取得失敗: "
                f"{member} / {member_channel_id}"
            )

    else:

        print(
            "メンバー別チャンネル未設定:",
            repr(member)
        )


    return channels




# =========================
# 起動時処理
# =========================

@bot.event
async def on_ready():

    print("=" * 40)
    print(f"ログイン成功: {bot.user}")

    init_archive_db()

    print("アーカイブDB初期化完了")

    init_photo_db()

    print("写真検索DB初期化完了")
    
    print(
        "写真画像保存先:",
        get_photo_storage_path()
    )

    print(
        f"保存済みチェック間隔: "
        f"{ARCHIVE_INTERVAL}秒"
    )

    print("!archive_start で開始")

    print("=" * 40)

# =========================
# 開始コマンド
# =========================

@bot.command()
@commands.is_owner()
async def archive_start(ctx):

    if archive_loop.is_running():

        await ctx.send(
            "⚠️ アーカイブはすでに動作中です。"
        )

        return


    archive_loop.start()


    await ctx.send(
        "▶️ ブログアーカイブを開始しました。"
    )


    print(
        "アーカイブ巡回を開始しました。"
    )

# =========================
# 写真検索DB件数確認
# =========================

@bot.command(
    name="photo_count"
)
@commands.is_owner()
async def photo_count_command(ctx):

    try:

        counts = get_photo_db_counts()

        await ctx.send(
            "📷 **写真検索DBの状態**\n"
            f"ブログ: **{counts['blogs']}件**\n"
            f"画像: **{counts['images']}件**\n"
            f"AIタグ: **{counts['ai_tags']}件**\n"
            f"手動タグ: **{counts['manual_tags']}件**\n"
            f"確認待ち: **{counts['pending_reviews']}件**\n"
            f"お気に入り: **{counts['favorites']}件**"
        )

    except Exception as error:

        print(
            "写真検索DB件数取得エラー:",
            error
        )

        await ctx.send(
            "⚠️ 写真検索DBの件数取得に失敗しました。\n"
            f"`{error}`"
        )


# =========================
# 停止コマンド
# =========================

@bot.command()
@commands.is_owner()
async def archive_stop(ctx):

    if not archive_loop.is_running():

        await ctx.send(
            "⚠️ アーカイブは停止中です。"
        )

        return


    archive_loop.cancel()


    await ctx.send(
        "🛑 ブログアーカイブを停止しました。"
    )


    print(
        "アーカイブ巡回を停止しました。"
    )


# =========================
# DBリセット
# =========================

@bot.command()
@commands.is_owner()
async def archive_reset(ctx):

    # 巡回中なら先に停止
    was_running = archive_loop.is_running()

    if was_running:
        archive_loop.cancel()

        # タスクが停止するまで少し待つ
        await asyncio.sleep(1)

    try:
        reset_archive()

        await ctx.send(
            "🧹 アーカイブDBをリセットしました。\n"
            "これまで送信済みだった記事も、再び送信対象になります。"
        )

        print(
            "アーカイブDBをリセットしました。"
        )

    except Exception as error:
        print(
            "アーカイブDBリセットエラー:",
            error,
        )

        await ctx.send(
            f"⚠️ DBリセットに失敗しました。\n`{error}`"
        )

    # リセット前に動作中だった場合だけ再開
    if was_running:
        archive_loop.start()

        await ctx.send(
            "▶️ アーカイブ巡回を再開しました。"
        )

# =========================
# DB件数確認
# =========================

@bot.command()
@commands.is_owner()
async def archive_count_command(ctx):

    from archive_database import archive_count


    count = archive_count()


    await ctx.send(
        f"📦 現在のアーカイブ件数: **{count}件**"
    )



# =========================
# アーカイブ本体
# =========================

@tasks.loop(
    seconds=ARCHIVE_INTERVAL
)
async def archive_loop():

    print("=" * 50)
    print("アーカイブ巡回を開始します。")

    try:

        blogs = await get_archive_targets()

    except Exception as e:

        print(
            "ブログ一覧取得エラー:",
            e
        )

        return


    if not blogs:

        print(
            "未アーカイブの記事はありません。"
        )

        return


    print(
        f"今回の処理対象: {len(blogs)}件"
    )


    async with aiohttp.ClientSession() as session:

        for index, blog in enumerate(
            blogs,
            start=1
        ):

            blog_url = blog.get(
                "url",
                ""
            )

            print("-" * 50)

            print(
                f"処理中 {index}/{len(blogs)}"
            )

            print(
                f"グループ: {blog.get('group', '不明')}"
            )

            print(
                f"メンバー: {blog.get('member', '不明')}"
            )

            print(
                f"日時: {blog.get('date', '不明')}"
            )

            print(
                f"URL: {blog_url}"
            )


            if not blog_url:

                print(
                    "URLが空のためスキップします。"
                )

                continue


            try:

                channels = get_channels(
                    blog
                )


                if not channels:

                    print(
                        "送信先チャンネルがありません。"
                    )

                    continue


                # =====================
                # 記事画像URL取得
                # =====================

                image_urls = await get_images(
                    blog_url
                )


                if not image_urls:

                    image_urls = []


                print(
                    f"取得画像数: {len(image_urls)}"
                )

                
                # =====================
                # 写真検索DBへ保存
                # =====================

                blog["images"] = image_urls

                blog_id = save_photo_blog(
                    blog
                )

                photo_image_records = []

                for image_index, image_url in enumerate(
                    image_urls,
                    start=1
                ):

                    image_id = save_photo_image(
                        blog_id=blog_id,
                        image_url=image_url,
                        image_index=image_index,
                    )

                    photo_image_records.append({
                        "image_id": image_id,
                        "image_url": image_url,
                        "image_index": image_index,
                    })


                # =====================
                # 画像ファイルをVolumeへ保存
                # =====================

                download_result = await download_blog_images(
                    session,
                    blog_id=blog_id,
                    blog=blog,
                    image_records=photo_image_records,
                )

                print(
                    "写真画像保存結果:",
                    f"成功 {download_result['success']}件 / "
                    f"失敗 {download_result['failed']}件"
                )



                # =====================
                # Embed作成
                # =====================

                embed = discord.Embed(

                    title=blog.get(
                        "title"
                    ) or "無題",

                    url=blog_url,

                    color=0x00AAFF

                )


                embed.add_field(

                    name="🏷️ グループ",

                    value=blog.get(
                        "group"
                    ) or "不明",

                    inline=True

                )


                embed.add_field(

                    name="👤 メンバー",

                    value=blog.get(
                        "member"
                    ) or "不明",

                    inline=True

                )


                embed.add_field(

                    name="📅 投稿日時",

                    value=blog.get(
                        "date"
                    ) or "不明",

                    inline=False

                )


                embed.set_footer(

                    text=(
                        "Archive BOT"
                        f" • 画像総数 {len(image_urls)}枚"
                    )

                )


                # 全送信先への送信が成功したか
                send_succeeded = True


                # =====================
                # チャンネルごとに送信
                # =====================

                for channel in channels:

                    try:

                        await channel.send(
                            embed=embed
                        )


                        await asyncio.sleep(
                            SEND_DELAY
                        )


                        # Discordの添付上限を取得
                        if channel.guild:

                            upload_limit = (
                                channel.guild.filesize_limit
                            )

                        else:

                            # ギルド情報を取れなかった場合の
                            # 安全側の予備値
                            upload_limit = (
                                8 * 1024 * 1024
                            )


                        if image_urls:

                            failed_urls = []
                            attachments = []

                            # 画像を取得し、Discordへ送れる添付を準備する。
                            for image_index, image_url in enumerate(
                                image_urls,
                                start=1
                            ):

                                attachment = await download_attachment(
                                    session,
                                    image_url,
                                    image_index,
                                    upload_limit
                                )

                                if not attachment:
                                    failed_urls.append(image_url)
                                    continue

                                file = attachment.get("file")

                                if not file:
                                    reason = attachment.get(
                                        "reason",
                                        "送信できませんでした。"
                                    )

                                    print(
                                        f"画像送信対象外: "
                                        f"{reason} {image_url}"
                                    )

                                    failed_urls.append(image_url)
                                    continue

                                attachments.append({
                                    "file": file,
                                    "size": attachment.get("size", 0),
                                    "url": image_url,
                                })

                            # Discordは1メッセージにつき最大10ファイル。
                            # さらに合計容量が大きくなりすぎないよう、
                            # アップロード上限以内でグループ分けする。
                            file_groups = []
                            current_group = []
                            current_size = 0
                            group_size_limit = max(
                                upload_limit - (512 * 1024),
                                1 * 1024 * 1024
                            )

                            for attachment in attachments:
                                attachment_size = attachment["size"]

                                should_split = (
                                    len(current_group) >= 10
                                    or (
                                        current_group
                                        and current_size + attachment_size
                                        > group_size_limit
                                    )
                                )

                                if should_split:
                                    file_groups.append(current_group)
                                    current_group = []
                                    current_size = 0

                                current_group.append(attachment)
                                current_size += attachment_size

                            if current_group:
                                file_groups.append(current_group)

                            # グループごとにまとめて送信する。
                            for file_group in file_groups:
                                try:
                                    await channel.send(
                                        files=[
                                            item["file"]
                                            for item in file_group
                                        ]
                                    )
                                    await asyncio.sleep(SEND_DELAY)
                                except Exception as send_error:
                                    print(
                                        f"添付まとめ送信エラー "
                                        f"channel={channel.id}:",
                                        send_error
                                    )
                                    failed_urls.extend(
                                        item["url"]
                                        for item in file_group
                                    )

                            # 変換後も送れなかったものは元画像URLを投稿
                            if failed_urls:
                                failed_text = (
                                    "⚠️ 容量または変換エラーのため、"
                                    "添付できなかった画像です。\n"
                                    + "\n".join(
                                        f"・{failed_url}"
                                        for failed_url in failed_urls
                                    )
                                )

                                while failed_text:
                                    message_part = failed_text[:1900]
                                    failed_text = failed_text[1900:]

                                    await channel.send(
                                        message_part,
                                        suppress_embeds=True
                                    )
                                    await asyncio.sleep(SEND_DELAY)


                    except Exception as e:

                        send_succeeded = False


                        print(
                            f"チャンネル送信エラー "
                            f"channel={channel.id}:",
                            e
                        )


                # =====================
                # DB保存
                # =====================

                if send_succeeded:

                    save_archive(
                        blog
                    )


                    print(
                        "保存完了:",
                        blog_url
                    )

                else:

                    print(
                        "一部の送信に失敗したため、"
                        "DBには保存しませんでした。"
                    )


            except Exception as e:

                print(
                    "アーカイブ処理エラー:",
                    blog_url,
                    e
                )


            await asyncio.sleep(
                SEND_DELAY
            )


    print("=" * 50)
    print("今回のアーカイブ巡回が完了しました。")


# =========================
# Bot準備完了待ち
# =========================

@archive_loop.before_loop
async def before_archive_loop():

    await bot.wait_until_ready()



# =========================
# BOT起動
# =========================

if not TOKEN:
    raise RuntimeError(
        "環境変数 DISCORD_TOKEN が設定されていません。"
    )


bot.run(
    TOKEN
)
