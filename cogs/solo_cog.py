import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio

from core.bot import StoryBot
from engine.solo_manager import SoloGameManager
from ui.embeds import EmbedBuilder
from ui.listing_view import SoloLibraryView
from ui.solo_view import SoloView, ShareEndingView
from ui.world_browser import WorldSelectView

DB_PATH = "data/nexus.db"


async def init_solo_db() -> None:
    """Create only the tables required for safe solo runtime wiring."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS story_plays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                story_id INTEGER,
                ending_id TEXT,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS shared_endings (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                story_id INTEGER,
                ending_id TEXT,
                ending_text TEXT,
                shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def start_solo_interaction(
    interaction: discord.Interaction,
    story_ref: int | str,
    perspective_id: str | None = None,
) -> None:
    await start_solo_interaction_with_perspective(interaction, story_ref, perspective_id=perspective_id)


async def _check_story_lock(interaction: discord.Interaction, story_id: int) -> str | None:
    """Return an Arabic error message if story is currently locked; otherwise None."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT winner_id FROM mystery_rooms WHERE is_active = 1 AND exclusive_story_id = ?",
                (story_id,),
            )
            lock = await cursor.fetchone()
            if not lock:
                return None
            winner_id = lock[0]
            if winner_id and winner_id != interaction.user.id:
                return "❌ هذه القصة مقفلة حالياً خلف لغز غرفة الغموض! كن أول من يحل اللغز أو انتظر حتى تتاح للجميع."
    except Exception as e:
        print(f"[SoloCog] lock check failed: {e}")
    return None


