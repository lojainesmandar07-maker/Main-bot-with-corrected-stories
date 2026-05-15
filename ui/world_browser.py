import discord
from discord.ui import View, Select, Button
from ui.embeds import EmbedBuilder

WORLD_CONFIG = {
    "solo": {
        "name": "القصص الفردية",
        "desc": "مجموعة من القصص المنوعة للعب الفردي.",
        "emoji": "👤",
        "color": discord.Color.dark_grey()
    },
    "fantasy": {
        "name": "عالم الفانتازيا",
        "desc": "عالم السحر والمخلوقات الأسطورية.",
        "emoji": "🐉",
        "color": discord.Color.gold()
    },
    "past": {
        "name": "عالم الماضي",
        "desc": "رحلة عبر الزمن إلى العصور القديمة.",
        "emoji": "⏳",
        "color": discord.Color.gold()
    },
    "future": {
        "name": "عالم المستقبل",
        "desc": "تكنولوجيا متقدمة وخيال علمي.",
        "emoji": "🚀",
        "color": discord.Color.blue()
    },
    "alternate": {
        "name": "العالم البديل",
        "desc": "حقائق بديلة وأبعاد موازية.",
        "emoji": "🌀",
        "color": discord.Color.dark_magenta()
    }
}


class WorldBrowserPersistentRouter(View):
    """Single persistent view for world/category/story browser component callbacks."""

    STALE_COMPONENT_MESSAGE = "⚠️ هذا العنصر قديم أو لم يعد صالحاً. افتح المتصفح مرة أخرى من أمر المكتبة."

    def __init__(self):
        super().__init__(timeout=None)

    async def handle_component_interaction(self, interaction: discord.Interaction) -> bool:
        data = interaction.data or {}
        custom_id = data.get("custom_id")
        if not custom_id:
            return False

        # Route only world-browser IDs.
        if custom_id == "world_select_dropdown":
            values = data.get("values") or []
            if not values:
                await interaction.response.send_message(self.STALE_COMPONENT_MESSAGE, ephemeral=True)
                return True
            return await self._handle_world_select(interaction, values[0])

        if custom_id.startswith("cat_select:"):
            values = data.get("values") or []
            world_type = custom_id.split(":", 1)[1]
            if not values:
                await interaction.response.send_message(self.STALE_COMPONENT_MESSAGE, ephemeral=True)
                return True
            return await self._handle_category_select(interaction, world_type, values[0])

        if custom_id.startswith("story_select:"):
            values = data.get("values") or []
            world_type = custom_id.split(":", 1)[1]
            if not values:
                await interaction.response.send_message(self.STALE_COMPONENT_MESSAGE, ephemeral=True)
                return True
            return await self._handle_story_select(interaction, world_type, values[0])

        if custom_id == "back_to_worlds_btn":
            view = WorldSelectView()
            embed = EmbedBuilder.world_select_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            return True

        if custom_id.startswith("back_to_categories:"):
            world_type = custom_id.split(":", 1)[1]
            bot = interaction.client
            categories = bot.story_manager.get_world_categories(world_type)
            if world_type not in WORLD_CONFIG:
                await interaction.response.send_message(self.STALE_COMPONENT_MESSAGE, ephemeral=True)
                return True
            view = CategoryBrowserView(world_type, categories or {})
            world = WORLD_CONFIG[world_type]
            embed = EmbedBuilder.category_browser_embed(world_type, world["name"], world["desc"])
            await interaction.response.edit_message(embed=embed, view=view)
            return True

        if custom_id.startswith("start_story_btn:"):
            story_id = custom_id.split(":", 1)[1]
            from cogs.solo_cog import start_solo_interaction_with_perspective
            await start_solo_interaction_with_perspective(interaction, story_id)
            return True

        return False

    async def _handle_world_select(self, interaction: discord.Interaction, world_type: str) -> bool:
        bot = interaction.client
        if world_type not in WORLD_CONFIG:
            await interaction.response.send_message(self.STALE_COMPONENT_MESSAGE, ephemeral=True)
            return True

        categories = bot.story_manager.get_world_categories(world_type)
        if not categories:
            await interaction.response.send_message(
                "لا توجد قصص متاحة في هذا العالم حالياً. جرّب عالماً آخر من القائمة 🌍",
                ephemeral=True,
            )
            return True

        view = CategoryBrowserView(world_type, categories)
        embed = EmbedBuilder.category_browser_embed(world_type, WORLD_CONFIG[world_type]["name"], WORLD_CONFIG[world_type]["desc"])
        await interaction.response.edit_message(embed=embed, view=view)
        return True

    async def _handle_category_select(self, interaction: discord.Interaction, world_type: str, category: str) -> bool:
        bot = interaction.client
        if world_type not in WORLD_CONFIG:
            await interaction.response.send_message(self.STALE_COMPONENT_MESSAGE, ephemeral=True)
            return True

        stories = bot.story_manager.get_stories_by_world_and_category(world_type, category)
        if not stories:
            await interaction.response.send_message(
                "لا توجد قصص في هذا التصنيف حالياً. اختر تصنيفاً آخر.",
                ephemeral=True,
            )
            return True

        view = View(timeout=None)
        options = []
        for i, story in enumerate(stories):
            if i >= 25:
                break
            options.append(discord.SelectOption(
                label=story.title,
                description=story.description[:50] + "..." if story.description and len(story.description) > 50 else (story.description or "بدون وصف"),
                value=str(story.id)
            ))

        if options:
            view.add_item(StorySelect(world_type, options))

        view.add_item(BackToCategoriesButton(world_type))
        view.add_item(BackToWorldsButton())

        world = WORLD_CONFIG[world_type]
        preview = "\n".join(f"• {story.title}" for story in stories[:5])
        embed = discord.Embed(
            title=f"📚 {world['name']} • {category}",
            description=(
                "اختر القصة من القائمة المنسدلة بالأسفل، ثم اضغط زر البدء.\n\n"
                f"**معاينة سريعة:**\n{preview or 'لا توجد معاينة حالياً.'}"
            ),
            color=world["color"],
        )
        if len(stories) > 5:
            embed.add_field(name="معلومة", value=f"يوجد {len(stories)} قصة في هذا التصنيف.", inline=False)
        embed.set_footer(text="يمكنك العودة للتصنيفات أو العوالم في أي وقت.")

        await interaction.response.edit_message(embed=embed, view=view)
        return True

    async def _handle_story_select(self, interaction: discord.Interaction, world_type: str, story_id_value: str) -> bool:
        bot = interaction.client
        if world_type not in WORLD_CONFIG:
            await interaction.response.send_message(self.STALE_COMPONENT_MESSAGE, ephemeral=True)
            return True

        try:
            story_id = int(story_id_value)
        except (TypeError, ValueError):
            await interaction.response.send_message(self.STALE_COMPONENT_MESSAGE, ephemeral=True)
            return True

        story = bot.story_manager.get_story(story_id)
        if not story:
            await interaction.response.send_message("❌ لم يتم العثور على القصة.", ephemeral=True)
            return True

        embed = EmbedBuilder.story_preview_embed(story)
        view = View(timeout=None)
        view.add_item(StartStoryButton(story.id))
        view.add_item(BackToCategoriesButton(world_type))
        view.add_item(BackToWorldsButton())
        await interaction.response.edit_message(embed=embed, view=view)
        return True


class WorldSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)

        options = [
            discord.SelectOption(
                label=w_info["name"],
                description=w_info["desc"],
                emoji=w_info["emoji"],
                value=w_type,
            )
            for w_type, w_info in WORLD_CONFIG.items()
        ]

        select = Select(
            custom_id="world_select_dropdown",
            placeholder="اختر العالم الذي تريد استكشافه...",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.add_item(select)


class CategoryBrowserView(View):
    def __init__(self, world_type: str, categories: dict, timeout=None):
        super().__init__(timeout=timeout)
        options = []
        for i, category in enumerate(categories.keys()):
            if i >= 25:
                break
            options.append(discord.SelectOption(label=category, value=category))

        if options:
            self.add_item(CategorySelect(world_type, options))

        self.add_item(BackToWorldsButton())


class CategorySelect(Select):
    def __init__(self, world_type: str, options: list):
        super().__init__(
            custom_id=f"cat_select:{world_type}",
            placeholder="اختر التصنيف...",
            options=options,
            min_values=1,
            max_values=1,
        )


class StorySelect(Select):
    def __init__(self, world_type: str, options: list):
        super().__init__(
            custom_id=f"story_select:{world_type}",
            placeholder="اختر القصة...",
            options=options,
            min_values=1,
            max_values=1,
        )


class StartStoryButton(Button):
    def __init__(self, story_id: int | str):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="ابدأ القصة الآن",
            custom_id=f"start_story_btn:{story_id}",
        )


class BackToWorldsButton(Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="العودة للعوالم",
            custom_id="back_to_worlds_btn",
        )


class BackToCategoriesButton(Button):
    def __init__(self, world_type: str):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="العودة للتصنيفات",
            custom_id=f"back_to_categories:{world_type}",
        )
