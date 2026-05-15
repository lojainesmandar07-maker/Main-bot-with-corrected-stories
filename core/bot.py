import discord
from discord.ext import commands
from engine.story_manager import StoryManager
from engine.event_manager import EventManager


class StoryBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = True

        # This bot currently uses slash/app commands only.
        # Using mention-only prefix avoids requiring privileged message content intent.
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

        self.story_manager = StoryManager()
        self.event_manager = EventManager(self, self.story_manager)

    async def _get_intent_diagnostics(self) -> tuple[list[str], list[str]]:
        required_privileged = {
            "members": "on_member_join, role-based logic in profile/personality/NPC flows",
        }
        optional_privileged = {
            "presences": "not required",
            "message_content": "not required (slash commands + components only)",
        }

        missing_required: list[str] = []
        notes: list[str] = []

        try:
            app_info = await self.application_info()
            flags = app_info.flags
        except Exception as e:
            notes.append(f"Could not fetch application flags for intent diagnostics: {e}")
            return missing_required, notes

        flag_values = {
            "members": bool(getattr(flags, "gateway_guild_members", False) or getattr(flags, "gateway_guild_members_limited", False)),
            "presences": bool(getattr(flags, "gateway_presence", False) or getattr(flags, "gateway_presence_limited", False)),
            "message_content": bool(getattr(flags, "gateway_message_content", False) or getattr(flags, "gateway_message_content_limited", False)),
        }

        for intent_name, reason in required_privileged.items():
            if getattr(self.intents, intent_name, False) and not flag_values[intent_name]:
                missing_required.append(
                    f"- {intent_name}: enabled in code but disabled in Discord Developer Portal ({reason})"
                )

        for intent_name, reason in optional_privileged.items():
            if getattr(self.intents, intent_name, False) and not flag_values[intent_name]:
                notes.append(f"- {intent_name}: enabled in code but disabled in portal ({reason})")

        return missing_required, notes

    async def setup_hook(self):
        missing_required_intents, _ = await self._get_intent_diagnostics()
        if missing_required_intents:
            joined = "\n".join(missing_required_intents)
            raise RuntimeError(
                "Startup aborted: privileged gateway intent mismatch detected.\n"
                f"{joined}\n"
                "Enable the required intent(s) in Discord Developer Portal -> Bot -> Privileged Gateway Intents."
            )

        # Ensure daily pulse db is initialized before trying to read from it
        from cogs.setup_cog import init_nexus_db
        await init_nexus_db()

        # Re-register persistent views BEFORE loading cogs
        from ui.listing_view import SoloLibraryView, MultiLibraryView
        from ui.world_browser import (
            WORLD_CONFIG,
            BackToCategoriesButton,
            BackToWorldsButton,
            CategoryBrowserView,
            StartStoryButton,
            StorySelect,
            WorldSelectView,
        )

        class _PersistentItemView(discord.ui.View):
            """Wrap a single persistent UI item so discord.py can rebind callbacks on restart."""

            def __init__(self, item: discord.ui.Item):
                super().__init__(timeout=None)
                self.add_item(item)

        self.add_view(SoloLibraryView({}, timeout=None))
        self.add_view(MultiLibraryView({}, timeout=None))
        self.add_view(WorldSelectView())
        self.add_view(_PersistentItemView(BackToWorldsButton()))

        from cogs.setup_cog import NexusSetupView, ChannelSetupView
        self.add_view(NexusSetupView())
        self.add_view(ChannelSetupView())

        # Register persistent world-browser components that use dynamic custom_ids.
        # We bind one lightweight view/item per known world/category/story so callbacks
        # remain alive after bot restarts.
        for world_type in WORLD_CONFIG.keys():
            self.add_view(CategoryBrowserView(world_type, {}, timeout=None))
            self.add_view(_PersistentItemView(BackToCategoriesButton(world_type)))

            categories = self.story_manager.get_world_categories(world_type)
            for category in categories.keys():
                self.add_view(
                    _PersistentItemView(
                        StorySelect(
                            world_type=world_type,
                            category=category,
                            options=[discord.SelectOption(label="stub", value="0")],
                        )
                    )
                )

            stories = self.story_manager.get_stories_by_world(world_type)
            for story in stories.values():
                self.add_view(_PersistentItemView(StartStoryButton(story.id)))

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

        # Sync commands
        from core.config import GUILD_ID
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            # await self.tree.sync(guild=guild)  # Disabled to prevent Cloudflare 1015 ban
            print(f"Synced commands to guild {GUILD_ID}")
        else:
            # await self.tree.sync()  # Disabled to prevent Cloudflare 1015 ban
            print("Synced global commands")

        print(f"Bot setup complete. Loaded {len(loaded_extensions)}/{len(extensions)} extensions.")
        if failed_extensions:
            print("Failed extensions:")
            for extension, error in failed_extensions:
                print(f"- {extension}: {error}")

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
        print(f"Gateway intents: guilds={self.intents.guilds}, members={self.intents.members}, message_content={self.intents.message_content}, presences={self.intents.presences}")
        missing_required, notes = await self._get_intent_diagnostics()
        if missing_required:
            print("⚠️ Missing required privileged intent grants:")
            for issue in missing_required:
                print(issue)
            print("⚠️ Fix in Developer Portal: Applications -> [Your App] -> Bot -> Privileged Gateway Intents.")
        elif notes:
            print("Intent diagnostics:")
            for note in notes:
                print(note)
        print("Ready to run interactive stories!")
