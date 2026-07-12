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

    # -------------------------
    # 1. 全体チャンネル
    # -------------------------

    if ARCHIVE_ALL_CHANNEL:

        channel = bot.get_channel(
            ARCHIVE_ALL_CHANNEL
        )

        if channel:
            channels.append(channel)



    # -------------------------
    # 2. グループチャンネル
    # -------------------------

    group = blog.get(
        "group"
    )

    group_channel_id = ARCHIVE_GROUP_CHANNELS.get(
        group
    )

    if group_channel_id:

        channel = bot.get_channel(
            group_channel_id
        )

        if channel:
            channels.append(channel)



    # -------------------------
    # 3. メンバーチャンネル
    # -------------------------

    member = blog.get(
        "member"
    )

    member_channel_id = ARCHIVE_MEMBER_CHANNELS.get(
        member
    )


    if member_channel_id:

        channel = bot.get_channel(
            member_channel_id
        )

        if channel:
            channels.append(channel)



    # -------------------------
    # 重複削除
    # -------------------------

    unique = []

    seen = set()


    for channel in channels:

        if channel.id not in seen:

            unique.append(
                channel
            )

            seen.add(
                channel.id
            )


    return unique




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
            "画像ダウンロードエラー:",
            e
        )

        return None


# =========================
# 起動時処理
# =========================

@bot.event
async def on_ready():

    print(
        f"ログイン成功: {bot.user}"
    )


    init_archive_db()


    print(
        "準備完了。"
    )

    print(
        "!archive_start で巡回開始"
    )




# =========================
# 停止コマンド
# =========================

@bot.command()
@commands.is_owner()
async def archive_stop(ctx):

    if archive_loop.is_running():

        archive_loop.cancel()


        await ctx.send(
            "🛑 ブログアーカイブの自動巡回を停止しました。"
        )


    else:

        await ctx.send(
            "⚠️ アーカイブは停止中です。"
        )





# =========================
# 開始コマンド
# =========================

@bot.command()
@commands.is_owner()
async def archive_start(ctx):

    if not archive_loop.is_running():

        archive_loop.start()


        await ctx.send(
            "▶️ ブログアーカイブを開始しました。"
        )


    else:

        await ctx.send(
            "⚠️ すでに動作中です。"
        )





# =========================
# DBリセット
# =========================

@bot.command()
@commands.is_owner()
async def archive_reset(ctx):

    if os.path.exists(
        "data"
    ):

        try:

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


        except Exception as e:


            await ctx.send(
                f"⚠️ リセット失敗: {e}"
            )


    else:


        await ctx.send(
            "⚠️ dataフォルダがありません。"
        )





# =========================
# アーカイブ本体
# =========================

@tasks.loop(seconds=ARCHIVE_INTERVAL)
async def archive_loop():

    # 未アーカイブ記事取得
    blogs = await get_archive_targets()

    if not blogs:
        print("アーカイブ対象なし")
        return

    # 一番古い記事だけ処理
    blog = blogs[0]

    print(
        f"送信開始: "
        f"{blog['group']} "
        f"{blog['member']} "
        f"{blog['date']}"
    )

    try:

        channels = get_channels(blog)

        if not channels:

            print("送信先なし")
            return

        image_urls = await get_images(
            blog["url"]
        )

        embed = discord.Embed(
            title=blog["title"],
            url=blog["url"],
            color=0x00AEEF
        )

        embed.add_field(
            name="グループ",
            value=blog["group"],
            inline=True
        )

        embed.add_field(
            name="メンバー",
            value=blog["member"],
            inline=True
        )

        embed.add_field(
            name="投稿日",
            value=blog["date"],
            inline=False
        )

        embed.set_footer(
            text=f"画像 {len(image_urls)}枚"
        )

        async with aiohttp.ClientSession() as session:

            for channel in channels:

                await channel.send(
                    embed=embed
                )

                await asyncio.sleep(
                    SEND_DELAY
                )

                files = []

                for index, url in enumerate(
                    image_urls,
                    start=1
                ):

                    file = await download_image(
                        session,
                        url,
                        index
                    )

                    if file:
                        files.append(file)

                    # Discordは10枚まで
                    if len(files) == 10:

                        await channel.send(
                            files=files
                        )

                        files = []

                        await asyncio.sleep(
                            SEND_DELAY
                        )

                if files:

                    await channel.send(
                        files=files
                    )

                    await asyncio.sleep(
                        SEND_DELAY
                    )

        # 成功したら保存
        save_archive(blog)

        print(
            "保存完了:",
            blog["url"]
        )

    except Exception as e:

        print(
            "アーカイブ送信エラー:",
            e
        )





# =========================
# BOT起動
# =========================

bot.run(
    TOKEN
)
