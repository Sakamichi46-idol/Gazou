import re


def normalize_date(date_text):
    if not date_text:
        return ""

    numbers = re.findall(
        r"\d+",
        date_text
    )

    if len(numbers) < 3:
        return date_text

    year = numbers[0]
    month = numbers[1].zfill(2)
    day = numbers[2].zfill(2)

    return f"{year}年{month}月{day}日"
