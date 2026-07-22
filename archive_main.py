import asyncio
import os

import aiohttp
import discord
from discord.ext import commands, tasks

from archive_checker import (
    get_archive_lanes,
)

from archive_database import (
    archive_count,
    init_archive_db,
    reset_archive,
    save_archive,
)

from photo_database import (
    get_photo_db_counts,
    get_photo_storage_stats,
    init_photo_db,
    save_photo_blog,
    save_photo_image,
)

from photo_image_downloader import (
    download_blog_images,
    get_photo_storage_path,
)

from archive_image_getter import (
    get_images,
)

from archive_config import (
    ARCHIVE_INTERVAL,
    SEND_DELAY,
)

from archive_media import (
    download_attachment,
)

from archive_parsers.utils import (
    normalize_member_name,
)


# =========================
# Discord設定
# =========================

TOKEN = os.getenv(
    "DISCORD_TOKEN"
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


# =========================
# 2レーン設定
# =========================

# 新着記事を確認する間隔
#
# RailwayのVariablesで、
# ARCHIVE_PRIORITY_INTERVAL=300
# のように変更可能。
#
# 未設定の場合は5分。
ARCHIVE_PRIORITY_INTERVAL = max(
    int(
        os.getenv(
            "ARCHIVE_PRIORITY_INTERVAL",
            "300",
        )
    ),
    60,
)


# 2つのループが同じ記事を
# 同時に処理しないためのロック
archive_processing_lock = asyncio.Lock()


# 新着優先ループの初回確認が
# 終わったことを表すイベント
priority_first_pass_done = asyncio.Event()


# =========================
# チャンネル設定
# =========================

ARCHIVE_ALL_CHANNEL = 1527929665480556635

ARCHIVE_GROUP_CHANNELS = {
    "乃木坂46": 1527929694220193812,
    "櫻坂46": 1527929780891160696,
    "日向坂46": 1527929807986364556,
}


# =========================
# メンバー別チャンネル
# =========================

ARCHIVE_MEMBER_CHANNELS = {

    # =========================
    # 乃木坂46
    # =========================

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

    # =========================
    # 乃木坂46 6期生
    # =========================

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

    # =========================
    # 日向坂46 5期生
    # =========================

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

    "ポカ": 1527938802826477589,
}


# =========================
# 投稿先取得
# =========================

def get_channels(
    blog,
):

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
        "",
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
            "",
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
                "メンバー別チャンネル取得成功:",
                member,
                channel.id,
            )

        else:

            print(
                "メンバー別チャンネル取得失敗:",
                member,
                member_channel_id,
            )

    else:

        print(
            "メンバー別チャンネル未設定:",
            repr(member),
        )

    return channels


# =========================
# 容量表示
# =========================

def format_file_size(
    size_bytes: int,
) -> str:

    size = float(
        max(
            int(size_bytes),
            0,
        )
    )

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]

    for unit in units:

        if (
            size < 1024
            or unit == units[-1]
        ):

            if unit == "B":

                return (
                    f"{int(size)} {unit}"
                )

            return (
                f"{size:.2f} {unit}"
            )

        size /= 1024

    return (
        f"{int(size_bytes)} B"
    )


# =========================
# Bot起動時処理
# =========================

@bot.event
async def on_ready():

    print("=" * 50)
    print(f"ログイン成功: {bot.user}")

    init_archive_db()

    print(
        "アーカイブDB初期化完了"
    )

    init_photo_db()

    print(
        "写真検索DB初期化完了"
    )

    print(
        "写真画像保存先:",
        get_photo_storage_path(),
    )

    print(
        "新着記事確認間隔:",
        f"{ARCHIVE_PRIORITY_INTERVAL}秒",
    )

    print(
        "過去記事確認間隔:",
        f"{ARCHIVE_INTERVAL}秒",
    )

    print(
        "開始コマンド: !archive_start"
    )

    print("=" * 50)


# =========================
# 開始コマンド
# =========================

