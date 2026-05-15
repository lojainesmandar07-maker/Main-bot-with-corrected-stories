import discord
from discord import app_commands
from discord.ext import commands
from core.bot import StoryBot
from core.config import load_config, save_config
import aiosqlite
import traceback

DB_PATH = "data/nexus.db"

async def init_nexus_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_pulse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_str TEXT UNIQUE,
                question TEXT,
                options_json TEXT,
                message_id INTEGER,
                channel_id INTEGER,
                is_closed BOOLEAN DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_pulse_votes (
                pulse_id INTEGER,
                user_id INTEGER,
                option_index INTEGER,
                PRIMARY KEY (pulse_id, user_id),
                FOREIGN KEY (pulse_id) REFERENCES daily_pulse(id)
            )
        """)
        await db.commit()

class SetupCog(commands.Cog):
    def __init__(self, bot: StoryBot):
        self.bot = bot
        # init_nexus_db is now awaited in setup_hook in bot.py

    @app_commands.command(name="إعداد_النيكسوس", description="لوحة تحكم الإدارة لتهيئة النظام (للمشرفين فقط)")
    @app_commands.default_permissions(manage_guild=True)
    async def setup_nexus(self, interaction: discord.Interaction):
        try:
            if not interaction.user.guild_permissions.manage_guild:
                await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط.", ephemeral=True)
                return

            view = NexusSetupView()
            embed = discord.Embed(
                title="⚙️ لوحة تحكم النيكسوس",
                description="اختر الإعداد الذي تود تعديله من القائمة أدناه:",
                color=discord.Color.dark_theme()
            )

            config = load_config()
            channel_id = config.get("pulse_channel_id")
            time_str = config.get("pulse_time") or "غير محدد (بتوقيت UTC)"
            is_enabled = "مفعل ✅" if str(config.get("pulse_enabled", "0")) == "1" else "معطل ❌"

            channel_mention = f"<#{channel_id}>" if channel_id else "غير محدد"

            embed.add_field(name="القناة", value=channel_mention, inline=False)
            embed.add_field(name="وقت النبضة", value=time_str, inline=False)
            embed.add_field(name="حالة النظام", value=is_enabled, inline=False)

            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            print(f"Error in setup_nexus: {e}")
            await interaction.response.send_message("⚠️ حدث خطأ أثناء تنفيذ الأمر.", ephemeral=True)

async def set_config(key: str, value: str):
    config = load_config()
    config[key] = value
    save_config(config)

async def get_db_config(key: str) -> str:
    return load_config().get(key)

class NexusSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="اختر إعداداً للتعديل...",
        options=[
            discord.SelectOption(label="قناة النبضة اليومية", value="channel", emoji="📢"),
            discord.SelectOption(label="وقت النبضة اليومية", value="time", emoji="⏰"),
            discord.SelectOption(label="تفعيل/تعطيل النظام", value="toggle", emoji="🔄")
        ],
        custom_id="nexus_setup_select"
    )
    async def setup_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط.", ephemeral=True)
            return

        value = select.values[0]

        if value == "channel":
            view = ChannelSetupView()
            await interaction.response.send_message("اختر القناة من القائمة:", view=view, ephemeral=True)
        elif value == "time":
            modal = TimeSetupModal()
            await interaction.response.send_modal(modal)
        elif value == "toggle":
            current_val = await get_db_config("pulse_enabled")
            new_val = "0" if current_val == "1" else "1"
            await set_config("pulse_enabled", new_val)
            status = "مفعل ✅" if new_val == "1" else "معطل ❌"
            await interaction.response.send_message(f"تم تغيير حالة نظام النبضة اليومية إلى: {status}", ephemeral=True)

class ChannelSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="اختر قناة للنبضة اليومية...",
        custom_id="nexus_channel_select"
    )
    async def channel_select(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ هذا الأمر مخصص للمشرفين فقط.", ephemeral=True)
            return

        channel = select.values[0]
        await set_config("pulse_channel_id", str(channel.id))
        await interaction.response.send_message(f"✅ تم تعيين القناة <#{channel.id}> للنبضة اليومية.", ephemeral=True)

class TimeSetupModal(discord.ui.Modal, title="تكوين وقت النبضة اليومية"):
    time_input = discord.ui.TextInput(
        label="الوقت (بتوقيت UTC, مثلاً 14:30)",
        placeholder="HH:MM",
        max_length=5,
        min_length=5,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        time_str = self.time_input.value
        # Basic validation
        try:
            h, m = map(int, time_str.split(':'))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except:
            await interaction.response.send_message("❌ صيغة الوقت غير صحيحة. استخدم HH:MM (مثال 14:30)", ephemeral=True)
            return

        await set_config("pulse_time", time_str)
        await interaction.response.send_message(f"✅ تم تعيين وقت النبضة اليومية إلى {time_str} UTC.", ephemeral=True)

async def setup(bot: StoryBot):
    await bot.add_cog(SetupCog(bot))
