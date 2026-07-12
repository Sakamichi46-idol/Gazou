import re


def normalize_datetime(date_str: str) -> str:
    """
    各グループの日付を

    2026年07月10日 17:56

    の形式へ統一する。
    """

    if not date_str:
        return ""

    date_str = date_str.strip()

    match = re.search(
        r"(\d{4})[./年](\d{1,2})[./月](\d{1,2})日?\s*(\d{1,2})?[:：]?(\d{2})?",
        date_str
    )

    if not match:
        return date_str

    year = match.group(1)
    month = int(match.group(2))
    day = int(match.group(3))

    hour = match.group(4)
    minute = match.group(5)

    if hour is not None and minute is not None:
        return (
            f"{year}年"
            f"{month:02d}月"
            f"{day:02d}日 "
            f"{int(hour):02d}:{minute}"
        )

    return (
        f"{year}年"
        f"{month:02d}月"
        f"{day:02d}日"
    )