@bot.command(
    name="archive_start"
)
@commands.is_owner()
async def archive_start_command(
    ctx,
):

    priority_running = (
        priority_archive_loop.is_running()
    )

    history_running = (
        history_archive_loop.is_running()
    )

    if (
        priority_running
        and history_running
    ):

        await ctx.send(
            "⚠️ アーカイブはすでに動作中です。"
        )

        return

    priority_first_pass_done.clear()

    if not priority_running:

        priority_archive_loop.start()

    if not history_running:

        history_archive_loop.start()

    await ctx.send(
        "▶️ ブログアーカイブを開始しました。\n"
        "🚀 新着優先レーン: 動作開始\n"
        "📚 過去記事レーン: 新着初回確認後に開始"
    )

    print(
        "2レーンのアーカイブ巡回を開始しました。"
    )


# =========================
# 停止コマンド
# =========================

@bot.command(
    name="archive_stop"
)
@commands.is_owner()
async def archive_stop_command(
    ctx,
):

    priority_running = (
        priority_archive_loop.is_running()
    )

    history_running = (
        history_archive_loop.is_running()
    )

    if not (
        priority_running
        or history_running
    ):

        await ctx.send(
            "⚠️ アーカイブは停止中です。"
        )

        return

    if priority_running:

        priority_archive_loop.cancel()

    if history_running:

        history_archive_loop.cancel()

    priority_first_pass_done.clear()

    await ctx.send(
        "🛑 ブログアーカイブを停止しました。\n"
        "🚀 新着優先レーン: 停止\n"
        "📚 過去記事レーン: 停止"
    )

    print(
        "2レーンのアーカイブ巡回を停止しました。"
    )


# =========================
# 動作状況確認
# =========================

@bot.command(
    name="archive_status"
)
@commands.is_owner()
async def archive_status_command(
    ctx,
):

    priority_status = (
        "動作中"
        if priority_archive_loop.is_running()
        else "停止中"
    )

    history_status = (
        "動作中"
        if history_archive_loop.is_running()
        else "停止中"
    )

    lock_status = (
        "処理中"
        if archive_processing_lock.locked()
        else "待機中"
    )

    await ctx.send(
        "⚙️ **アーカイブ動作状況**\n"
        f"🚀 新着優先レーン: **{priority_status}**\n"
        f"📚 過去記事レーン: **{history_status}**\n"
        f"🔒 共通処理: **{lock_status}**\n"
        f"新着確認間隔: **{ARCHIVE_PRIORITY_INTERVAL}秒**\n"
        f"過去記事確認間隔: **{ARCHIVE_INTERVAL}秒**"
    )


# =========================
# 写真検索DB件数確認
# =========================

@bot.command(
    name="photo_count"
)
@commands.is_owner()
async def photo_count_command(
    ctx,
):

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
            error,
        )

        await ctx.send(
            "⚠️ 写真検索DBの件数取得に失敗しました。\n"
            f"`{error}`"
        )


# =========================
# 写真ファイル保存状況
# =========================

@bot.command(
    name="photo_storage"
)
@commands.is_owner()
async def photo_storage_command(
    ctx,
):

    try:

        stats = get_photo_storage_stats()

        storage_path = (
            get_photo_storage_path()
        )

        await ctx.send(
            "💾 **写真ファイルの保存状況**\n"
            f"画像登録数: **{stats['total_images']}件**\n"
            f"保存完了: **{stats['completed']}件**\n"
            f"未保存: **{stats['pending']}件**\n"
            f"保存失敗: **{stats['failed']}件**\n"
            f"保存容量: "
            f"**{format_file_size(stats['total_size'])}**\n"
            f"保存先: `{storage_path}`"
        )

    except Exception as error:

        print(
            "写真保存状況取得エラー:",
            error,
        )

        await ctx.send(
            "⚠️ 写真ファイルの保存状況を"
            "取得できませんでした。\n"
            f"`{error}`"
        )


# =========================
# アーカイブDB件数確認
# =========================

