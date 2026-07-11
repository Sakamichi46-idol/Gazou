import re


def normalize_datetime(date_str: str) -> str:
    """
    日付を統一フォーマットへ変換する。

    例
    2026.7.10 17:56
        ↓
    2026年07月10日 17:56
    """

    if not date_str:
        return ""

    date_str = date_str.strip()

    match = re.match(
        r"(\d{4})[./年](\d{1,2})[./月](\d{1,2})日?\s*(\d{1,2}:\d{2})?",
        date_str
    )

    if not match:
        return date_str

    year = match.group(1)
    month = int(match.group(2))
    day = int(match.group(3))
    time = match.group(4)

    if time:
        return (
            f"{year}年"
            f"{month:02d}月"
            f"{day:02d}日 "
            f"{time}"
        )

    return (
        f"{year}年"
        f"{month:02d}月"
        f"{day:02d}日"
    )
