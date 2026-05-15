import discord
from discord import app_commands
from discord.ext import commands, tasks
from core.bot import StoryBot
from core.config import load_config
import aiosqlite
import datetime
import json
import random

DB_PATH = "data/nexus.db"

DAILY_QUESTIONS = [
    {
        "q": "لو كان بإمكانك إيقاف الزمن لمدة ساعة واحدة، ماذا ستفعل؟",
        "opts": ["أقرأ كل الكتب التي لم أقرأها 📚", "أستكشف الأماكن المغلقة 🏰", "أرتاح في صمت تام 🧘‍♂️", "أصلح أخطاء الماضي ⏪"]
    },
    {
        "q": "أي عالم من هذه العوالم تفضل العيش فيه للأبد؟",
        "opts": ["عالم سحري بفرسان وتنانين 🐉", "عالم مستقبلي مليء بالتكنولوجيا 🤖", "عالم موازٍ يعكس أحلامك المظلمة 🌌", "عالم بدائي يعتمد على الطبيعة فقط 🌿"]
    },
    {
        "q": "لقد وجدت قطعة أثرية تمنحك قوة واحدة. ماذا تختار؟",
        "opts": ["قراءة الأفكار 🧠", "الاختفاء عن الأنظار 👻", "الطيران في السماء 🦅", "التحكم بالعناصر الأربعة 🌋"]
    },
    {
        "q": "هل تفضل أن تكون...",
        "opts": ["بطلاً مجهولاً يُنقذ الجميع 🦸‍♂️", "شريراً مشهوراً يحكم العالم 🦹", "حكيماً منعزلاً يعرف كل الأسرار 🧙", "رحالاً يزور جميع الأكوان 🌌"]
    }
]