@bot.command(
    name="archive_count"
)
@commands.is_owner()
async def archive_count_command(
    ctx,
):

    try:

        count = archive_count()

        await ctx.send(
            "📦 現在のアーカイブ件数: "
            f"**{count}件**"
        )

    except Exception as error:

        print(
            "アーカイブ件数取得エラー:",
            error,
        )

        await ctx.send(
            "⚠️ アーカイブ件数を"
            "取得できませんでした。\n"
            f"`{error}`"
        )


# =========================
# DBリセット
# =========================

@bot.command(
    name="archive_reset"
)
@commands.is_owner()
async def archive_reset_command(
    ctx,
):

    priority_was_running = (
        priority_archive_loop.is_running()
    )

    history_was_running = (
        history_archive_loop.is_running()
    )

    if priority_was_running:

        priority_archive_loop.cancel()

    if history_was_running:

        history_archive_loop.cancel()

    priority_first_pass_done.clear()

    if (
        priority_was_running
        or history_was_running
    ):

        await asyncio.sleep(
            1
        )

    try:

        reset_archive()

        await ctx.send(
            "🧹 アーカイブDBをリセットしました。\n"
            "これまで送信済みだった記事も、"
            "再び送信対象になります。"
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
            "⚠️ DBリセットに失敗しました。\n"
            f"`{error}`"
        )

        return

    if priority_was_running:

        priority_archive_loop.start()

    if history_was_running:

        history_archive_loop.start()

    if (
        priority_was_running
        or history_was_running
    ):

        await ctx.send(
            "▶️ アーカイブ巡回を再開しました。"
        )


# =========================
# 画像をDiscord送信用にまとめる
# =========================

async def prepare_discord_attachments(
    session,
    image_urls,
    upload_limit,
):

    failed_urls = []
    attachments = []

    for image_index, image_url in enumerate(
        image_urls,
        start=1,
    ):

        attachment = await download_attachment(
            session,
            image_url,
            image_index,
            upload_limit,
        )

        if not attachment:

            failed_urls.append(
                image_url
            )

            continue

        file = attachment.get(
            "file"
        )

        if not file:

            reason = attachment.get(
                "reason",
                "送信できませんでした。",
            )

            print(
                "画像送信対象外:",
                reason,
                image_url,
            )

            failed_urls.append(
                image_url
            )

            continue

        attachments.append({
            "file": file,
            "size": attachment.get(
                "size",
                0,
            ),
            "url": image_url,
        })

    return (
        attachments,
        failed_urls,
    )


# =========================
# 添付をグループ分け
# =========================

def split_attachment_groups(
    attachments,
    upload_limit,
):

    file_groups = []
    current_group = []
    current_size = 0

    group_size_limit = max(
        upload_limit
        - (512 * 1024),
        1 * 1024 * 1024,
    )

    for attachment in attachments:

        attachment_size = attachment[
            "size"
        ]

        should_split = (
            len(current_group) >= 10
            or (
                current_group
                and (
                    current_size
                    + attachment_size
                    > group_size_limit
                )
            )
        )

        if should_split:

            file_groups.append(
                current_group
            )

            current_group = []
            current_size = 0

        current_group.append(
            attachment
        )

        current_size += (
            attachment_size
        )

    if current_group:

        file_groups.append(
            current_group
        )

    return file_groups


# =========================
# 送信できないURLを投稿
# =========================

async def send_failed_urls(
    channel,
    failed_urls,
):

    if not failed_urls:

        return

    failed_text = (
        "⚠️ 容量または変換エラーのため、"
        "添付できなかった画像です。\n"
        + "\n".join(
            f"・{failed_url}"
            for failed_url in failed_urls
        )
    )

    while failed_text:

        message_part = failed_text[
            :1900
        ]

        failed_text = failed_text[
            1900:
        ]

        await channel.send(
            message_part,
            suppress_embeds=True,
        )

        await asyncio.sleep(
            SEND_DELAY
        )


# =========================
# 1チャンネルへ送信
# =========================

