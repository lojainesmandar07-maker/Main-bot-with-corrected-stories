import discord
from discord import app_commands
from discord.ext import commands, tasks
from core.bot import StoryBot
from core.config import get_config
import aiosqlite
import datetime

DB_PATH = "data/nexus.db"

async def init_mystery_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mystery_rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                riddle TEXT,
                answer TEXT,
                hint TEXT,
                winner_id INTEGER,
                exclusive_story_id INTEGER,
                opens_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                message_id INTEGER
            )
        """)
        await db.commit()


def get_mystery_channel_id() -> int | None:
    world_channels = get_config("world_channels", {})
    target = (
        world_channels.get("general_channel")
        or world_channels.get("endings_channel")
        or get_config("test_channel")
    )
    try:
        return int(target) if target else None
    except Exception:
        return None


class MysteryRoomModal(discord.ui.Modal, title="إنشاء غرفة الغموض"):
    riddle = discord.ui.TextInput(label="اللغز", style=discord.TextStyle.paragraph, required=True)
    answer = discord.ui.TextInput(label="الجواب", style=discord.TextStyle.short, required=True)
    hint = discord.ui.TextInput(label="تلميح (اختياري)", style=discord.TextStyle.paragraph, required=False)
    story_id = discord.ui.TextInput(label="رقم القصة الحصرية", style=discord.TextStyle.short, required=True)
    days = discord.ui.TextInput(label="أيام قبل الفتح للكل", style=discord.TextStyle.short, default="7", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            s_id = int(self.story_id.value)
            d_val = int(self.days.value)
        except ValueError:
            await interaction.response.send_message("❌ يجب أن يكون رقم القصة وعدد الأيام أرقاماً صحيحة.", ephemeral=True)
            return

        opens_at = datetime.datetime.utcnow() + datetime.timedelta(days=d_val)

        story = interaction.client.story_manager.get_story(s_id)
        if not story:
            await interaction.response.send_message(
                "❌ رقم القصة غير صالح. استخدم `/قصص_فردية` لاختيار قصة موجودة أولاً.",
                ephemeral=True,
            )
            return

        target_channel_id = get_mystery_channel_id()
        if not target_channel_id:
             await interaction.response.send_message("❌ لم يتم تحديد قناة عامة لنشر اللغز في الإعدادات.", ephemeral=True)
             return

        channel = interaction.client.get_channel(target_channel_id)
        if not channel:
             await interaction.response.send_message("❌ القناة المحددة غير موجودة.", ephemeral=True)
             return

        embed = discord.Embed(
            title="🚪 غرفة الغموض الجديدة",
            description=f"**لقد ظهر لغز جديد في النيكسوس!**\n\n{self.riddle.value}\n\n*أول من يقوم بحل اللغز عبر `/حل` سيحصل على وصول حصري لقصة سرية!*",
            color=discord.Color.dark_magenta()
        )
        embed.set_footer(text="استخدم /تلميح إذا احتجت مساعدة لاحقاً")

        msg = await channel.send(embed=embed)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO mystery_rooms (riddle, answer, hint, exclusive_story_id, opens_at, message_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.riddle.value, self.answer.value, self.hint.value, s_id, opens_at, msg.id))
            await db.commit()

        await interaction.response.send_message("✅ تم إنشاء غرفة الغموض ونشر اللغز بنجاح!", ephemeral=True)


class MysteryCog(commands.Cog):
    def __init__(self, bot: StoryBot):
        self.bot = bot

    async def single_story_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        stories = self.bot.story_manager.get_stories_by_mode("single").values()
        needle = (current or "").strip().casefold()
        out: list[app_commands.Choice[str]] = []
        for story in stories:
            sid = str(story.id)
            label = f"{story.title} ({sid})"
            if needle and needle not in label.casefold():
                continue
            out.append(app_commands.Choice(name=label[:100], value=sid))
            if len(out) >= 25:
                break
        return out

    async def cog_load(self):
        try:
            await init_mystery_db()
            if not self.check_opens_loop.is_running():
                self.check_opens_loop.start()
        except Exception as e:
            print(f"[MysteryCog] init error: {e}")

    def cog_unload(self):
        self.check_opens_loop.cancel()

    @tasks.loop(hours=1.0)
    async def check_opens_loop(self):
        """Background task: check if opens_at passed -> announce story now open for all"""
        now = datetime.datetime.utcnow()
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT id, exclusive_story_id FROM mystery_rooms WHERE is_active = 1 AND opens_at <= ?", (now,))
            expired_rooms = await cursor.fetchall()

            for r_id, story_id in expired_rooms:
                await db.execute("UPDATE mystery_rooms SET is_active = 0 WHERE id = ?", (r_id,))
                await db.commit()

                # Announce
                ch_id = get_mystery_channel_id()
                if ch_id:
                    channel = self.bot.get_channel(ch_id)
                    if channel:
                        story = self.bot.story_manager.get_story(story_id)
                        s_name = story.title if story else f"قصة #{story_id}"
                        embed = discord.Embed(
                            title="🔓 انفتحت أبواب الغموض",
                            description=f"القصة الحصرية **{s_name}** أصبحت الآن متاحة للجميع للعب!\nاستخدم `/لعب_فردي` لاستكشافها.",
                            color=discord.Color.green()
                        )
                        try:
                            await channel.send(embed=embed)
                        except Exception as e:
                            print(f"[MysteryCog] announce open error: {e}")

    @check_opens_loop.before_loop
    async def before_check_opens(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="غرفة_جديدة", description="إنشاء لغز وغرفة غموض جديدة (للإدارة فقط)")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        story_ref="القصة الحصرية (اختياري - سيتم جلبها من الملف)",
        riddle="نص اللغز (اختياري)",
        answer="الجواب الصحيح (اختياري)",
        days="عدد الأيام قبل فتح القصة للجميع",
        hint="تلميح اختياري",
    )
    @app_commands.autocomplete(story_ref=single_story_autocomplete)
    async def new_mystery_room(
        self,
        interaction: discord.Interaction,
        story_ref: str | None = None,
        riddle: str | None = None,
        answer: str | None = None,
        days: app_commands.Range[int, 1, 30] = 7,
        hint: str | None = None,
    ):
        try:
            if not interaction.user.guild_permissions.manage_guild:
                await interaction.response.send_message("❌ هذا الأمر مخصص للإدارة فقط.", ephemeral=True)
                return

            import json

            try:
                def _load_json():
                    with open("data/mystery_rooms.json", "r", encoding="utf-8") as f:
                        return json.load(f)
                all_rooms = await asyncio.to_thread(_load_json)
            except Exception as e:
                print(f"[MysteryCog] error loading mystery_rooms.json: {e}")
                await interaction.response.send_message("⚠️ تعذر تحميل ملف الغرف.", ephemeral=True)
                return

            if not all_rooms:
                await interaction.response.send_message("❌ ملف غرف الغموض فارغ.", ephemeral=True)
                return

            async with aiosqlite.connect(DB_PATH) as db:
                row = await db.execute("SELECT COUNT(*) FROM mystery_rooms")
                count = (await row.fetchone())[0]

            index = count % len(all_rooms)
            room_data = all_rooms[index]

            auto_riddle = room_data.get("riddle", riddle)
            auto_answer = room_data.get("answer", answer)
            auto_story_ref = room_data.get("exclusive_story_id", story_ref)
            auto_hint = room_data.get("hint", hint)

            story = self.bot.story_manager.resolve_story(auto_story_ref, game_mode="single")
            if not story or not isinstance(story.id, int):
                await interaction.response.send_message("❌ القصة المختارة غير صالحة لغرفة الغموض.", ephemeral=True)
                return

            opens_at = datetime.datetime.utcnow() + datetime.timedelta(days=int(days))
            target_channel_id = get_mystery_channel_id()
            if not target_channel_id:
                await interaction.response.send_message("❌ لم يتم تحديد قناة عامة لنشر اللغز في الإعدادات.", ephemeral=True)
                return

            channel = self.bot.get_channel(target_channel_id)
            if not channel:
                await interaction.response.send_message("❌ القناة المحددة غير موجودة.", ephemeral=True)
                return

            embed = discord.Embed(
                title="🚪 غرفة الغموض الجديدة",
                description=f"**لقد ظهر لغز جديد في النيكسوس!**\n\n{auto_riddle}\n\n*أول من يقوم بحل اللغز عبر `/حل` سيحصل على وصول حصري لقصة سرية!*",
                color=discord.Color.dark_magenta()
            )
            embed.set_footer(text="استخدم /تلميح إذا احتجت مساعدة لاحقاً")
            msg = await channel.send(embed=embed)

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("""
                    INSERT INTO mystery_rooms (riddle, answer, hint, exclusive_story_id, opens_at, message_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (auto_riddle, auto_answer, auto_hint or "", story.id, opens_at, msg.id))
                await db.commit()

            await interaction.response.send_message(
                f"✅ تم إنشاء غرفة الغموض ونشر اللغز بنجاح للقصة **{story.title}**.",
                ephemeral=True,
            )
        except Exception as e:
            print(f"Error in new_mystery_room: {e}")
            await interaction.response.send_message("⚠️ حدث خطأ أثناء تنفيذ الأمر.", ephemeral=True)

    @app_commands.command(name="حل", description="حاول حل اللغز النشط في غرفة الغموض")
    @app_commands.describe(answer="جواب اللغز الخاص بك")
    async def solve_mystery(self, interaction: discord.Interaction, answer: str):
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute("SELECT id, answer, winner_id, exclusive_story_id FROM mystery_rooms WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
                room = await cursor.fetchone()

            if not room:
                await interaction.response.send_message("❌ لا توجد غرفة غموض نشطة حالياً.", ephemeral=True)
                return

            r_id, correct_answer, winner_id, story_id = room

            if winner_id:
                await interaction.response.send_message("❌ لقد قام شخص آخر بحل اللغز مسبقاً! انتظر حتى تتاح القصة للجميع.", ephemeral=True)
                return

            user_ans = answer.strip().lower()
            db_ans = correct_answer.strip().lower()

            if user_ans == db_ans:
                # Correct!
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute("UPDATE mystery_rooms SET winner_id = ? WHERE id = ?", (interaction.user.id, r_id))
                    await db.commit()

                story = self.bot.story_manager.get_story(story_id)
                s_name = story.title if story else f"القصة #{story_id}"

                # Announce winner
                ch_id = get_mystery_channel_id()
                if ch_id:
                    channel = self.bot.get_channel(ch_id)
                    if channel:
                        embed = discord.Embed(
                            title="🎉 لغز محلول!",
                            description=f"تهانينا لـ <@{interaction.user.id}> لقد حل اللغز الصحيح للغرفة المظلمة!\n\nلقد حصل على وصول حصري مبكر إلى **{s_name}**.",
                            color=discord.Color.gold()
                        )
                        try:
                            await channel.send(embed=embed)
                        except Exception as e:
                            print(f"[MysteryCog] winner announce error: {e}")

                await interaction.response.send_message(f"✅ جواب صحيح! لقد فككت الشفرة وربحت وصولاً حصرياً إلى **{s_name}**.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ جواب خاطئ. حاول مرة أخرى!", ephemeral=True)
        except Exception as e:
            print(f"Error in solve_mystery: {e}")
            await interaction.response.send_message("⚠️ حدث خطأ أثناء تنفيذ الأمر.", ephemeral=True)

    @app_commands.command(name="تلميح", description="الحصول على تلميح للغز الحالي (متاح بعد 48 ساعة من النشر)")
    async def mystery_hint(self, interaction: discord.Interaction):
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute("SELECT hint, message_id FROM mystery_rooms WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
                room = await cursor.fetchone()

            if not room:
                await interaction.response.send_message("❌ لا توجد غرفة غموض نشطة حالياً.", ephemeral=True)
                return

            hint, msg_id = room
            if not hint:
                await interaction.response.send_message("❌ لا يوجد تلميح لهذا اللغز.", ephemeral=True)
                return

            # Check if 48 hrs passed
            try:
                 creation_time = discord.utils.snowflake_time(msg_id)
                 now = discord.utils.utcnow()
                 if (now - creation_time).total_seconds() < 48 * 3600:
                     time_left = 48 - ((now - creation_time).total_seconds() / 3600)
                     await interaction.response.send_message(f"❌ التلميح لن يكون متاحاً إلا بعد {time_left:.1f} ساعة.", ephemeral=True)
                     return
            except Exception:
                 pass

            embed = discord.Embed(
                title="💡 تلميح اللغز",
                description=hint,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in mystery_hint: {e}")
            await interaction.response.send_message("⚠️ حدث خطأ أثناء تنفيذ الأمر.", ephemeral=True)

async def setup(bot: StoryBot):
    await bot.add_cog(MysteryCog(bot))
