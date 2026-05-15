import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio
from core.config import get_config

DB_PATH = "data/nexus.db"

# --- Title milestones ---
TITLE_MILESTONES = {
    1:  "الراوي المبتدئ",
    3:  "صاحب الحكايا",
    5:  "المحارب الناشئ",
    10: "حارس القصص",
    15: "صانع الأساطير",
    20: "سيد الروايات",
    30: "أسطورة الأبد",
}

# --- Archetype Arabic names ---
ARCHETYPE_NAMES = {
    "warrior":    "المحارب",
    "guardian":   "الحارس",
    "strategist": "المخطط",
    "shadow":     "الظل",
    "rebel":      "المتمرد",
    "seeker":     "الباحث",
    "oracle":     "العرّاف",
    "wanderer":   "التائه",
}


async def init_db():
    """Create profile and optional-social tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id           INTEGER PRIMARY KEY,
                title             TEXT    DEFAULT 'الراوي المبتدئ',
                stories_completed INTEGER DEFAULT 0,
                joined_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Optional systems: keep /بروفايل safe on fresh databases.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS friend_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER,
                target_user_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS decision_votes (
                decision_id INTEGER,
                user_id INTEGER,
                option_index INTEGER,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (decision_id, user_id)
            )
        """)
        await db.commit()


async def on_story_complete(user_id: int, channel: discord.TextChannel):
    """
    Call this function every time ANY story (solo or event) is completed.
    It increments the counter, checks for a new title milestone, and
    announces the new title in the channel if one was earned.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Upsert: create player row if first time, else increment
        await db.execute("""
            INSERT INTO players (user_id, stories_completed)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE
            SET stories_completed = stories_completed + 1
        """, (user_id,))

        row = await db.execute(
            "SELECT stories_completed, title FROM players WHERE user_id = ?",
            (user_id,)
        )
        player = await row.fetchone()
        count, current_title = player

        # Find the correct title for this milestone
        new_title = current_title
        for threshold in sorted(TITLE_MILESTONES.keys(), reverse=True):
            if count >= threshold:
                new_title = TITLE_MILESTONES[threshold]
                break

        # If title changed, update DB and announce
        if new_title != current_title:
            await db.execute(
                "UPDATE players SET title = ? WHERE user_id = ?",
                (new_title, user_id)
            )
            embed = discord.Embed(
                title="🏅 لقب جديد!",
                description=f"<@{user_id}> حصل على لقب جديد: **{new_title}**",
                color=0xFFD700
            )
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

        await db.commit()


class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize DB on cog load
        asyncio.create_task(init_db())

    @app_commands.command(name="بروفايل", description="اعرض ملفك الشخصي في The Nexus")
    async def profile(self, interaction: discord.Interaction):
        try:
            # --- Step 1: Read archetype LIVE from Discord roles ---
            # Never stored in DB — always read from the member's current roles
            archetype_roles = get_config("archetype_roles", {})
            # Config stores role IDs as integers or strings — normalize to int
            role_to_archetype = {int(v): k for k, v in archetype_roles.items() if v}
            member_role_ids = [r.id for r in interaction.user.roles]
            archetype_key = next(
                (role_to_archetype[rid] for rid in member_role_ids if rid in role_to_archetype),
                None
            )
            archetype_display = ARCHETYPE_NAMES.get(archetype_key, "غير محدد بعد")

            # --- Step 2: Read player data from DB ---
            async with aiosqlite.connect(DB_PATH) as db:
                row = await db.execute(
                    "SELECT title, stories_completed, joined_at FROM players WHERE user_id = ?",
                    (interaction.user.id,)
                )
                player = await row.fetchone()

            title = player[0] if player else "الراوي المبتدئ"
            count = player[1] if player else 0
            joined = player[2][:10] if player and player[2] else "غير معروف"

            # Fetch optional social stats safely
            challenge_count = 0
            votes_count = 0
            async with aiosqlite.connect(DB_PATH) as db:
                try:
                    row = await db.execute(
                        "SELECT COUNT(*) FROM friend_challenges WHERE challenger_id = ? OR target_user_id = ?",
                        (interaction.user.id, interaction.user.id),
                    )
                    challenge_count = (await row.fetchone())[0]
                except Exception:
                    challenge_count = 0

                try:
                    row = await db.execute(
                        "SELECT COUNT(*) FROM decision_votes WHERE user_id = ?",
                        (interaction.user.id,),
                    )
                    votes_count = (await row.fetchone())[0]
                except Exception:
                    votes_count = 0

            # --- Step 3: Build embed ---
            embed = discord.Embed(
                title=f"🪪 ملف {interaction.user.display_name}",
                description="ملخص تقدمك الحالي داخل The Nexus.",
                color=0x2E4057
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(
                name="🧬 الهوية",
                value=f"**الشخصية:** {archetype_display}\n**اللقب:** {title}",
                inline=False,
            )
            embed.add_field(
                name="📚 التقدم القصصي",
                value=f"القصص المكتملة: **{count}**\nتاريخ الانضمام: **{joined}**",
                inline=True,
            )
            embed.add_field(
                name="🤝 النشاط الاجتماعي",
                value=f"التحديات: **{challenge_count}**\nالتصويتات: **{votes_count}**",
                inline=True,
            )

            if not archetype_key:
                embed.set_footer(text="💡 استخدم /اختبار_الشخصية لتحديد شخصيتك وفتح محتوى إضافي")
            else:
                embed.set_footer(text="لتحسين ملفك: أكمل قصصاً أكثر وشارك في القرارات الاجتماعية.")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            import traceback
            print(f"[ProfileCog] Error: {traceback.format_exc()}")
            await interaction.response.send_message(
                "⚠️ حدث خطأ أثناء تحميل ملفك الشخصي."
            )


async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