async def send_blog_to_channel(
    session,
    channel,
    embed,
    image_urls,
):

    await channel.send(
        embed=embed
    )

    await asyncio.sleep(
        SEND_DELAY
    )

    if channel.guild:

        upload_limit = (
            channel.guild.filesize_limit
        )

    else:

        upload_limit = (
            8 * 1024 * 1024
        )

    if not image_urls:

        return

    attachments, failed_urls = (
        await prepare_discord_attachments(
            session,
            image_urls,
            upload_limit,
        )
    )

    file_groups = split_attachment_groups(
        attachments,
        upload_limit,
    )

    for file_group in file_groups:

        try:

            await channel.send(
                files=[
                    item["file"]
                    for item in file_group
                ]
            )

            await asyncio.sleep(
                SEND_DELAY
            )

        except Exception as send_error:

            print(
                "添付まとめ送信エラー "
                f"channel={channel.id}:",
                send_error,
            )

            failed_urls.extend(
                item["url"]
                for item in file_group
            )

    await send_failed_urls(
        channel,
        failed_urls,
    )


# =========================
# Embed作成
# =========================

def build_blog_embed(
    blog,
    image_count,
    lane_name,
):

    if lane_name == "priority":

        lane_text = (
            "🚀 New Priority"
        )

        color = 0x00CC66

    else:

        lane_text = (
            "📚 History Archive"
        )

        color = 0x00AAFF

    embed = discord.Embed(
        title=(
            blog.get(
                "title"
            )
            or "無題"
        ),
        url=blog.get(
            "url",
            "",
        ),
        color=color,
    )

    embed.add_field(
        name="🏷️ グループ",
        value=(
            blog.get(
                "group"
            )
            or "不明"
        ),
        inline=True,
    )

    embed.add_field(
        name="👤 メンバー",
        value=(
            blog.get(
                "member"
            )
            or "不明"
        ),
        inline=True,
    )

    embed.add_field(
        name="📅 投稿日時",
        value=(
            blog.get(
                "date"
            )
            or "不明"
        ),
        inline=False,
    )

    embed.set_footer(
        text=(
            f"Archive BOT • {lane_text}"
            f" • 画像総数 {image_count}枚"
        )
    )

    return embed


# =========================
# 1記事を処理
# =========================

async def process_single_blog(
    session,
    blog,
    lane_name,
    index,
    total,
):

    blog_url = str(
        blog.get(
            "url",
            "",
        )
    ).strip()

    print("-" * 50)

    print(
        f"[{lane_name}] "
        f"処理中 {index}/{total}"
    )

    print(
        "グループ:",
        blog.get(
            "group",
            "不明",
        ),
    )

    print(
        "メンバー:",
        blog.get(
            "member",
            "不明",
        ),
    )

    print(
        "日時:",
        blog.get(
            "date",
            "不明",
        ),
    )

    print(
        "URL:",
        blog_url,
    )

    if not blog_url:

        print(
            "URLが空のためスキップします。"
        )

        return False

    channels = get_channels(
        blog
    )

    if not channels:

        print(
            "送信先チャンネルがありません。"
        )

        return False

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
        start=1,
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
        f"失敗 {download_result['failed']}件",
    )

    # =====================
    # Embed作成
    # =====================

    embed = build_blog_embed(
        blog,
        len(image_urls),
        lane_name,
    )

    send_succeeded = True

    # =====================
    # 各チャンネルへ送信
    # =====================

    for channel in channels:

        try:

            await send_blog_to_channel(
                session,
                channel,
                embed,
                image_urls,
            )

        except asyncio.CancelledError:

            raise

        except Exception as error:

            send_succeeded = False

            print(
                "チャンネル送信エラー "
                f"channel={channel.id}:",
                error,
            )

    # =====================
    # アーカイブDBへ保存
    # =====================

    if send_succeeded:

        save_archive(
            blog
        )

        print(
            "アーカイブ保存完了:",
            blog_url,
        )

        return True

    print(
        "一部の送信に失敗したため、"
        "アーカイブDBには保存しませんでした。"
    )

    return False


