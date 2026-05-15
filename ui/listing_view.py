import discord
from typing import Dict, List, Optional

from engine.models import Story


def _sorted_categories(categories: Dict[str, List[Story]]) -> Dict[str, List[Story]]:
    sorted_items = sorted(categories.items(), key=lambda item: item[0])
    return {
        category: sorted(stories, key=lambda story: (story.series, str(story.id), story.title))
        for category, stories in sorted_items
    }


def _story_select_options(stories: List[Story], start_index: int, page_size: int) -> List[discord.SelectOption]:
    options: List[discord.SelectOption] = []
    for story in stories[start_index:start_index + page_size]:
        description = f"ID: {story.id} | سلسلة: {story.series}"
        options.append(
            discord.SelectOption(
                label=story.title[:100],
                value=str(story.id),
                description=description[:100],
                emoji="📖",
            )
        )
    return options


class CategorySelect(discord.ui.Select):
    def __init__(self, parent_view: "BaseLibraryView"):
        self.parent_view = parent_view
        # Slice to 25 to respect Discord limits
        options = [
            discord.SelectOption(label=category[:100], value=category, emoji="🗂️")
            for category in parent_view.category_names[:25]
        ]

        # We assign a static custom_id so it persists. We differentiate by view type.
        view_type = "solo" if isinstance(parent_view, SoloLibraryView) else "multi"
        super().__init__(
            placeholder="1) اختر التصنيف",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"lib_cat_select_{view_type}"
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.current_category = self.values[0]
        self.parent_view.story_page = 0
        self.parent_view.selected_story_id = None
        await self.parent_view.refresh_message(interaction)


class StorySelect(discord.ui.Select):
    def __init__(self, parent_view: "BaseLibraryView"):
        self.parent_view = parent_view
        stories = parent_view.current_stories
        start_index = parent_view.story_page * parent_view.page_size
        options = _story_select_options(stories, start_index, parent_view.page_size)

        view_type = "solo" if isinstance(parent_view, SoloLibraryView) else "multi"
        super().__init__(
            placeholder="2) اختر القصة",
            options=options,
            min_values=1,
            max_values=1,
            disabled=not options,
            custom_id=f"lib_story_select_{view_type}"
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_story_id = self.values[0]
        await self.parent_view.refresh_message(interaction)


class BaseLibraryView(discord.ui.View):
    def __init__(self, categories: Dict[str, List[Story]], timeout: float = 180):
        super().__init__(timeout=timeout)
        self.categories = _sorted_categories(categories)
        self.category_names = list(self.categories.keys())
        self.current_category = self.category_names[0] if self.category_names else None
        self.selected_story_id: Optional[str] = None
        self.page_size = 20
        self.story_page = 0
        self.message: Optional[discord.Message] = None
        self._rebuild_components()

    @property
    def current_stories(self) -> List[Story]:
        if not self.current_category:
            return []
        return self.categories.get(self.current_category, [])

    @property
    def max_page(self) -> int:
        stories = self.current_stories
        if not stories:
            return 0
        return (len(stories) - 1) // self.page_size

    def _rebuild_components(self):
        self.clear_items()
        if self.category_names:
            self.add_item(CategorySelect(self))
            self.add_item(StorySelect(self))
        self.add_item(PrevStoriesButton(self, disabled=self.story_page <= 0))
        self.add_item(NextStoriesButton(self, disabled=self.story_page >= self.max_page))
        self.add_action_components()

    def add_action_components(self):
        return

    def build_embed(self, title: str, description: str, color: discord.Color) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="التدفق: تصنيف ← قصة ← بدء. يمكنك تغيير الاختيار في أي وقت.")

        if not self.current_category:
            embed.add_field(name="لا توجد بيانات", value="لم يتم العثور على تصنيفات حالياً.", inline=False)
            return embed

        stories = self.current_stories
        start_index = self.story_page * self.page_size
        end_index = min(start_index + self.page_size, len(stories))
        page_stories = stories[start_index:end_index]

        embed.add_field(name="التصنيف المختار", value=self.current_category, inline=False)
        embed.add_field(
            name="الصفحة",
            value=f"{self.story_page + 1}/{self.max_page + 1} (إجمالي القصص في التصنيف: {len(stories)})",
            inline=False,
        )

        if page_stories:
            preview = "\n".join(
                f"• #{story.id} | سلسلة {story.series} — {story.title}" for story in page_stories[:8]
            )
            embed.add_field(name="معاينة القصص", value=preview[:1024], inline=False)
        else:
            embed.add_field(name="معاينة القصص", value="لا توجد قصص في هذه الصفحة.", inline=False)

        if self.selected_story_id is not None:
            selected_story = next((story for story in stories if str(story.id) == str(self.selected_story_id)), None)
            if selected_story:
                embed.add_field(
                    name="القصة المختارة",
                    value=(
                        f"**{selected_story.title}**\n"
                        f"ID: `{selected_story.id}` | سلسلة: `{selected_story.series}`\n"
                        f"{selected_story.description[:240]}"
                    ),
                    inline=False,
                )

        return embed

    async def refresh_message(self, interaction: discord.Interaction):
        self.story_page = max(0, min(self.story_page, self.max_page))
        self._rebuild_components()
        embed = self.render_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    def render_embed(self) -> discord.Embed:
        raise NotImplementedError


class PrevStoriesButton(discord.ui.Button):
    def __init__(self, parent_view: BaseLibraryView, disabled: bool = False):
        self.parent_view = parent_view
        super().__init__(
            label="⬅️ السابق",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id="lib_prev_page",
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.story_page > 0:
            self.parent_view.story_page -= 1
            self.parent_view.selected_story_id = None
        await self.parent_view.refresh_message(interaction)


class NextStoriesButton(discord.ui.Button):
    def __init__(self, parent_view: BaseLibraryView, disabled: bool = False):
        self.parent_view = parent_view
        super().__init__(
            label="التالي ➡️",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id="lib_next_page",
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.story_page < self.parent_view.max_page:
            self.parent_view.story_page += 1
            self.parent_view.selected_story_id = None
        await self.parent_view.refresh_message(interaction)


class StartSoloButton(discord.ui.Button):
    def __init__(self, parent_view: "SoloLibraryView"):
        self.parent_view = parent_view
        super().__init__(label="3) ▶️ ابدأ القصة", style=discord.ButtonStyle.success, row=3, custom_id="lib_start_solo")

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.selected_story_id is None:
            await interaction.response.send_message("اختر قصة أولاً من القائمة.", ephemeral=True)
            return

        from cogs.solo_cog import start_solo_interaction

        await start_solo_interaction(interaction, self.parent_view.selected_story_id)


class StartEventButton(discord.ui.Button):
    def __init__(self, parent_view: "MultiLibraryView"):
        self.parent_view = parent_view
        super().__init__(label="3) 🚀 بدء الحدث", style=discord.ButtonStyle.primary, row=3, custom_id="lib_start_event")

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.selected_story_id is None:
            await interaction.response.send_message("اختر قصة جماعية أولاً.", ephemeral=True)
            return

        guild_permissions = getattr(interaction.user, "guild_permissions", None)
        if not guild_permissions or not guild_permissions.manage_guild:
            await interaction.response.send_message("❌ هذا الزر للمشرفين فقط.", ephemeral=True)
            return

        bot = interaction.client
        if bot.event_manager.active_event:
            await interaction.response.send_message("❌ يوجد حدث نشط حالياً. أوقفه ثم أعد المحاولة.", ephemeral=True)
            return

        story = bot.story_manager.resolve_story(self.parent_view.selected_story_id, game_mode="multi")
        if not story or story.game_mode != "multi":
            await interaction.response.send_message("❌ القصة المختارة غير متاحة كحدث جماعي.", ephemeral=True)
            return

        if interaction.channel is None:
            await interaction.response.send_message("❌ لا يمكن تشغيل الحدث هنا.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"✅ سيتم بدء الحدث الآن: **{story.title}**\n⏱️ زمن التصويت: 30 ثانية.",
            ephemeral=True,
        )
        bot.loop.create_task(bot.event_manager.start_event(interaction.channel, story.id, voting_timeout=30.0))


class SoloLibraryView(BaseLibraryView):
    def __init__(self, categories: Dict[str, List[Story]], timeout: float = 180):
        super().__init__(categories, timeout=timeout)

    def add_action_components(self):
        self.add_item(StartSoloButton(self))

    def render_embed(self) -> discord.Embed:
        return self.build_embed(
            title="👤 مكتبة القصص الفردية",
            description="اختَر التصنيف ثم القصة من القوائم، وبعدها اضغط زر البدء.",
            color=discord.Color.purple(),
        )


class MultiLibraryView(BaseLibraryView):
    def __init__(self, categories: Dict[str, List[Story]], timeout: float = 180):
        super().__init__(categories, timeout=timeout)

    def add_action_components(self):
        self.add_item(StartEventButton(self))

    def render_embed(self) -> discord.Embed:
        return self.build_embed(
            title="👥 مكتبة الفعاليات الجماعية",
            description="اختَر التصنيف ثم القصة الجماعية، ويمكن للمشرف بدء الحدث مباشرة من الزر.",
            color=discord.Color.blue(),
        )
