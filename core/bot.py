import discord
from discord.ext import commands
from engine.story_manager import StoryManager
from engine.event_manager import EventManager


class StoryBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        # This bot currently uses slash/app commands only.
        # Using mention-only prefix avoids requiring privileged message content intent.
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

        self.story_manager = StoryManager()
        self.event_manager = EventManager(self, self.story_manager)

    async def setup_hook(self):
        # Ensure daily pulse db is initialized before trying to read from it
        from cogs.setup_cog import init_nexus_db
        await init_nexus_db()

        # Re-register persistent views BEFORE loading cogs
        from ui.listing_view import SoloLibraryView, MultiLibraryView
        from ui.world_browser import (
            WorldBrowserPersistentRouter,
            WorldSelectView,
        )

        self.add_view(SoloLibraryView({}, timeout=None))
        self.add_view(MultiLibraryView({}, timeout=None))

        from cogs.setup_cog import NexusSetupView, ChannelSetupView
        self.add_view(NexusSetupView())
        self.add_view(ChannelSetupView())

        # Register world-browser persistent handlers once.
        self._world_browser_router = WorldBrowserPersistentRouter()
        self.add_view(WorldSelectView())

        # Load daily pulse views and decision views
        import aiosqlite
        import json
        import os

        async def table_exists(db, table_name: str) -> bool:
            cursor = await db.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table_name,),
            )
            return (await cursor.fetchone()) is not None

        if os.path.exists("data/nexus.db"):
            try:
                async with aiosqlite.connect("data/nexus.db") as db:
                    if await table_exists(db, "daily_pulse"):
                        cursor = await db.execute("SELECT id, options_json FROM daily_pulse WHERE is_closed = 0")
                        rows = await cursor.fetchall()
                        from cogs.daily_cog import DailyPulseView
                        for pulse_id, options_json in rows:
                            try:
                                options = json.loads(options_json)
                            except Exception:
                                options = []
                            self.add_view(DailyPulseView(pulse_id, options))

                    if await table_exists(db, "collective_decisions"):
                        d_cursor = await db.execute("SELECT id, options_json FROM collective_decisions WHERE is_active = 1")
                        d_rows = await d_cursor.fetchall()
                        from cogs.social_cog import DecisionVoteView
                        for decision_id, options_json in d_rows:
                            try:
                                options = json.loads(options_json)
                            except Exception:
                                options = []
                            if isinstance(options, list) and options:
                                self.add_view(DecisionVoteView(decision_id, options))
            except Exception as e:
                print(f"Error loading persistent views: {e}")

        # Load cogs here. Keep startup resilient: one broken extension should not crash the bot.
        extensions = [
            "cogs.event_cog",
            "cogs.solo_cog",
            "cogs.profile_cog",
            "cogs.admin_cog",
            "cogs.personality_cog",
            "cogs.npc_cog",
            "cogs.setup_cog",
            "cogs.daily_cog",
            "cogs.challenge_cog",
            "cogs.social_cog",
            "cogs.stats_cog",
            "cogs.mystery_cog",
        ]
        loaded_extensions = []
        failed_extensions = []

        for extension in extensions:
            try:
                await self.load_extension(extension)
                loaded_extensions.append(extension)
            except Exception as e:
                failed_extensions.append((extension, str(e)))
                print(f"Failed to load extension {extension}: {e}")

        # Sync commands (environment-driven policy with backoff/cadence guards)
        from core.config import GUILD_ID
        import time

        sync_mode = os.getenv("COMMAND_SYNC_MODE", "dev" if GUILD_ID else "prod").strip().lower()
        global_sync_enabled = os.getenv("ENABLE_GLOBAL_COMMAND_SYNC", "false").strip().lower() in {"1", "true", "yes", "on"}
        global_sync_interval_seconds = int(os.getenv("GLOBAL_COMMAND_SYNC_INTERVAL_SECONDS", "21600"))
        sync_state_path = "data/command_sync_state.json"

        def load_sync_state() -> dict:
            try:
                if os.path.exists(sync_state_path):
                    with open(sync_state_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                print(f"[Sync] Failed reading sync state, using defaults: {e}")
            return {}

        def save_sync_state(state: dict) -> None:
            try:
                os.makedirs(os.path.dirname(sync_state_path), exist_ok=True)
                with open(sync_state_path, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[Sync] Failed writing sync state: {e}")

        async def guarded_sync(sync_scope: str, sync_call):
            try:
                synced = await sync_call()
                print(f"[Sync] Synced {sync_scope} commands ({len(synced)} commands).")
                state = load_sync_state()
                state["last_successful_sync_at"] = int(time.time())
                state["last_successful_sync_scope"] = sync_scope
                save_sync_state(state)
            except discord.HTTPException as e:
                retry_after = getattr(e, "retry_after", None)
                if retry_after is not None:
                    print(f"[Sync] Sync rate-limited for {sync_scope}; retry_after={retry_after}s. Startup continues.")
                else:
                    print(f"[Sync] HTTP sync failure for {sync_scope}: {e}. Startup continues.")
            except Exception as e:
                print(f"[Sync] Unexpected sync failure for {sync_scope}: {e}. Startup continues.")

        if sync_mode == "dev":
            if GUILD_ID:
                guild = discord.Object(id=int(GUILD_ID))
                self.tree.copy_global_to(guild=guild)
                await guarded_sync(f"guild {GUILD_ID}", lambda: self.tree.sync(guild=guild))
            else:
                print("[Sync] Skipped sync: COMMAND_SYNC_MODE=dev but GUILD_ID is not set.")
        else:
            if global_sync_enabled:
                state = load_sync_state()
                now = int(time.time())
                last_sync = int(state.get("last_successful_sync_at", 0) or 0)
                elapsed = now - last_sync
                if elapsed >= global_sync_interval_seconds:
                    await guarded_sync("global", self.tree.sync)
                else:
                    remaining = global_sync_interval_seconds - elapsed
                    print(
                        f"[Sync] Skipped global sync: next allowed in {remaining}s "
                        f"(interval={global_sync_interval_seconds}s)."
                    )
            else:
                print("[Sync] Skipped global sync: ENABLE_GLOBAL_COMMAND_SYNC is false.")

        print(f"Bot setup complete. Loaded {len(loaded_extensions)}/{len(extensions)} extensions.")
        if failed_extensions:
            print("Failed extensions:")
            for extension, error in failed_extensions:
                print(f"- {extension}: {error}")


    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            router = getattr(self, "_world_browser_router", None)
            if router and await router.handle_component_interaction(interaction):
                return
        await super().on_interaction(interaction)

    async def on_application_command_error(self, interaction: discord.Interaction, error):
        msg = "⚠️ حدث خطأ غير متوقع، يرجى المحاولة لاحقاً."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass
        import traceback
        print(f"[ERROR] {traceback.format_exc()}")

    async def on_member_join(self, member: discord.Member):
        import asyncio
        from core.config import get_config

        # Wait 30 seconds
        await asyncio.sleep(30)

        # Send DM
        try:
            embed = discord.Embed(
                title="🌌 مرحباً بك في The Nexus",
                description="عالم من القصص التفاعلية ينتظرك. كل قرار تتخذه يُشكّل مصيرك.\n\nاستخدم الأمر `/اختبار_الشخصية` في السيرفر لتبدأ رحلتك وتكتشف نمطك الحقيقي!",
                color=discord.Color.from_rgb(88, 101, 242)
            )
            await member.send(embed=embed)
        except discord.Forbidden:
            pass  # DMs closed

        # Post in configured channel
        world_channels = get_config("world_channels", {})
        welcome_ch_id = world_channels.get("general_channel") or get_config("test_channel")

        if welcome_ch_id:
            try:
                channel = self.get_channel(int(welcome_ch_id))
                if channel:
                    await channel.send(f"👋 انضم <@{member.id}> — اكتب `/اختبار_الشخصية` لتبدأ!")
            except Exception as e:
                print(f"Error sending welcome message: {e}")

    async def on_ready(self):
        print(f"Logged in as {self.user.name} (ID: {self.user.id})")
        print("Ready to run interactive stories!")
