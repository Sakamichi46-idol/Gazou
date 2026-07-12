import re
from datetime import datetime


# =========================
# 日時の統一
# =========================

def normalize_datetime(
    date_str: str
) -> str:
    """
    各公式サイトの日付表記を、

        2020年10月30日 20:15

    の形式へ統一する。

    対応例:

        2026.7.10 17:56
        2026/7/10 17:56
        2026-07-10 17:56
        2026年7月10日 17:56
        2026.7.10
        2026年7月10日
    """

    if not date_str:
        return ""

    date_str = str(
        date_str
    ).strip()


    # 全角スペースなどを通常スペースへ
    date_str = date_str.replace(
        "\u3000",
        " "
    )


    # 連続する空白を1つへ
    date_str = re.sub(
        r"\s+",
        " ",
        date_str
    )


    match = re.search(
        r"""
        (?P<year>\d{4})
        \s*
        [./\-年]
        \s*
        (?P<month>\d{1,2})
        \s*
        [./\-月]
        \s*
        (?P<day>\d{1,2})
        \s*
        日?
        (?:
            \s+
            (?P<hour>\d{1,2})
            \s*
            [:：]
            \s*
            (?P<minute>\d{2})
        )?
        """,
        date_str,
        flags=re.VERBOSE
    )


    if not match:

        print(
            "日時正規化失敗:",
            date_str
        )

        return date_str


    try:

        year = int(
            match.group(
                "year"
            )
        )

        month = int(
            match.group(
                "month"
            )
        )

        day = int(
            match.group(
                "day"
            )
        )

        hour_text = match.group(
            "hour"
        )

        minute_text = match.group(
            "minute"
        )


        # 日付として有効か確認
        datetime(
            year,
            month,
            day
        )


        if (
            hour_text is not None
            and minute_text is not None
        ):

            hour = int(
                hour_text
            )

            minute = int(
                minute_text
            )


            # 時刻として有効か確認
            datetime(
                year,
                month,
                day,
                hour,
                minute
            )


            return (
                f"{year:04d}年"
                f"{month:02d}月"
                f"{day:02d}日 "
                f"{hour:02d}:"
                f"{minute:02d}"
            )


        return (
            f"{year:04d}年"
            f"{month:02d}月"
            f"{day:02d}日"
        )


    except ValueError:

        print(
            "不正な日時:",
            date_str
        )

        return date_str


# =========================
# datetimeへ変換
# =========================

def parse_datetime(
    date_str: str
) -> datetime:
    """
    normalize_datetime()で統一された日時を、
    ソート用のdatetimeへ変換する。

    解析できない日時は最後へ送るため、
    datetime.maxを返す。
    """

    if not date_str:

        return datetime.max


    normalized = normalize_datetime(
        date_str
    )


    formats = (
        "%Y年%m月%d日 %H:%M",
        "%Y年%m月%d日",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%Y.%m.%d %H:%M",
        "%Y.%m.%d",
    )


    for date_format in formats:

        try:

            return datetime.strptime(
                normalized,
                date_format
            )

        except ValueError:

            continue


    print(
        "日時解析失敗:",
        date_str
    )


    return datetime.max


# =========================
# ブログ用ソートキー
# =========================

def blog_datetime_key(
    blog: dict
) -> datetime:
    """
    blogs.sort(key=blog_datetime_key)

    の形で使う。
    """

    return parse_datetime(
        blog.get(
            "date",
            ""
        )
    )


# =========================
# 文字列の整理
# =========================

def clean_text(
    text: str
) -> str:
    """
    メンバー名やタイトル内の余分な空白を整理する。
    """

    if not text:
        return ""

    text = str(
        text
    ).replace(
        "\u3000",
        " "
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# =========================
# メンバー名の空白除去
# =========================

def normalize_member_name(
    name: str
) -> str:
    """
    例:

        冨里 奈央
            ↓
        冨里奈央
    """

    if not name:
        return ""

    return re.sub(
        r"\s+",
        "",
        str(name)
    )