# =========================
# 複数記事を処理
# =========================

async def process_blog_list(
    blogs,
    lane_name,
):

    if not blogs:

        print(
            f"[{lane_name}] "
            "処理対象の記事はありません。"
        )

        return

    print(
        f"[{lane_name}] "
        f"今回の処理対象: {len(blogs)}件"
    )

    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=30,
        sock_read=120,
    )

    connector = aiohttp.TCPConnector(
        limit=10,
        limit_per_host=5,
        ttl_dns_cache=300,
    )

    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
    ) as session:

        for index, blog in enumerate(
            blogs,
            start=1,
        ):

            try:

                await process_single_blog(
                    session,
                    blog,
                    lane_name,
                    index,
                    len(blogs),
                )

            except asyncio.CancelledError:

                print(
                    f"[{lane_name}] "
                    "処理が停止されました。"
                )

                raise

            except Exception as error:

                print(
                    f"[{lane_name}] "
                    "アーカイブ処理エラー:",
                    blog.get(
                        "url",
                        "",
                    ),
                    error,
                )

            await asyncio.sleep(
                SEND_DELAY
            )


# =========================
# 指定レーンを1回処理
# =========================

async def run_archive_lane(
    lane_name,
):

    print("=" * 50)

    if lane_name == "priority":

        print(
            "🚀 新着優先レーン巡回開始"
        )

    else:

        print(
            "📚 過去記事レーン巡回開始"
        )

    # 一方のレーンが処理中なら、
    # 完了するまでここで待つ。
    async with archive_processing_lock:

        try:

            # ロック取得後に改めて一覧を取得する。
            # これにより、先に処理された記事は
            # DB除外されて重複送信されない。
            lanes = await get_archive_lanes()

        except asyncio.CancelledError:

            raise

        except Exception as error:

            print(
                f"[{lane_name}] "
                "ブログ一覧取得エラー:",
                error,
            )

            return

        blogs = lanes.get(
            lane_name,
            [],
        )

        await process_blog_list(
            blogs,
            lane_name,
        )

    print(
        f"[{lane_name}] "
        "今回の巡回が完了しました。"
    )

    print("=" * 50)


# =========================
# 新着優先ループ
# =========================

@tasks.loop(
    seconds=ARCHIVE_PRIORITY_INTERVAL
)
async def priority_archive_loop():

    try:

        await run_archive_lane(
            "priority"
        )

    finally:

        # 成功・失敗を問わず、
        # 最初の確認が終了したら
        # 過去記事レーンを解放する。
        if not priority_first_pass_done.is_set():

            priority_first_pass_done.set()


# =========================
# 過去記事ループ
# =========================

@tasks.loop(
    seconds=ARCHIVE_INTERVAL
)
async def history_archive_loop():

    await run_archive_lane(
        "history"
    )


# =========================
# 新着ループ開始前
# =========================

@priority_archive_loop.before_loop
async def before_priority_archive_loop():

    await bot.wait_until_ready()


# =========================
# 過去記事ループ開始前
# =========================

@history_archive_loop.before_loop
async def before_history_archive_loop():

    await bot.wait_until_ready()

    print(
        "📚 過去記事レーンは、"
        "新着優先レーンの初回確認を待機中です。"
    )

    await priority_first_pass_done.wait()

    print(
        "📚 新着初回確認完了。"
        "過去記事レーンを開始します。"
    )


# =========================
# ループエラー表示
# =========================

@priority_archive_loop.error
async def priority_archive_loop_error(
    error,
):

    print(
        "新着優先ループエラー:",
        error,
    )


@history_archive_loop.error
async def history_archive_loop_error(
    error,
):

    print(
        "過去記事ループエラー:",
        error,
    )


# =========================
# BOT起動
# =========================

if not TOKEN:

    raise RuntimeError(
        "環境変数 DISCORD_TOKEN が"
        "設定されていません。"
    )


bot.run(
    TOKEN
)
