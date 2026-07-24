import asyncio
import os
from typing import Iterable

import discord


def get_env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    if value in {"1", "true", "yes", "on", "enabled", "有効"}:
        return True
    if value in {"0", "false", "no", "off", "disabled", "無効"}:
        return False
    return default


LOW_EGRESS_MODE = get_env_bool("LOW_EGRESS_MODE", True)

try:
    _embeds_per_message = int(os.getenv("IMAGE_EMBEDS_PER_MESSAGE", "10"))
except (TypeError, ValueError):
    _embeds_per_message = 10

IMAGE_EMBEDS_PER_MESSAGE = max(1, min(_embeds_per_message, 10))


def clean_http_urls(urls: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in urls:
        url = str(value or "").strip()
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        result.append(url)
    return result


def build_image_embeds(urls: Iterable[str]) -> list[discord.Embed]:
    embeds: list[discord.Embed] = []
    for url in clean_http_urls(urls):
        embed = discord.Embed()
        embed.set_image(url=url)
        embeds.append(embed)
    return embeds


async def send_url_gallery(
    channel: discord.abc.Messageable,
    image_urls: Iterable[str],
    *,
    content: str | None = None,
    header_embed: discord.Embed | None = None,
    send_delay: float = 0.0,
) -> bool:
    """画像本体をRailwayから送らず、URL画像を最大10枚ずつ表示する。"""
    urls = clean_http_urls(image_urls)

    if header_embed is not None:
        await channel.send(content=content, embed=header_embed)
        content = None
    elif content and not urls:
        await channel.send(content=content, suppress_embeds=True)
        return True

    if not urls:
        return True

    embeds = build_image_embeds(urls)
    first = True
    for start in range(0, len(embeds), IMAGE_EMBEDS_PER_MESSAGE):
        group = embeds[start:start + IMAGE_EMBEDS_PER_MESSAGE]
        await channel.send(
            content=content if first else None,
            embeds=group,
        )
        first = False
        if send_delay > 0 and start + IMAGE_EMBEDS_PER_MESSAGE < len(embeds):
            await asyncio.sleep(send_delay)

    return True
