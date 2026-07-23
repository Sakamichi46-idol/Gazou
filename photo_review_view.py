from __future__ import annotations

import asyncio
from typing import Any

import discord
from discord.ext import commands

from photo_database import (
    get_pending_person_reviews,
    get_photo_image,
    get_image_people,
    set_confirmed_image_people,
)


def _split_names(*values: Any) -> list[str]:
    names: list[str] = []
    for value in values:
        text = str(value or "").replace("、", ",")
        for item in text.split(","):
            name = item.strip()
            if name and name not in names:
                names.append(name)
    return names


class PersonNameModal(discord.ui.Modal):
    def __init__(self, parent: "PhotoReviewView", *, mode: str) -> None:
        self.parent_view = parent
        self.mode = mode
        title = "人物を追加" if mode == "add" else "人物を削除"
        super().__init__(title=title, timeout=300)

        self.person_names = discord.ui.TextInput(
            label="人物名",
            placeholder="例: 井上和, 菅原咲月",
            required=True,
            max_length=300,
        )
        self.add_item(self.person_names)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        names = _split_names(str(self.person_names.value))
        if not names:
            await interaction.response.send_message(
                "⚠️ 人物名を入力してください。",
                ephemeral=True,
            )
            return

        if self.mode == "add":
            for name in names:
                if name not in self.parent_view.selected_people:
                    self.parent_view.selected_people.append(name)
            message = f"➕ **{'、'.join(names)}** を追加しました。"
        else:
            removed = [
                name for name in names
                if name in self.parent_view.selected_people
            ]
            self.parent_view.selected_people = [
                name for name in self.parent_view.selected_people
                if name not in names
            ]
            message = (
                f"➖ **{'、'.join(removed)}** を削除しました。"
                if removed
                else "⚠️ 選択中の人物には含まれていません。"
            )

        self.parent_view.rebuild_components()
        await interaction.response.edit_message(
            embed=self.parent_view.build_embed(notice=message),
            view=self.parent_view,
        )


