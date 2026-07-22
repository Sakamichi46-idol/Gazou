import asyncio
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Any

import aiohttp
import discord
from discord.ext import commands

from photo_ai_analyzer import analyze_photo_image
from photo_database import (
    get_all_people,
    get_image_people,
    set_confirmed_image_people,
    get_connection,
    get_photo_db_counts,
    get_photo_image,
    get_photo_storage_stats,
    reset_image_analysis_status,
    reset_image_download_status,
    save_manual_tag,
)
from photo_image_downloader import download_photo_image
from photo_search import send_photo_search_results, send_photo_author_search_results


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with closing(get_connection()) as connection:
        cursor = connection.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def _row(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = _rows(query, params)
    return rows[0] if rows else None


def _execute(query: str, params: tuple[Any, ...] = ()) -> int:
    with closing(get_connection()) as connection:
        cursor = connection.execute(query, params)
        connection.commit()
        return int(cursor.rowcount)


def _format_bytes(size: int) -> str:
    value = float(max(int(size or 0), 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def _get_redownload_record(image_id: int) -> dict[str, Any] | None:
    return _row(
        """
        SELECT
            photo_images.id,
            photo_images.blog_id,
            photo_images.image_url,
            photo_images.image_index,
            photo_blogs.group_name,
            photo_blogs.member_name,
            photo_blogs.published_at
        FROM photo_images
        JOIN photo_blogs ON photo_blogs.id = photo_images.blog_id
        WHERE photo_images.id = ?
        """,
        (image_id,),
    )


async def _redownload_one(session: aiohttp.ClientSession, image_id: int) -> dict[str, Any]:
    record = await asyncio.to_thread(_get_redownload_record, image_id)
    if not record:
        return {"success": False, "error": "画像IDが見つかりません。"}

    await asyncio.to_thread(reset_image_download_status, image_id)

    return await download_photo_image(
        session,
        image_id=int(record["id"]),
        blog_id=int(record["blog_id"]),
        image_url=str(record["image_url"]),
        image_index=int(record["image_index"]),
        group_name=str(record["group_name"]),
        member_name=str(record["member_name"]),
        published_at=str(record["published_at"]),
    )


def register_photo_commands(bot: commands.Bot) -> None:

    @bot.command(name="photo_search")
    
    async def photo_search_command(ctx: commands.Context, *, query: str = "") -> None:
        await send_photo_search_results(ctx, query)

    @bot.command(name="photo_search_author")
    
    async def photo_search_author_command(ctx: commands.Context, *, author_name: str = "") -> None:
        await send_photo_author_search_results(ctx, author_name)

    @bot.command(name="photo_person_set")
    @commands.is_owner()
    async def photo_person_set_command(ctx: commands.Context, image_id: int, *, person_names: str = "") -> None:
        names = [name.strip() for name in person_names.replace("、", ",").split(",") if name.strip()]
        if not names:
            await ctx.send("使い方: `!photo_person_set 画像ID 人物名`\n複数人: `!photo_person_set 125 菅原咲月,井上和`")
            return
        if not await asyncio.to_thread(get_photo_image, image_id):
            await ctx.send("⚠️ 画像IDが見つかりません。")
            return
        await asyncio.to_thread(
            set_confirmed_image_people, image_id, names,
            confirmed_by=str(ctx.author.id), note="Discord command",
        )
        await ctx.send(f"✅ 画像ID **{image_id}** の人物を **{'、'.join(names)}** として確定しました。")

    @bot.command(name="photo_person_clear")
    @commands.is_owner()
    async def photo_person_clear_command(ctx: commands.Context, image_id: int) -> None:
        if not await asyncio.to_thread(get_photo_image, image_id):
            await ctx.send("⚠️ 画像IDが見つかりません。")
            return
        await asyncio.to_thread(
            set_confirmed_image_people, image_id, [],
            confirmed_by=str(ctx.author.id), note="人物なし・判定解除",
        )
        await ctx.send(f"🧹 画像ID **{image_id}** の確定人物を解除しました。")

    @bot.command(name="person_list")
    
    async def person_list_command(ctx: commands.Context) -> None:
        people = await asyncio.to_thread(get_all_people)
        if not people:
            await ctx.send("👤 登録人物はまだありません。")
            return

        lines = [f"{index}. {person.get('person_name', '名称不明')}" for index, person in enumerate(people, 1)]
        text = "👤 **登録人物一覧**\n" + "\n".join(lines)
        for start in range(0, len(text), 1900):
            await ctx.send(text[start:start + 1900])

    @bot.command(name="person_info")
    
    async def person_info_command(ctx: commands.Context, *, person_name: str = "") -> None:
        person_name = person_name.strip()
        if not person_name:
            await ctx.send("使い方: `!person_info 人物名`")
            return

        info = await asyncio.to_thread(
            _row,
            """
            SELECT
                photo_people.id,
                photo_people.person_name,
                photo_people.group_name,
                photo_people.generation_name,
                COUNT(DISTINCT photo_faces.id) AS confirmed_faces
            FROM photo_people
            LEFT JOIN photo_faces
                ON photo_faces.confirmed_person_id = photo_people.id
            WHERE photo_people.person_name = ?
            GROUP BY photo_people.id
            """,
            (person_name,),
        )
        ai_count = await asyncio.to_thread(
            _row,
            "SELECT COUNT(*) AS count FROM photo_ai_analysis WHERE person_name = ?",
            (person_name,),
        )
        if not info and not ai_count:
            await ctx.send("⚠️ その人物は見つかりませんでした。")
            return

        await ctx.send(
            "👤 **人物情報**\n"
            f"名前: **{person_name}**\n"
            f"グループ: **{(info or {}).get('group_name', '') or '未登録'}**\n"
            f"世代: **{(info or {}).get('generation_name', '') or '未登録'}**\n"
            f"AI解析画像: **{int((ai_count or {}).get('count', 0))}件**\n"
            f"顔確認済み: **{int((info or {}).get('confirmed_faces', 0))}件**"
        )

    @bot.command(name="tag_add")
    @commands.is_owner()
    async def tag_add_command(ctx: commands.Context, image_id: int, *, tag: str = "") -> None:
        tag = tag.strip()
        if not tag:
            await ctx.send("使い方: `!tag_add 画像ID タグ`")
            return
        image = await asyncio.to_thread(get_photo_image, image_id)
        if not image:
            await ctx.send("⚠️ 画像IDが見つかりません。")
            return
        await asyncio.to_thread(
            save_manual_tag,
            image_id,
            category="manual",
            tag=tag,
            created_by=str(ctx.author.id),
            note="Discord command",
        )
        await ctx.send(f"🏷️ 画像ID **{image_id}** に `{tag}` を追加しました。")

    @bot.command(name="tag_remove")
    @commands.is_owner()
    async def tag_remove_command(ctx: commands.Context, image_id: int, *, tag: str = "") -> None:
        tag = tag.strip()
        if not tag:
            await ctx.send("使い方: `!tag_remove 画像ID タグ`")
            return
        deleted = await asyncio.to_thread(
            _execute,
            "DELETE FROM photo_manual_tags WHERE image_id = ? AND tag = ?",
            (image_id, tag),
        )
        if deleted:
            await ctx.send(f"🗑️ 画像ID **{image_id}** から `{tag}` を削除しました。")
        else:
            await ctx.send("⚠️ 指定されたタグは見つかりませんでした。")

    @bot.command(name="ai_retry")
    @commands.is_owner()
    async def ai_retry_command(ctx: commands.Context, image_id: int | None = None, limit: int = 10) -> None:
        if image_id is not None:
            image = await asyncio.to_thread(get_photo_image, image_id)
            if not image:
                await ctx.send("⚠️ 画像IDが見つかりません。")
                return
            await asyncio.to_thread(reset_image_analysis_status, image_id)
            await ctx.send(f"🤖 画像ID **{image_id}** を再解析します。")
            result = await analyze_photo_image(image_id)
            await ctx.send(f"解析結果: **{result.get('status', '不明')}**")
            return

        limit = max(1, min(int(limit), 50))
        failed = await asyncio.to_thread(
            _rows,
            "SELECT id FROM photo_images WHERE analysis_status IN ('failed', 'review') ORDER BY id LIMIT ?",
            (limit,),
        )
        if not failed:
            await ctx.send("✅ 再解析対象はありません。")
            return
        await ctx.send(f"🤖 {len(failed)}件の再解析を開始します。")
        completed = 0
        for item in failed:
            target_id = int(item["id"])
            await asyncio.to_thread(reset_image_analysis_status, target_id)
            result = await analyze_photo_image(target_id)
            if result.get("status") == "completed":
                completed += 1
        await ctx.send(f"✅ 再解析終了: 完了 **{completed}件** / 対象 **{len(failed)}件**")

    @bot.command(name="photo_redownload")
    @commands.is_owner()
    async def photo_redownload_command(ctx: commands.Context, image_id: int | None = None, limit: int = 10) -> None:
        if image_id is None:
            limit = max(1, min(int(limit), 50))
            targets = await asyncio.to_thread(
                _rows,
                "SELECT id FROM photo_images WHERE download_status = 'failed' ORDER BY id LIMIT ?",
                (limit,),
            )
        else:
            targets = [{"id": image_id}]

        if not targets:
            await ctx.send("✅ 再ダウンロード対象はありません。")
            return

        await ctx.send(f"🔄 {len(targets)}件の再ダウンロードを開始します。")
        succeeded = 0
        timeout = aiohttp.ClientTimeout(total=None, connect=30, sock_read=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for item in targets:
                result = await _redownload_one(session, int(item["id"]))
                if result.get("success"):
                    succeeded += 1
        await ctx.send(f"✅ 再ダウンロード終了: 成功 **{succeeded}件** / 対象 **{len(targets)}件**")

    @bot.command(name="photo_stats")
    
    async def photo_stats_command(ctx: commands.Context) -> None:
        counts, storage = await asyncio.gather(
            asyncio.to_thread(get_photo_db_counts),
            asyncio.to_thread(get_photo_storage_stats),
        )
        analysis = await asyncio.to_thread(
            _row,
            """
            SELECT
                SUM(CASE WHEN analysis_status = 'completed' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN analysis_status = 'pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN analysis_status = 'failed' THEN 1 ELSE 0 END) AS failed,
                SUM(CASE WHEN analysis_status = 'review' THEN 1 ELSE 0 END) AS review
            FROM photo_images
            """,
        ) or {}
        await ctx.send(
            "📊 **写真DB統計**\n"
            f"ブログ: **{counts.get('blogs', 0)}件**\n"
            f"画像: **{counts.get('images', 0)}件**\n"
            f"人物: **{counts.get('people', 0)}人**\n"
            f"AI完了: **{int(analysis.get('completed') or 0)}件**\n"
            f"AI待ち: **{int(analysis.get('pending') or 0)}件**\n"
            f"AI確認待ち: **{int(analysis.get('review') or 0)}件**\n"
            f"AI失敗: **{int(analysis.get('failed') or 0)}件**\n"
            f"保存容量: **{_format_bytes(storage.get('total_size', 0))}**"
        )

    @bot.command(name="photo_recent")
    
    async def photo_recent_command(ctx: commands.Context, limit: int = 10) -> None:
        limit = max(1, min(int(limit), 30))
        recent = await asyncio.to_thread(
            _rows,
            """
            SELECT photo_images.id, photo_images.image_index,
                   photo_blogs.group_name, photo_blogs.member_name,
                   photo_blogs.title, photo_blogs.published_at
            FROM photo_images
            JOIN photo_blogs ON photo_blogs.id = photo_images.blog_id
            ORDER BY photo_images.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        if not recent:
            await ctx.send("📷 保存画像はまだありません。")
            return
        lines = [
            f"`ID {item['id']}` {item['group_name']} / {item['member_name']} / {item['published_at']}"
            for item in recent
        ]
        await ctx.send("🕒 **最近登録された画像**\n" + "\n".join(lines))

    @bot.command(name="favorite_add")
    
    async def favorite_add_command(ctx: commands.Context, image_id: int) -> None:
        if not await asyncio.to_thread(get_photo_image, image_id):
            await ctx.send("⚠️ 画像IDが見つかりません。")
            return
        await asyncio.to_thread(
            _execute,
            "INSERT OR IGNORE INTO photo_favorites (image_id, discord_user_id, created_at) VALUES (?, ?, ?)",
            (image_id, str(ctx.author.id), _now()),
        )
        await ctx.send(f"⭐ 画像ID **{image_id}** をお気に入りに追加しました。")

    @bot.command(name="favorite_remove")
    
    async def favorite_remove_command(ctx: commands.Context, image_id: int) -> None:
        deleted = await asyncio.to_thread(
            _execute,
            "DELETE FROM photo_favorites WHERE image_id = ? AND discord_user_id = ?",
            (image_id, str(ctx.author.id)),
        )
        await ctx.send("⭐ お気に入りから削除しました。" if deleted else "⚠️ お気に入りに登録されていません。")

    @bot.command(name="favorite_list")
    
    async def favorite_list_command(ctx: commands.Context, limit: int = 20) -> None:
        limit = max(1, min(int(limit), 50))
        favorites = await asyncio.to_thread(
            _rows,
            """
            SELECT photo_images.id, photo_blogs.group_name, photo_blogs.member_name,
                   photo_blogs.published_at
            FROM photo_favorites
            JOIN photo_images ON photo_images.id = photo_favorites.image_id
            JOIN photo_blogs ON photo_blogs.id = photo_images.blog_id
            WHERE photo_favorites.discord_user_id = ?
            ORDER BY photo_favorites.id DESC
            LIMIT ?
            """,
            (str(ctx.author.id), limit),
        )
        if not favorites:
            await ctx.send("⭐ お気に入りはまだありません。")
            return
        lines = [f"`ID {x['id']}` {x['group_name']} / {x['member_name']} / {x['published_at']}" for x in favorites]
        await ctx.send("⭐ **お気に入り一覧**\n" + "\n".join(lines))

    @bot.command(name="review_list")
    @commands.is_owner()
    async def review_list_command(ctx: commands.Context, limit: int = 10) -> None:
        limit = max(1, min(int(limit), 30))
        reviews = await asyncio.to_thread(
            _rows,
            """
            SELECT photo_review_queue.id, photo_review_queue.image_id,
                   photo_review_queue.review_type, photo_review_queue.question,
                   photo_review_queue.candidates
            FROM photo_review_queue
            WHERE status = 'pending'
            ORDER BY id
            LIMIT ?
            """,
            (limit,),
        )
        if not reviews:
            await ctx.send("✅ 画像の確認待ちはありません。")
            return
        lines = [
            f"`Review {x['id']}` 画像ID `{x['image_id']}` / {x['review_type']}\n{x['question']}\n候補: {x['candidates']}"
            for x in reviews
        ]
        await ctx.send("🧐 **確認待ち一覧**\n\n" + "\n\n".join(lines))

    @bot.command(name="review_done")
    @commands.is_owner()
    async def review_done_command(ctx: commands.Context, review_id: int, *, selected_value: str = "") -> None:
        review = await asyncio.to_thread(
            _row,
            "SELECT * FROM photo_review_queue WHERE id = ? AND status = 'pending'",
            (review_id,),
        )
        if not review:
            await ctx.send("⚠️ 指定された確認待ちは見つかりません。")
            return

        selected_value = selected_value.strip()
        if review.get("review_type") == "person_identity":
            if not selected_value:
                await ctx.send(
                    "⚠️ 写っている人物名を入力してください。\n"
                    f"例: `!review_done {review_id} 井上和`\n"
                    f"複数人: `!review_done {review_id} 菅原咲月,井上和`\n"
                    f"人物なし: `!review_done {review_id} なし`"
                )
                return
            names = [] if selected_value in {"なし", "人物なし", "不明"} else [
                name.strip() for name in selected_value.replace("、", ",").split(",") if name.strip()
            ]
            await asyncio.to_thread(
                set_confirmed_image_people, int(review["image_id"]), names,
                confirmed_by=str(ctx.author.id), note="Discord review",
            )
            display = "人物なし" if not names else "、".join(names)
            await ctx.send(f"✅ Review **{review_id}** を完了し、画像ID **{review['image_id']}** を **{display}** として確定しました。")
            return

        updated = await asyncio.to_thread(
            _execute,
            """
            UPDATE photo_review_queue
            SET status = 'completed', reviewed_by = ?, selected_value = ?,
                review_note = 'Discord command', reviewed_at = ?, updated_at = ?
            WHERE id = ? AND status = 'pending'
            """,
            (str(ctx.author.id), selected_value, _now(), _now(), review_id),
        )
        await ctx.send(f"✅ Review **{review_id}** を完了にしました。" if updated else "⚠️ 指定された確認待ちは見つかりません。")

