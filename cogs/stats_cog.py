import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite

from core.bot import StoryBot

DB_PATH = "data/nexus.db"


async def _ensure_players_table() -> None:
    """Ensure leaderboard base table exists without touching optional systems."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                title TEXT DEFAULT 'الراوي المبتدئ',
                stories_completed INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def _table_exists(db: aiosqlite.Connection, table_name: str) -> bool:
    cursor = await db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return (await cursor.fetchone()) is not None


class StatsCog(commands.Cog):
    def __init__(self, bot: StoryBot):
        self.bot = bot

    async def cog_load(self) -> None:
        try:
            await _ensure_players_table()
        except Exception as e:
            print(f"[StatsCog] DB init error: {e}")

    @app_commands.command(name="إحصائيات", description="نظرة عامة على نشاط السيرفر")
    async def server_stats(self, interaction: discord.Interaction):
        """Show safe, real server-level statistics based on currently available tables."""
        try:
            metrics: list[tuple[str, str]] = []

            async with aiosqlite.connect(DB_PATH) as db:
                if await _table_exists(db, "players"):
                    cursor = await db.execute(
                        "SELECT COUNT(*), COALESCE(SUM(stories_completed), 0), COUNT(CASE WHEN stories_completed > 0 THEN 1 END) FROM players"
                    )
                    total_players, total_completed, active_players = await cursor.fetchone()
                    metrics.append(("👥 عدد اللاعبين المسجلين", f"{total_players}"))
                    metrics.append(("📚 إجمالي القصص المكتملة", f"{total_completed}"))
                    metrics.append(("✨ لاعبين أتمّوا قصة واحدة على الأقل", f"{active_players}"))

                if await _table_exists(db, "story_plays"):
                    cursor = await db.execute(
                        "SELECT COUNT(*), COUNT(DISTINCT user_id) FROM story_plays"
                    )
                    total_plays, unique_story_players = await cursor.fetchone()
                    metrics.append(("🎮 مرات اللعب المسجلة", f"{total_plays}"))
                    metrics.append(("🧭 لاعبين لعبوا فعلياً", f"{unique_story_players}"))

                if await _table_exists(db, "shared_endings"):
                    cursor = await db.execute("SELECT COUNT(*) FROM shared_endings")
                    shared_endings = (await cursor.fetchone())[0]
                    metrics.append(("🏁 نهايات تمت مشاركتها", f"{shared_endings}"))

                if await _table_exists(db, "decision_votes"):
                    cursor = await db.execute("SELECT COUNT(*) FROM decision_votes")
                    votes = (await cursor.fetchone())[0]
                    metrics.append(("🗳️ إجمالي التصويتات", f"{votes}"))

                if await _table_exists(db, "friend_challenges"):
                    cursor = await db.execute("SELECT COUNT(*) FROM friend_challenges")
                    challenges = (await cursor.fetchone())[0]
                    metrics.append(("⚔️ التحديات الاجتماعية", f"{challenges}"))

            if not metrics or all(value == "0" for _, value in metrics):
                embed = discord.Embed(
                    title="📊 إحصائيات السيرفر",
                    description=(
                        "لا توجد بيانات كافية حتى الآن لعرض إحصائيات مفصلة.\n"
                        "ابدأوا اللعب عبر أوامر القصص، وسنُحدّث اللوحة تلقائياً عند توفر النشاط."
                    ),
                    color=discord.Color.blurple(),
                )
                embed.set_footer(text="💡 جرّبوا /ابدأ أو /قصص_فردية ثم أكملوا قصة لبدء التتبع")
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return

            embed = discord.Embed(
                title="📊 إحصائيات السيرفر",
                description="لوحة موجزة مبنية على البيانات المتاحة حالياً.",
                color=discord.Color.dark_teal(),
            )
            for name, value in metrics:
                embed.add_field(name=name, value=value, inline=True)

            embed.set_footer(text="يتم إخفاء أي قسم غير متوفر تلقائياً للحفاظ على استقرار البوت")
            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as e:
            print(f"[StatsCog] server_stats error: {e}")
            await interaction.response.send_message(
                "⚠️ تعذر تحميل الإحصائيات حالياً. حاول مرة أخرى بعد قليل.",
                ephemeral=True,
            )

    @app_commands.command(name="لوحة_الشرف", description="أفضل اللاعبين حسب عدد القصص المكتملة")
    async def leaderboard(self, interaction: discord.Interaction):
        """Leaderboard based on the reliable players table only."""
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                if not await _table_exists(db, "players"):
                    embed = discord.Embed(
                        title="🏆 لوحة الشرف",
                        description="لا يمكن عرض اللوحة الآن لأن بيانات اللاعبين لم تُنشأ بعد.",
                        color=discord.Color.blurple(),
                    )
                    embed.set_footer(text="جرّب إنهاء قصة واحدة على الأقل لتفعيل اللوحة تلقائياً")
                    await interaction.response.send_message(embed=embed, ephemeral=False)
                    return

                cursor = await db.execute(
                    """
                    SELECT user_id, title, stories_completed
                    FROM players
                    ORDER BY stories_completed DESC, joined_at ASC
                    LIMIT 10
                    """
                )
                rows = await cursor.fetchall()

            if not rows or max((row[2] or 0) for row in rows) <= 0:
                embed = discord.Embed(
                    title="🏆 لوحة الشرف",
                    description="لا يوجد بعد أي لاعب أكمل قصة. كن أول من يصعد إلى القمة!",
                    color=discord.Color.blurple(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return

            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            lines = []
            for idx, (user_id, title, completed) in enumerate(rows, start=1):
                completed = completed or 0
                if completed <= 0:
                    continue
                badge = medals.get(idx, f"`#{idx}`")
                safe_title = title or "الراوي المبتدئ"
                lines.append(f"{badge} <@{user_id}> — **{completed}** قصة مكتملة • {safe_title}")

            if not lines:
                embed = discord.Embed(
                    title="🏆 لوحة الشرف",
                    description="لا يوجد بعد نشاط كافٍ لعرض ترتيب فعلي.",
                    color=discord.Color.blurple(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return

            embed = discord.Embed(
                title="🏆 لوحة الشرف",
                description="أفضل اللاعبين حسب عدد القصص المكتملة:\n\n" + "\n".join(lines),
                color=discord.Color.gold(),
            )
            embed.set_footer(text="يتم تحديث الترتيب تلقائياً كلما اكتملت قصص جديدة.")
            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as e:
            print(f"[StatsCog] leaderboard error: {e}")
            await interaction.response.send_message(
                "⚠️ تعذر تحميل لوحة الشرف حالياً. حاول لاحقاً.",
                ephemeral=True,
            )


async def setup(bot: StoryBot):
    await bot.add_cog(StatsCog(bot))
