import json
import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio

from core.bot import StoryBot

DB_PATH = "data/nexus.db"


async def init_social_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS collective_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                options_json TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                channel_id INTEGER,
                message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_votes (
                decision_id INTEGER,
                user_id INTEGER,
                option_index INTEGER,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (decision_id, user_id),
                FOREIGN KEY (decision_id) REFERENCES collective_decisions(id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS friend_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER,
                target_user_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


class DecisionVoteView(discord.ui.View):
    """Persistent decision-voting view used by both commands and startup restore."""

    def __init__(self, decision_id: int, options: list[str]):
        super().__init__(timeout=None)
        self.decision_id = decision_id
        self.options = options[:5]

        for idx, option in enumerate(self.options):
            btn = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label=(option[:80] if option else f"خيار {idx + 1}"),
                custom_id=f"decision_vote_{decision_id}_{idx}",
            )
            btn.callback = self._make_callback(idx)
            self.add_item(btn)

    def _make_callback(self, option_index: int):
        async def callback(interaction: discord.Interaction):
            try:
                async with aiosqlite.connect(DB_PATH) as db:
                    row = await db.execute(
                        "SELECT is_active FROM collective_decisions WHERE id = ?",
                        (self.decision_id,),
                    )
                    decision = await row.fetchone()
                    if not decision or decision[0] != 1:
                        await interaction.response.send_message("❌ هذا القرار لم يعد نشطاً.", ephemeral=True)
                        return

                    await db.execute(
                        """
                        INSERT INTO decision_votes (decision_id, user_id, option_index)
                        VALUES (?, ?, ?)
                        ON CONFLICT(decision_id, user_id) DO UPDATE SET
                            option_index = excluded.option_index,
                            voted_at = CURRENT_TIMESTAMP
                        """,
                        (self.decision_id, interaction.user.id, option_index),
                    )
                    await db.commit()

                    count_row = await db.execute(
                        "SELECT COUNT(*) FROM decision_votes WHERE decision_id = ?",
                        (self.decision_id,),
                    )
                    total_votes = (await count_row.fetchone())[0]

                await interaction.response.send_message(
                    f"✅ تم تسجيل تصويتك على الخيار رقم {option_index + 1}. (إجمالي الأصوات: {total_votes})",
                    ephemeral=True,
                )
            except Exception as e:
                print(f"[SocialCog] vote error: {e}")
                await interaction.response.send_message("⚠️ تعذر تسجيل التصويت حالياً.", ephemeral=True)

        return callback


async def _get_active_decision():
    async with aiosqlite.connect(DB_PATH) as db:
        row = await db.execute(
            """
            SELECT id, question, options_json
            FROM collective_decisions
            WHERE is_active = 1
            ORDER BY id DESC
            LIMIT 1
            """
        )
        return await row.fetchone()


class SocialCog(commands.Cog):
    def __init__(self, bot: StoryBot):
        self.bot = bot
        asyncio.create_task(init_social_db())

    @app_commands.command(name="قصص_جماعية", description="تصفح واختر قصصاً متعددة اللاعبين")
    async def multiplayer_stories(self, interaction: discord.Interaction):
        # We will point this to the world browser, pre-filtered for multiplayer if possible,
        # or just open the world browser as the central hub.
        from ui.embeds import EmbedBuilder
        from ui.world_browser import WorldSelectView
        embed = EmbedBuilder.world_select_embed()
        embed.description = "اختر عالم **القصص الجماعية 👥** من القائمة أدناه لبدء اللعب مع أصدقائك."
        await interaction.response.send_message(embed=embed, view=WorldSelectView())

    @app_commands.command(name="إنشاء_قرار", description="إنشاء قرار جماعي جديد للتصويت (للإدارة فقط)")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        question="سؤال القرار",
        option_1="الخيار الأول",
        option_2="الخيار الثاني",
        option_3="الخيار الثالث (اختياري)",
        option_4="الخيار الرابع (اختياري)",
        channel="القناة التي يُنشر فيها القرار (اختياري)",
    )
    async def create_decision(
        self,
        interaction: discord.Interaction,
        question: str,
        option_1: str,
        option_2: str,
        option_3: str | None = None,
        option_4: str | None = None,
        channel: discord.TextChannel | None = None,
    ):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ هذا الأمر مخصص للإدارة فقط.", ephemeral=True)
            return

        options = [option_1.strip(), option_2.strip()]
        if option_3 and option_3.strip():
            options.append(option_3.strip())
        if option_4 and option_4.strip():
            options.append(option_4.strip())

        if len(options) < 2:
            await interaction.response.send_message("❌ يجب توفير خيارين على الأقل.", ephemeral=True)
            return

        target_channel = channel or interaction.channel
        if not target_channel:
            await interaction.response.send_message("❌ لا يمكن نشر القرار في هذه الوجهة.", ephemeral=True)
            return

        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE collective_decisions SET is_active = 0, closed_at = CURRENT_TIMESTAMP WHERE is_active = 1")
                cursor = await db.execute(
                    """
                    INSERT INTO collective_decisions (question, options_json, is_active, created_by)
                    VALUES (?, ?, 1, ?)
                    """,
                    (question.strip(), json.dumps(options, ensure_ascii=False), interaction.user.id),
                )
                decision_id = cursor.lastrowid
                await db.commit()

            embed = discord.Embed(
                title="🗳️ قرار جماعي جديد",
                description=question,
                color=discord.Color.blurple(),
            )
            for i, opt in enumerate(options, start=1):
                embed.add_field(name=f"الخيار {i}", value=opt, inline=False)
            embed.set_footer(text=f"صوّت من الأزرار أدناه • معرف القرار: {decision_id}")

            view = DecisionVoteView(decision_id, options)
            message = await target_channel.send(embed=embed, view=view)

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE collective_decisions SET channel_id = ?, message_id = ? WHERE id = ?",
                    (target_channel.id, message.id, decision_id),
                )
                await db.commit()

            await interaction.response.send_message("✅ تم إنشاء القرار ونشره بنجاح.", ephemeral=True)
        except Exception as e:
            print(f"[SocialCog] create_decision error: {e}")
            await interaction.response.send_message("⚠️ تعذر إنشاء القرار حالياً.", ephemeral=True)

    @app_commands.command(name="قرار_اجتماعي", description="عرض القرار الجماعي النشط والتصويت عليه")
    async def latest_decision(self, interaction: discord.Interaction):
        try:
            record = await _get_active_decision()
            if not record:
                await interaction.response.send_message(
                    "ℹ️ لا يوجد قرار اجتماعي نشط حالياً.\n"
                    "تابع القنوات العامة، أو اطلب من الإدارة إنشاء قرار عبر `/إنشاء_قرار`.",
                    ephemeral=True,
                )
                return

            decision_id, question, options_json = record
            try:
                options = json.loads(options_json)
            except Exception:
                options = []

            if not isinstance(options, list) or not options:
                await interaction.response.send_message("⚠️ بيانات القرار الحالي غير صالحة.", ephemeral=True)
                return

            embed = discord.Embed(
                title="🗳️ القرار الجماعي الحالي",
                description=question,
                color=discord.Color.blurple(),
            )
            for i, opt in enumerate(options[:5], start=1):
                embed.add_field(name=f"الخيار {i}", value=opt, inline=False)
            embed.set_footer(text="اختيارك قابل للتعديل أثناء بقاء القرار نشطاً.")

            await interaction.response.send_message(
                embed=embed,
                view=DecisionVoteView(decision_id, options),
                ephemeral=True,
            )
        except Exception as e:
            print(f"[SocialCog] latest_decision error: {e}")
            await interaction.response.send_message("⚠️ تعذر جلب القرار الاجتماعي.", ephemeral=True)

    @app_commands.command(name="سجل_القرارات", description="عرض آخر القرارات الجماعية")
    async def decisions_history(self, interaction: discord.Interaction):
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                row = await db.execute(
                    """
                    SELECT id, question, is_active, created_at
                    FROM collective_decisions
                    ORDER BY id DESC
                    LIMIT 5
                    """
                )
                items = await row.fetchall()

            if not items:
                await interaction.response.send_message(
                    "ℹ️ لا يوجد سجل قرارات بعد.\n"
                    "عند نشر أول قرار جماعي سيظهر تاريخه هنا.",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title="🧾 سجل القرارات",
                description="آخر 5 قرارات جماعية (من الأحدث إلى الأقدم).",
                color=discord.Color.dark_blue(),
            )
            for decision_id, question, is_active, created_at in items:
                status = "نشط ✅" if is_active == 1 else "مغلق"
                embed.add_field(
                    name=f"#{decision_id} • {status}",
                    value=f"{question[:140]}\nتاريخ الإنشاء: {created_at}",
                    inline=False,
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[SocialCog] decisions_history error: {e}")
            await interaction.response.send_message("⚠️ تعذر عرض سجل القرارات حالياً.", ephemeral=True)


async def setup(bot: StoryBot):
    await bot.add_cog(SocialCog(bot))
