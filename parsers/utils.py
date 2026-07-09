import re


def normalize_datetime(date_text):
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

    result = f"{year}年{month}月{day}日"

    # 時刻がある場合
    if len(numbers) >= 5:
        hour = numbers[3].zfill(2)
        minute = numbers[4].zfill(2)

        result += f" {hour}:{minute}"

    return result