class CandidateSelect(discord.ui.Select):
    def __init__(self, parent: "PhotoReviewView") -> None:
        self.parent_view = parent
        current = parent.current_review
        available = _split_names(
            current.get("candidate_people"),
            current.get("candidates"),
            current.get("ai_person_name"),
            current.get("confirmed_people"),
        )

        for selected in parent.selected_people:
            if selected not in available:
                available.append(selected)

        options = [
            discord.SelectOption(
                label=name[:100],
                value=name[:100],
                default=name in parent.selected_people,
            )
            for name in available[:25]
        ]

        if not options:
            options = [
                discord.SelectOption(
                    label="候補なし（人物追加を使用）",
                    value="__none__",
                    default=False,
                )
            ]

        super().__init__(
            placeholder="写っている人物を複数選択",
            min_values=0,
            max_values=len(options),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_people = [
            value for value in self.values if value != "__none__"
        ]
        self.parent_view.rebuild_components()
        await interaction.response.edit_message(
            embed=self.parent_view.build_embed(
                notice="☑️ 選択内容を更新しました。"
            ),
            view=self.parent_view,
        )


class PhotoReviewView(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        owner_id: int,
        reviews: list[dict[str, Any]],
        *,
        edit_mode: bool = False,
    ) -> None:
        super().__init__(timeout=900)
        self.bot = bot
        self.owner_id = int(owner_id)
        self.reviews = reviews
        self.edit_mode = bool(edit_mode)
        self.index = 0
        self.selected_people: list[str] = []
        self.message: discord.Message | None = None
        self._load_current_selection()
        self.rebuild_components()

    @property
    def current_review(self) -> dict[str, Any]:
        return self.reviews[self.index]

    def _load_current_selection(self) -> None:
        current = self.current_review
        confirmed = _split_names(current.get("confirmed_people"))
        candidates = _split_names(
            current.get("candidate_people"),
            current.get("candidates"),
            current.get("ai_person_name"),
        )
        self.selected_people = confirmed or candidates

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "⚠️ このレビュー画面は、コマンドを実行したオーナーだけ操作できます。",
                ephemeral=True,
            )
            return False
        return True

    def rebuild_components(self) -> None:
        self.clear_items()
        self.add_item(CandidateSelect(self))

        confirm_button = discord.ui.Button(
            label="確定",
            emoji="✅",
            style=discord.ButtonStyle.success,
            row=1,
        )
        confirm_button.callback = self.confirm_callback
        self.add_item(confirm_button)

        add_button = discord.ui.Button(
            label="人物追加",
            emoji="➕",
            style=discord.ButtonStyle.primary,
            row=1,
        )
        add_button.callback = self.add_person_callback
        self.add_item(add_button)

        remove_button = discord.ui.Button(
            label="人物削除",
            emoji="➖",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        remove_button.callback = self.remove_person_callback
        self.add_item(remove_button)

        none_button = discord.ui.Button(
            label="人物なし",
            emoji="🚫",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        none_button.callback = self.none_callback
        self.add_item(none_button)

        previous_button = discord.ui.Button(
            label="前へ",
            emoji="◀️",
            style=discord.ButtonStyle.secondary,
            disabled=self.index <= 0,
            row=2,
        )
        previous_button.callback = self.previous_callback
        self.add_item(previous_button)

        next_button = discord.ui.Button(
            label="次へ",
            emoji="▶️",
            style=discord.ButtonStyle.secondary,
            disabled=self.index >= len(self.reviews) - 1,
            row=2,
        )
        next_button.callback = self.next_callback
        self.add_item(next_button)

        close_button = discord.ui.Button(
            label="終了",
            emoji="⏹️",
            style=discord.ButtonStyle.danger,
            row=2,
        )
        close_button.callback = self.close_callback
        self.add_item(close_button)

    def build_embed(self, notice: str = "") -> discord.Embed:
        review = self.current_review
        selected = "、".join(self.selected_people) or "人物なし"
        candidates = _split_names(
            review.get("candidate_people"),
            review.get("candidates"),
            review.get("ai_person_name"),
        )
        candidate_text = "\n".join(f"・{name}" for name in candidates) or "候補なし"

        embed = discord.Embed(
            title="✏️ 写真人物タグ編集" if self.edit_mode else "🧐 写真人物レビュー",
            description=(
                f"**画像ID：{review['image_id']}**\n"
                + (f"編集モード\n" if self.edit_mode else f"Review ID：{review.get('review_id', '-')}\n")
                + f"{self.index + 1}件目 / {len(self.reviews)}件"
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="📝 ブログ情報",
            value=(
                f"グループ：{review.get('group_name') or '不明'}\n"
                f"投稿者：{review.get('member_name') or '不明'}\n"
                f"投稿日：{review.get('published_at') or '不明'}\n"
                f"タイトル：{review.get('title') or '不明'}"
            )[:1024],
            inline=False,
        )
        embed.add_field(
            name="🤖 候補",
            value=candidate_text[:1024],
            inline=True,
        )
        embed.add_field(
            name="☑️ 現在の選択",
            value=selected[:1024],
            inline=True,
        )
        if notice:
            embed.add_field(name="操作結果", value=notice[:1024], inline=False)

        image_url = str(review.get("image_url") or "").strip()
        if image_url.startswith(("http://", "https://")):
            embed.set_image(url=image_url)
        embed.set_footer(text=("現在の登録を修正し、「確定」を押すと上書き保存されます。" if self.edit_mode else "候補を選び、必要なら人物を追加・削除してから「確定」を押してください。"))
        return embed

    async def confirm_callback(self, interaction: discord.Interaction) -> None:
        review = self.current_review
        names = list(dict.fromkeys(self.selected_people))
        await asyncio.to_thread(
            set_confirmed_image_people,
            int(review["image_id"]),
            names,
            confirmed_by=str(interaction.user.id),
            note="Discord photo edit" if self.edit_mode else "Discord button review",
        )

        completed_image_id = int(review["image_id"])

        if self.edit_mode:
            for child in self.children:
                if hasattr(child, "disabled"):
                    child.disabled = True
            display = "人物なし" if not names else "、".join(names)
            embed = self.build_embed(
                notice=f"✅ 画像ID {completed_image_id} の人物を「{display}」に更新しました。"
            )
            embed.color = discord.Color.green()
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
            return

        self.reviews.pop(self.index)

        if not self.reviews:
            self.clear_items()
            embed = discord.Embed(
                title="✅ レビュー完了",
                description=(
                    f"画像ID **{completed_image_id}** を確定しました。\n"
                    "現在、確認待ちの画像はありません。"
                ),
                color=discord.Color.green(),
            )
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
            return

        if self.index >= len(self.reviews):
            self.index = len(self.reviews) - 1
        self._load_current_selection()
        self.rebuild_components()
        display = "人物なし" if not names else "、".join(names)
        await interaction.response.edit_message(
            embed=self.build_embed(
                notice=f"✅ 画像ID {completed_image_id} を「{display}」で確定しました。"
            ),
            view=self,
        )

    async def add_person_callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(PersonNameModal(self, mode="add"))

    async def remove_person_callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(PersonNameModal(self, mode="remove"))

    async def none_callback(self, interaction: discord.Interaction) -> None:
        self.selected_people = []
        self.rebuild_components()
        await interaction.response.edit_message(
            embed=self.build_embed(notice="🚫 人物なしを選択しました。"),
            view=self,
        )

    async def previous_callback(self, interaction: discord.Interaction) -> None:
        if self.index > 0:
            self.index -= 1
            self._load_current_selection()
        self.rebuild_components()
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def next_callback(self, interaction: discord.Interaction) -> None:
        if self.index < len(self.reviews) - 1:
            self.index += 1
            self._load_current_selection()
        self.rebuild_components()
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def close_callback(self, interaction: discord.Interaction) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True
        await interaction.response.edit_message(
            embed=self.build_embed(notice="⏹️ レビュー画面を終了しました。"),
            view=self,
        )
        self.stop()

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[Any],
    ) -> None:
        print(f"写真レビュー画面エラー: {error}")
        message = "⚠️ 操作中にエラーが発生しました。もう一度 `!review_list` を実行してください。"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            pass

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


async def send_photo_review_view(ctx: commands.Context, limit: int = 100) -> None:
    reviews = await asyncio.to_thread(get_pending_person_reviews, limit)
    if not reviews:
        await ctx.send("✅ 画像の確認待ちはありません。")
        return

    view = PhotoReviewView(
        bot=ctx.bot,
        owner_id=ctx.author.id,
        reviews=reviews,
    )
    message = await ctx.send(embed=view.build_embed(), view=view)
    view.message = message


async def send_photo_edit_view(ctx: commands.Context, image_id: int) -> None:
    """確定済みを含む任意の画像について、人物タグ編集画面を開く。"""
    image = await asyncio.to_thread(get_photo_image, int(image_id))
    if not image:
        await ctx.send(f"⚠️ 画像ID **{image_id}** は見つかりません。")
        return

    people = await asyncio.to_thread(get_image_people, int(image_id))
    confirmed = [
        str(row.get("person_name") or "").strip()
        for row in people
        if row.get("relation_status") == "confirmed" and str(row.get("person_name") or "").strip()
    ]
    candidates = [
        str(row.get("person_name") or "").strip()
        for row in people
        if row.get("relation_status") == "candidate" and str(row.get("person_name") or "").strip()
    ]

    review = dict(image)
    # get_photo_image() は主キーを ``id`` で返すため、
    # レビュー画面が参照する ``image_id`` を明示的に追加する。
    review.update({
        "image_id": int(image["id"]),
        "review_id": "edit",
        "confirmed_people": "、".join(dict.fromkeys(confirmed)),
        "candidate_people": "、".join(dict.fromkeys(candidates)),
    })

    view = PhotoReviewView(
        bot=ctx.bot,
        owner_id=ctx.author.id,
        reviews=[review],
        edit_mode=True,
    )
    message = await ctx.send(embed=view.build_embed(), view=view)
    view.message = message