async def init_daily_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_pulse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_str TEXT UNIQUE,
                question TEXT,
                options_json TEXT,
                message_id INTEGER,
                channel_id INTEGER,
                is_closed BOOLEAN DEFAULT 0
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_pulse_votes (
                pulse_id INTEGER,
                user_id INTEGER,
                option_index INTEGER,
                PRIMARY KEY (pulse_id, user_id),
                FOREIGN KEY (pulse_id) REFERENCES daily_pulse(id)
            )
            """
        )
        await db.commit()


class DailyCog(commands.Cog):
    def __init__(self, bot: StoryBot):
        self.bot = bot

    async def cog_load(self):
        try:
            await init_daily_db()
            if not self.daily_loop.is_running():
                self.daily_loop.start()
        except Exception as e:
            print(f"[DailyCog] init error: {e}")

    def cog_unload(self):
        self.daily_loop.cancel()

    @tasks.loop(minutes=1.0)
    async def daily_loop(self):
        """Checks every minute if it's time to post the daily pulse."""
        try:
            config = load_config()
            if str(config.get("pulse_enabled", "0")) != "1":
                return
            target_time_str = config.get("pulse_time")
            target_channel_id = config.get("pulse_channel_id")
        except Exception as e:
            print(f"[DailyCog] daily loop skipped: {e}")
            return

        if not target_time_str or not target_channel_id:
            return

        now = datetime.datetime.utcnow()
        current_time_str = now.strftime("%H:%M")

        if current_time_str == target_time_str:
            date_str = now.strftime("%Y-%m-%d")

            # Check if we already posted today
            async with aiosqlite.connect(DB_PATH) as db:
                row = await db.execute("SELECT id FROM daily_pulse WHERE date_str = ?", (date_str,))
                if await row.fetchone():
                    return # Already posted today

            # Not posted, time to post!
            channel = self.bot.get_channel(int(target_channel_id))
            if not channel:
                return

            await self.post_daily_pulse(channel, date_str)

    @daily_loop.before_loop
    async def before_daily_loop(self):
        await self.bot.wait_until_ready()

    async def post_daily_pulse(self, channel: discord.TextChannel, date_str: str) -> bool:
        # 1. Announce yesterday's results if exists
        await self.announce_results(channel, date_str)

        # 2. Ensure we don't duplicate today's pulse
        async with aiosqlite.connect(DB_PATH) as db:
            row = await db.execute("SELECT id, is_closed FROM daily_pulse WHERE date_str = ?", (date_str,))
            existing = await row.fetchone()
            if existing:
                return False

        # 3. Fetch sequential question
        try:
            def _load_json():
                with open("data/daily_pulse.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            daily_questions = await asyncio.to_thread(_load_json)
        except Exception as e:
            print(f"[DailyCog] Failed to load daily_pulse.json: {e}")
            return False

        if not daily_questions:
            return False

        async with aiosqlite.connect(DB_PATH) as db:
            row = await db.execute("SELECT COUNT(*) FROM daily_pulse")
            count = (await row.fetchone())[0]

        index = count % len(daily_questions)
        q_data = daily_questions[index]
        question = q_data["q"]
        options = q_data["opts"]
        options_json = json.dumps(options, ensure_ascii=False)

        # 4. Save to DB
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                INSERT INTO daily_pulse (date_str, question, options_json, channel_id, is_closed)
                VALUES (?, ?, ?, ?, 0)
            """, (date_str, question, options_json, channel.id))
            pulse_id = cursor.lastrowid
            await db.commit()

        # 5. Post message
        embed = discord.Embed(
            title="❤️‍🔥 نبضة اليوم",
            description=f"**{question}**\n\nصوت لخيارك المفضل أدناه!",
            color=discord.Color.brand_red()
        )
        embed.set_footer(text=f"تاريخ النبضة: {date_str} • سيتم إعلان النتائج غداً")

        view = DailyPulseView(pulse_id, options)
        msg = await channel.send(embed=embed, view=view)

        # 6. Update DB with message ID
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE daily_pulse SET message_id = ? WHERE id = ?", (msg.id, pulse_id))
            await db.commit()
        return True

    async def announce_results(self, channel: discord.TextChannel, current_date: str):
        """Announce results for the most recent unclosed pulse that is older than today."""
        async with aiosqlite.connect(DB_PATH) as db:
            row = await db.execute(
                """
                SELECT id, question, options_json, date_str
                FROM daily_pulse
                WHERE is_closed = 0 AND date_str < ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (current_date,),
            )
            pulse = await row.fetchone()

            if not pulse:
                return

            pulse_id, question, options_json, date_str = pulse
            options = json.loads(options_json)

            # Count votes
            votes_row = await db.execute("SELECT option_index, COUNT(*) FROM daily_pulse_votes WHERE pulse_id = ? GROUP BY option_index", (pulse_id,))
            votes_data = await votes_row.fetchall()

            # Close the pulse
            await db.execute("UPDATE daily_pulse SET is_closed = 1 WHERE id = ?", (pulse_id,))
            await db.commit()

        if not votes_data:
            # No votes
            embed = discord.Embed(
                title="📊 نتائج نبضة الأمس",
                description=f"**السؤال:** {question}\n\nلم يقم أحد بالتصويت يوم أمس. 😔",
                color=discord.Color.light_grey()
            )
            await channel.send(embed=embed)
            return

        # Format results
        vote_counts = {i: 0 for i in range(len(options))}
        total_votes = 0
        for opt_idx, count in votes_data:
            vote_counts[opt_idx] = count
            total_votes += count

        results_text = f"**إجمالي الأصوات:** {total_votes}\n\n"

        # Sort by count descending
        sorted_opts = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)

        for idx, count in sorted_opts:
            percent = int((count / total_votes) * 100) if total_votes > 0 else 0
            bar = "█" * (percent // 10) + "░" * (10 - (percent // 10))
            results_text += f"**{options[idx]}**\n{bar} {percent}% ({count} أصوات)\n\n"

        embed = discord.Embed(
            title=f"📊 نتائج نبضة الأمس ({date_str})",
            description=f"**السؤال:** {question}\n\n{results_text}",
            color=discord.Color.green()
        )

        await channel.send(embed=embed)


    @app_commands.command(name="نبضة_اليوم", description="عرض أو نشر نبضة اليوم الحالية (للإدارة فقط)")
    @app_commands.default_permissions(manage_guild=True)
    async def pulse_command(self, interaction: discord.Interaction):
        try:
            # Admin can force post
            if interaction.user.guild_permissions.manage_guild:
                channel_id = load_config().get("pulse_channel_id")

                if not channel_id:
                    await interaction.response.send_message("❌ الرجاء إعداد قناة للنبضة أولاً عبر أمر `/إعداد_النيكسوس`.", ephemeral=True)
                    return

                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    await interaction.response.send_message("❌ القناة المحددة غير موجودة.", ephemeral=True)
                    return

                date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
                created = await self.post_daily_pulse(channel, date_str)
                if created:
                    await interaction.response.send_message(
                        "✅ تم نشر نبضة اليوم، وتم إعلان نتائج النبضة السابقة إن وُجدت.",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        "ℹ️ نبضة اليوم منشورة بالفعل لهذا التاريخ. يمكنك تعديل الإعدادات من `/إعداد_النيكسوس`.",
                        ephemeral=True,
                    )
                return

            # Regular user
            await interaction.response.send_message(
                "هذا الأمر مخصص للمشرفين للتحكم بالنظام.\n"
                "للمشاركة: راقب قناة النبضة اليومية وصوّت مباشرة من الأزرار عند نشر النبضة.",
                ephemeral=True,
            )
        except Exception as e:
            print(f"Error in pulse_command: {e}")
            await interaction.response.send_message("⚠️ حدث خطأ أثناء تنفيذ الأمر.", ephemeral=True)


class DailyPulseView(discord.ui.View):
    def __init__(self, pulse_id: int, options: list):
        super().__init__(timeout=None)
        self.pulse_id = pulse_id

        # Add a button for each option
        for i, opt in enumerate(options):
            # Limit button label length
            label = opt if len(opt) <= 80 else opt[:77] + "..."
            btn = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label=label,
                custom_id=f"pulse_vote_{pulse_id}_{i}"
            )
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, option_index: int):
        async def callback(interaction: discord.Interaction):
            try:
                async with aiosqlite.connect(DB_PATH) as db:
                    # Check if closed
                    row = await db.execute("SELECT is_closed FROM daily_pulse WHERE id = ?", (self.pulse_id,))
                    pulse = await row.fetchone()
                    if not pulse or pulse[0] == 1:
                        await interaction.response.send_message("❌ انتهى التصويت على هذه النبضة.", ephemeral=True)
                        return

                    # Insert or update vote
                    await db.execute("""
                        INSERT INTO daily_pulse_votes (pulse_id, user_id, option_index)
                        VALUES (?, ?, ?)
                        ON CONFLICT(pulse_id, user_id) DO UPDATE SET option_index = ?
                    """, (self.pulse_id, interaction.user.id, option_index, option_index))
                    await db.commit()

                await interaction.response.send_message("✅ تم تسجيل تصويتك بنجاح!", ephemeral=True)
            except Exception as e:
                print(f"Error voting: {e}")
                await interaction.response.send_message("⚠️ عذراً، حدث خطأ أثناء التصويت.", ephemeral=True)
        return callback

async def setup(bot: StoryBot):
    await bot.add_cog(DailyCog(bot))