class PerspectiveSelect(discord.ui.Select):
    def __init__(self, story_id: int, user_id: int, perspectives):
        self.story_id = story_id
        self.user_id = user_id
        options = [
            discord.SelectOption(
                label=(p.label or p.id)[:100],
                value=p.id,
                description=(p.description or "بدون وصف")[:100],
                emoji=(p.emoji or "🎭"),
            )
            for p in perspectives[:25]
        ]
        super().__init__(
            placeholder="اختر منظور البداية...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"perspective_select_{story_id}_{user_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الاختيار ليس لك.", ephemeral=True)
            return
        perspective_id = self.values[0]
        from cogs.solo_cog import start_solo_interaction_with_perspective
        await start_solo_interaction_with_perspective(
            interaction,
            self.story_id,
            perspective_id=perspective_id,
            force_new_response=False,
        )


class PerspectiveSelectView(discord.ui.View):
    def __init__(self, story_id: int, user_id: int, perspectives):
        super().__init__(timeout=180)
        self.add_item(PerspectiveSelect(story_id, user_id, perspectives))


async def start_solo_interaction_with_perspective(
    interaction: discord.Interaction,
    story_ref: int | str,
    perspective_id: str | None = None,
    force_new_response: bool = True,
) -> None:
    """Shared helper used by commands and UI views to start a real solo session."""
    cog = interaction.client.get_cog("SoloCog")
    if not cog:
        sender = interaction.response.send_message if force_new_response else interaction.followup.send
        await sender("❌ نظام اللعب الفردي غير متاح حالياً. حاول لاحقاً.", ephemeral=True)
        return

    story = cog.bot.story_manager.resolve_story(story_ref, game_mode="single")
    if not story:
        sender = interaction.response.send_message if force_new_response else interaction.followup.send
        await sender(embed=EmbedBuilder.error_embed("القصة غير موجودة."), ephemeral=True)
        return

    if not isinstance(story.id, int):
        sender = interaction.response.send_message if force_new_response else interaction.followup.send
        await sender(embed=EmbedBuilder.error_embed("هذه القصة لا تدعم نمط اللعب الفردي المباشر حالياً."), ephemeral=True)
        return

    lock_error = await _check_story_lock(interaction, story.id)
    if lock_error:
        sender = interaction.response.send_message if force_new_response else interaction.followup.send
        await sender(lock_error, ephemeral=True)
        return
    if story.game_mode != "single":
        sender = interaction.response.send_message if force_new_response else interaction.followup.send
        await sender(embed=EmbedBuilder.error_embed("هذه القصة غير مخصصة للعب الفردي."), ephemeral=True)
        return

    if story.perspectives and not perspective_id:
        view = PerspectiveSelectView(story_id=story.id, user_id=interaction.user.id, perspectives=story.perspectives)
        embed = discord.Embed(
            title=f"🎭 اختر منظورك — {story.title}",
            description="هذه القصة تدعم أكثر من منظور. اختر منظور البداية لتحديد زاوية السرد.",
            color=EmbedBuilder.world_color("solo", discord.Color.blurple()),
        )
        for p in story.perspectives[:5]:
            embed.add_field(
                name=f"{p.emoji or '🎭'} {p.label or p.id}",
                value=(p.description or "بدون وصف")[:200],
                inline=False,
            )
        sender = interaction.response.send_message if force_new_response else interaction.followup.send
        await sender(embed=embed, view=view, ephemeral=True)
        return

    session, error = cog.solo_manager.start_solo_game(interaction.user.id, story.id)
    if error:
        sender = interaction.response.send_message if force_new_response else interaction.followup.send
        await sender(embed=EmbedBuilder.error_embed(error), ephemeral=True)
        return

    if perspective_id:
        perspective = next((p for p in story.perspectives if p.id == perspective_id), None)
        if not perspective:
            sender = interaction.response.send_message if force_new_response else interaction.followup.send
            await sender(embed=EmbedBuilder.error_embed("المنظور المختار غير موجود."), ephemeral=True)
            return
        start_scene = story.get_scene(perspective.start_node)
        if not start_scene:
            sender = interaction.response.send_message if force_new_response else interaction.followup.send
            await sender(embed=EmbedBuilder.error_embed("تعذر بدء هذا المنظور بسبب مشهد بداية مفقود."), ephemeral=True)
            return
        session["scene"] = start_scene
        session["round"] = 1

    story = session["story"]
    scene = session["scene"]
    points = session["points"]
    round_number = session["round"]

    embed = EmbedBuilder.solo_scene_embed(scene, round_number, story.title, points)
    view = None
    if not scene.is_ending and scene.choices:
        view = SoloView(cog.solo_manager, interaction.user.id, scene.choices)
    elif scene.is_ending:
        cog.solo_manager.end_solo_game(interaction.user.id)

    if force_new_response:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        if view is not None:
            try:
                view.message = await interaction.original_response()
            except Exception:
                pass
    else:
        await interaction.response.edit_message(embed=embed, view=view)
        if view is not None and interaction.message:
            view.message = interaction.message
        if scene.is_ending:
            await handle_story_end(interaction, interaction.user.id, story, scene)


async def handle_story_end(
    interaction: discord.Interaction,
    user_id: int,
    story,
    scene,
) -> None:
    """Shared helper called by ui.solo_view when user reaches an ending."""
    # Ensure session is closed no matter who called this handler.
    try:
        cog = interaction.client.get_cog("SoloCog")
        if cog:
            cog.solo_manager.end_solo_game(user_id)
    except Exception:
        pass

    channel_for_notifications = None
    if interaction.guild and interaction.channel and hasattr(interaction.channel, "send"):
        channel_for_notifications = interaction.channel

    # 1) Record completion in story_plays
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO story_plays (user_id, story_id, ending_id)
                VALUES (?, ?, ?)
                """,
                (user_id, story.id, scene.id),
            )
            await db.commit()
    except Exception as e:
        print(f"[SoloCog] Failed to record story play: {e}")

    # 2) Notify profile/title system
    try:
        from cogs.profile_cog import on_story_complete
        if channel_for_notifications:
            await on_story_complete(user_id, channel_for_notifications)
    except Exception as e:
        print(f"[SoloCog] Failed to notify profile completion: {e}")

    # 3) Check weekly challenge completion
    challenge_notice = None
    try:
        from cogs.challenge_cog import check_weekly_challenge_completion
        challenge_notice = await check_weekly_challenge_completion(
            bot=interaction.client,
            user_id=user_id,
            story_id=story.id,
            ending_id=scene.id,
            guild=interaction.guild,
            notify_channel=channel_for_notifications,
        )
    except Exception as e:
        print(f"[SoloCog] Failed to check weekly challenge completion: {e}")

    # 4) Share-ending prompt (only if endings channel is configured)
    try:
        from core.config import get_config
        world_channels = get_config("world_channels", {})
        endings_ch_id = world_channels.get("endings_channel") or get_config("test_channel")

        if challenge_notice:
            await interaction.followup.send(challenge_notice, ephemeral=True)

        if not endings_ch_id:
            await interaction.followup.send("🎉 وصلت إلى نهاية القصة بنجاح! يمكنك بدء قصة جديدة من `/قصص_فردية`.", ephemeral=True)
            return

        prompt = "🎉 نهاية رائعة! هل ترغب بمشاركة نهايتك في قناة النهايات؟"
        view = ShareEndingView(
            user_id=user_id,
            story_id=story.id,
            scene_id=scene.id,
            ending_text=scene.text or "",
            story_title=story.title,
        )
        await interaction.followup.send(prompt, view=view, ephemeral=True)
    except Exception as e:
        print(f"[SoloCog] Failed to send ending share prompt: {e}")


class SoloCog(commands.Cog):
    def __init__(self, bot: StoryBot):
        self.bot = bot
        self.solo_manager = SoloGameManager(bot, bot.story_manager)
        asyncio.create_task(init_solo_db())

    @app_commands.command(name="ابدأ", description="ابدأ رحلتك عبر مستكشف العوالم")
    async def start_world_browser(self, interaction: discord.Interaction):
        embed = EmbedBuilder.world_select_embed()
        await interaction.response.send_message(embed=embed, view=WorldSelectView())

    @app_commands.command(name="مساعدة", description="دليل سريع لأوامر وخطوات The Nexus")
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=EmbedBuilder.help_embed())

    async def story_ref_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        stories = self.bot.story_manager.get_stories_by_mode("single").values()
        needle = (current or "").strip().casefold()
        choices: list[app_commands.Choice[str]] = []
        for story in stories:
            sid = str(story.id)
            label = f"{story.title} ({sid})"
            if needle and needle not in label.casefold():
                continue
            choices.append(app_commands.Choice(name=label[:100], value=sid))
            if len(choices) >= 25:
                break
        return choices

    @app_commands.command(name="لعب_فردي", description="ابدأ قصة فردية مباشرة بالاسم أو المعرّف")
    @app_commands.describe(story_ref="اسم القصة أو رقمها")
    @app_commands.autocomplete(story_ref=story_ref_autocomplete)
    async def play_solo(self, interaction: discord.Interaction, story_ref: str):
        await start_solo_interaction_with_perspective(interaction, story_ref)


async def setup(bot: StoryBot):
    await bot.add_cog(SoloCog(bot))
