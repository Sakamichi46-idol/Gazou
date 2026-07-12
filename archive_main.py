import os
import io
import shutil
import asyncio
import aiohttp

import discord
from discord.ext import commands, tasks

from archive_checker import get_archive_targets
from archive_database import (
    init_archive_db,
    save_archive
)
from archive_image_getter import get_images
from archive_config import (
    ARCHIVE_INTERVAL,
    SEND_DELAY
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

ARCHIVE_ALL_CHANNEL = 1525522665614606427

ARCHIVE_GROUP_CHANNELS = {

    "乃木坂46": 1525523279660580904,
    "櫻坂46": 1525523343644561418,
    "日向坂46": 1525523279660580904

}





# =========================
# メンバー別
# =========================

ARCHIVE_MEMBER_CHANNELS = {


    # 乃木坂46

    "伊藤理々杏": 1525523634074947634,

    "岩本蓮加": 1525523673241620510,

    "吉田綾乃クリスティー": 1525523778854064269,

    "遠藤さくら": 1525523832805523486,

    "賀喜遥香": 1525523877935972492,

    "金川紗耶": 1525523913247817839,

    "黒見明香": 1525523949658574868,

    "柴田柚菜": 1525524005422104797,

    "田村真佑": 1525524047759413431,

    "筒井あやめ": 1525524083163402430,

    "林瑠奈": 1525524118928359504,

    "弓木奈於": 1525524155389444146,


    "五百城茉央": 1525524214319284484,

    "池田瑛紗": 1525524326093164646,

    "一ノ瀬美空": 1525524358297026771,

    "井上和": 1525524401141846120,

    "岡本姫奈": 1525524435803701270,

    "小川彩": 1525524470536863907,

    "奥田いろは": 1525524505794183350,

    "川﨑桜": 1525524546227146823,

    "菅原咲月": 1525524582650609846,

    "冨里奈央": 1525524626904711248,

    "中西アルノ": 1525524662791180389,


    # 乃木坂6期生

    "愛宕心響": 1525524789651837098,

    "大越ひなの": 1525524826016452800,

    "小津玲奈": 1525524884929904823,

    "海邉朱莉": 1525524927329992754,

    "川端晃菜": 1525525001397342329,

    "鈴木佑捺": 1525525069139284200,

    "瀬戸口心月": 1525525120200867852,

    "長嶋凛桜": 1525525192833503415,

    "増田三莉音": 1525525285422891038,

    "森平麗心": 1525525353106509885,

    "矢田萌華": 1525525400997072966,

    # =========================
    # 櫻坂46
    # =========================

    "遠藤光莉": 1525525572548038837,

    "大園玲": 1525525811376164934,

    "大沼晶保": 1525525847472341062,

    "幸阪茉里乃": 1525525953789563073,

    "田村保乃": 1525526022747852870,

    "藤吉夏鈴": 1525526055299977298,

    "増本綺良": 1525526098153308272,

    "松田里奈": 1525526151005602003,

    "森田ひかる": 1525526187907219608,

    "守屋麗奈": 1525526234337902632,

    "山﨑天": 1525526285575520306,

    "石森璃花": 1525526331217940700,

    "遠藤理子": 1525526378320105643,

    "小田倉麗奈": 1525526426906792107,

    "小島凪紗": 1525526458137575624,

    "谷口愛季": 1525526496599347220,

    "中嶋優月": 1525526568615804978,

    "的野美青": 1525526613587005450,

    "向井純葉": 1525526652891697303,

    "村井優": 1525526689998962790,

    "村山美羽": 1525526719208095754,

    "山下瞳月": 1525526763411869697,


    # =========================
    # 櫻坂46 4期生
    # =========================

    "浅井恋乃未": 1525526845536338022,

    "稲熊ひな": 1525526905552375959,

    "勝又春": 1525526954134994986,

    "佐藤愛桜": 1525527014138712176,

    "中川智尋": 1525527062407020565,

    "松本和子": 1525527108082864400,

    "目黒陽色": 1525527177829941274,

    "山川宇衣": 1525527218514694205,

    "山田桃実": 1525527279239823422,



    # =========================
    # 日向坂46
    # =========================

    "金村美玖": 1525527395598078054,

    "小坂菜緒": 1525527429635117156,

    "上村ひなの": 1525527468398743654,

    "髙橋未来虹": 1525527554373718106,

    "森本茉莉": 1525527612104118362,

    "山口陽世": 1525527649735414012,

    "石塚瑶季": 1525527777716080842,

    "小西夏菜実": 1525527817532608702,

    "清水理央": 1525527845466804504,

    "正源司陽子": 1525527908297216206,

    "竹内希来里": 1525527941784801434,

    "平尾帆夏": 1525527978812113067,

    "平岡海月": 1525528013792481430,

    "藤嶌果歩": 1525528056482103396,

    "宮地すみれ": 1525528085687042181,

    "山下葉留花": 1525528120147447858,

    "渡辺莉奈": 1525528151495676005,


    # 日向坂46 5期生

    "大田美月": 1525528194076381284,

    "大野愛実": 1525528234509471754,

    "片山紗希": 1525528282307493989,

    "蔵盛妃那乃": 1525528407033774221,

    "坂井新奈": 1525528470409449653,

    "佐藤優羽": 1525528532665503845,

    "下田衣珠季": 1525528615951794217,

    "高井俐香": 1525528677813846186,

    "鶴崎仁香": 1525528734172450956,

    "松尾桜": 1525528767634735106,


    # =========================
    # その他
    # =========================

    "ポカ": 1525550922879598854

}

# =========================
# 投稿先取得
# =========================

def get_channels(blog):

    channels = []
    seen = set()

    # 全体チャンネル
    if ARCHIVE_ALL_CHANNEL:

        channel = bot.get_channel(
            ARCHIVE_ALL_CHANNEL
        )

        if channel:
            channels.append(channel)
            seen.add(channel.id)

    # グループチャンネル
    group = blog.get("group")

    group_channel = ARCHIVE_GROUP_CHANNELS.get(group)

    if group_channel:

        channel = bot.get_channel(group_channel)

        if channel and channel.id not in seen:

            channels.append(channel)
            seen.add(channel.id)

    # メンバーチャンネル
    member = normalize_member_name(
        blog.get(
            "member",
            ""
        )
    )

    member_channel_id = ARCHIVE_MEMBER_CHANNELS.get(
        member
    )

    if member_channel:

        channel = bot.get_channel(member_channel)

        if channel and channel.id not in seen:

            channels.append(channel)
            seen.add(channel.id)

    return channels


# =========================
# 画像ダウンロード
# =========================

async def download_image(
    session,
    url,
    index
):

    try:

        timeout = aiohttp.ClientTimeout(
            total=20
        )

        async with session.get(
            url,
            timeout=timeout
        ) as response:

            if response.status != 200:
                return None

            data = await response.read()

            return discord.File(
                io.BytesIO(data),
                filename=f"image_{index}.jpg"
            )

    except Exception as e:

        print(
            "画像取得エラー:",
            e
        )

        return None


# =========================
# 起動時処理
# =========================

@bot.event
async def on_ready():

    print("=" * 40)
    print(f"ログイン成功: {bot.user}")

    init_archive_db()

    print("アーカイブDB初期化完了")

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

    # 巡回中なら、先に停止
    was_running = archive_loop.is_running()


    if was_running:

        archive_loop.cancel()


    try:

        if os.path.exists("data"):

            shutil.rmtree(
                "data"
            )


        os.makedirs(
            "data",
            exist_ok=True
        )


        init_archive_db()


        await ctx.send(
            "🧹 アーカイブDBをリセットしました。"
        )


        print(
            "アーカイブDBをリセットしました。"
        )


    except Exception as e:

        print(
            "アーカイブDBリセットエラー:",
            e
        )


        await ctx.send(
            f"⚠️ DBリセットに失敗しました。\n`{e}`"
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


                        # Discordの添付上限に合わせ、
                        # 10枚ずつ送信する
                        if image_urls:

                            files = []


                            for image_index, image_url in enumerate(
                                image_urls,
                                start=1
                            ):

                                file = await download_image(

                                    session,

                                    image_url,

                                    image_index

                                )


                                if file:

                                    files.append(
                                        file
                                    )


                                if len(files) == 10:

                                    await channel.send(
                                        files=files
                                    )


                                    files = []


                                    await asyncio.sleep(
                                        SEND_DELAY
                                    )


                            # 10枚未満の残りを送信
                            if files:

                                await channel.send(
                                    files=files
                                )


                                await asyncio.sleep(
                                    SEND_DELAY
                                )


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
