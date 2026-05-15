import discord
from discord import app_commands
from discord.ext import commands
import json
from core.config import get_config
import aiosqlite
import datetime
import random
from discord.ext import tasks

DB_PATH = "data/nexus.db"

async def init_npc_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS npc_encounters (
                user_id INTEGER PRIMARY KEY,
                last_encountered TIMESTAMP,
                times_encountered INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def table_exists(db: aiosqlite.Connection, table_name: str) -> bool:
    cursor = await db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return (await cursor.fetchone()) is not None

NPC_PATHS = {
    "fantasy":   "data/npcs/fantasy_npcs.json",
    "past":      "data/npcs/past_npcs.json",
    "future":    "data/npcs/future_npcs.json",
    "alternate": "data/npcs/alternate_npcs.json",
}

WORLD_NAMES = {
    "fantasy":   "الفانتازيا",
    "past":      "الماضي",
    "future":    "المستقبل",
    "alternate": "الواقع البديل",
}

ARCHETYPE_NAMES = {
    "warrior": "المحارب", "guardian": "الحارس", "strategist": "المخطط",
    "shadow": "الظل", "rebel": "المتمرد", "seeker": "الباحث",
    "oracle": "العرّاف", "wanderer": "التائه",
}


def load_npcs(world: str) -> list:
    path = NPC_PATHS.get(world, "")
    if not path:
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_member_archetype(member: discord.Member) -> str | None:
    archetype_roles = get_config("archetype_roles", {})
    role_to_arch = {int(v): k for k, v in archetype_roles.items() if v}
    for role in member.roles:
        if role.id in role_to_arch:
            return role_to_arch[role.id]
    return None


class TopicSelectMenu(discord.ui.Select):
    def __init__(self, npc: dict, member_archetype: str | None):
        self.npc = npc
        self.member_archetype = member_archetype

        options = [
            discord.SelectOption(
                label=t["label"][:100],
                value=t["id"],
                emoji=t.get("emoji", "💬")
            )
            for t in npc.get("topics", [])
        ]
        super().__init__(
            placeholder="اختر موضوع الحوار...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"npc_topic_{npc['id']}"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_id = self.values[0]
        topics = {t["id"]: t for t in self.npc.get("topics", [])}
        topic = topics.get(selected_id)

        if not topic:
            await interaction.response.send_message("❌ موضوع غير موجود.", ephemeral=True)
            return

        # Use archetype-specific response if available
        response = topic["response"]
        if self.member_archetype:
            arch_resp = self.npc.get("archetype_responses", {}).get(self.member_archetype)
            if arch_resp and selected_id == "ask_advice":
                response = arch_resp

        embed = discord.Embed(
            title=f"💬 {self.npc['name']}",
            description=f"*{self.npc.get('personality', '')}*\n\n{response}",
            color=0x4B3D60
        )
        embed.set_footer(text="لخيارات إضافية: أعد استخدام أمر /شخصيات.")
        if self.npc.get("image_url"):
            embed.set_thumbnail(url=self.npc["image_url"])

        await interaction.response.send_message(embed=embed, ephemeral=True)


class NPCView(discord.ui.View):
    def __init__(self, npc: dict, member_archetype: str | None):
        super().__init__(timeout=180)
        if npc.get("topics"):
            self.add_item(TopicSelectMenu(npc, member_archetype))


class RandomEncounterView(discord.ui.View):
    def __init__(self, npc: dict):
        super().__init__(timeout=86400) # Valid for 1 day
        self.npc = npc

        # Add 3 dynamic action buttons for flavor
        actions = ["استمع لقصته", "اسأله عن الأسرار", "تجاهله والمضي قدماً"]
        styles = [discord.ButtonStyle.primary, discord.ButtonStyle.secondary, discord.ButtonStyle.danger]

        for i, action in enumerate(actions):
            btn = discord.ui.Button(
                label=action,
                style=styles[i],
                custom_id=f"rand_encounter_{npc['id']}_{i}"
            )
            btn.callback = self.make_callback(i, action)
            self.add_item(btn)

    def make_callback(self, index: int, action: str):
        async def callback(interaction: discord.Interaction):
            response = ""
            if index == 0:
                response = f"**{self.npc['name']}:** 'لدي الكثير لأرويه... العالم مليء بالقصص، وأنت جزء منها الآن.'"
            elif index == 1:
                response = f"**{self.npc['name']}:** 'الأسرار؟ بعضها أفضل أن يظل مدفوناً في النيكسوس.'"
            else:
                response = f"تترك {self.npc['name']} خلفك وتكمل طريقك في ظلال النيكسوس."

            embed = discord.Embed(
                title=f"📌 اختيارك: {action}",
                description=response,
                color=discord.Color.dark_theme()
            )
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

class NPCCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        try:
            await init_npc_db()
            if not self.weekly_encounter.is_running():
                self.weekly_encounter.start()
        except Exception as e:
            print(f"[NPCCog] init error: {e}")

    def cog_unload(self):
        self.weekly_encounter.cancel()

    @tasks.loop(hours=168.0)
    async def weekly_encounter(self):
        """Weekly random NPC encounter."""
        now = datetime.datetime.utcnow()
        thirty_days_ago = now - datetime.timedelta(days=30)

        try:
            async with aiosqlite.connect(DB_PATH) as db:
                if not await table_exists(db, "story_plays"):
                    return

                # Active players in last 30 days
                cursor = await db.execute(
                    "SELECT DISTINCT user_id FROM story_plays WHERE played_at >= ?",
                    (thirty_days_ago,),
                )
                active_players = [row[0] for row in await cursor.fetchall()]

                # Filter players not encountered in 30 days
                eligible_players = []
                for uid in active_players:
                    cursor = await db.execute(
                        "SELECT last_encountered FROM npc_encounters WHERE user_id = ?",
                        (uid,),
                    )
                    record = await cursor.fetchone()
                    if not record:
                        eligible_players.append(uid)
                    else:
                        try:
                            last_enc = datetime.datetime.fromisoformat(record[0]) if record[0] else None
                        except Exception:
                            last_enc = None
                        if not last_enc or last_enc <= thirty_days_ago:
                            eligible_players.append(uid)
        except Exception as e:
            print(f"[NPCCog] weekly encounter skipped: {e}")
            return

        if not eligible_players:
            return

        target_uid = random.choice(eligible_players)

        # Pick random NPC
        world = random.choice(list(NPC_PATHS.keys()))
        npcs = load_npcs(world)
        if not npcs:
            return
        npc = random.choice(npcs)

        # DM user
        try:
            user = await self.bot.fetch_user(target_uid)
            if user:
                embed = discord.Embed(
                    title="👤 لقاء مفاجئ في النيكسوس...",
                    description=f"بينما تتجول في {WORLD_NAMES[world]}، يظهر أمامك فجأة **{npc['name']}**.\n\n*{npc.get('personality', 'ينظر إليك بصمت...')}*",
                    color=discord.Color.dark_purple()
                )
                embed.set_footer(text="اختر تصرفك من الأزرار أدناه. بعد الاختيار سيتم إغلاق الأزرار.")
                if npc.get("image_url"):
                    embed.set_thumbnail(url=npc["image_url"])

                view = RandomEncounterView(npc)
                await user.send(embed=embed, view=view)

                # Record encounter
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute("""
                        INSERT INTO npc_encounters (user_id, last_encountered, times_encountered)
                        VALUES (?, ?, 1)
                        ON CONFLICT(user_id) DO UPDATE SET
                        last_encountered = ?, times_encountered = times_encountered + 1
                    """, (target_uid, now.isoformat(), now.isoformat()))
                    await db.commit()
        except discord.Forbidden:
            print(f"Failed to send random encounter DM to user {target_uid}. DMs are closed.")
        except Exception as e:
            print(f"Error sending random encounter: {e}")

    @weekly_encounter.before_loop
    async def before_weekly_encounter(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="شخصيات", description="تفاعل مع شخصيات عالم The Nexus")
    @app_commands.choices(world=[
        app_commands.Choice(name="الفانتازيا",    value="fantasy"),
        app_commands.Choice(name="الماضي",         value="past"),
        app_commands.Choice(name="المستقبل",       value="future"),
        app_commands.Choice(name="الواقع البديل", value="alternate"),
    ])
    async def show_npcs(self, interaction: discord.Interaction,
                         world: app_commands.Choice[str]):
        npcs = load_npcs(world.value)
        if not npcs:
            embed = discord.Embed(
                title=f"🌍 شخصيات عالم {world.name}",
                description="لا توجد شخصيات متاحة لهذا العالم حالياً. سنضيف شخصيات جديدة قريباً.",
                color=discord.Color.blurple(),
            )
            embed.set_footer(text="جرّب عالماً آخر من /شخصيات أو عُد لاحقاً")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        member_archetype = get_member_archetype(interaction.user)
        archetype_label = ARCHETYPE_NAMES.get(member_archetype, "غير محددة")

        # Show first NPC — user can run command again for others
        # For simplicity: show all NPCs as a select first, then show chosen NPC
        options = [
            discord.SelectOption(
                label=npc["name"][:100],
                value=npc["id"],
                description=npc.get("title", "")[:100],
                emoji="🧙"
            )
            for npc in npcs
        ]

        class NPCPickView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)
                select = discord.ui.Select(
                    placeholder="اختر الشخصية للتفاعل معها...",
                    options=options,
                    custom_id=f"npc_pick_{world.value}"
                )
                async def on_select(inter: discord.Interaction):
                    chosen_id = select.values[0]
                    chosen_npc = next((n for n in npcs if n["id"] == chosen_id), None)
                    if not chosen_npc:
                        await inter.response.send_message("❌ لم يُعثر على الشخصية.", ephemeral=True)
                        return

                    embed = discord.Embed(
                        title=f"🧙 {chosen_npc['name']}",
                        description=(
                            f"**{chosen_npc.get('title', '')}**\n\n"
                            f"*{chosen_npc.get('personality', '')}*\n\n"
                            f"اختر موضوعاً للحديث عنه من القائمة:"
                        ),
                        color=0x4B3D60
                    )
                    embed.add_field(name="🧬 شخصيتك الحالية", value=archetype_label, inline=False)
                    if chosen_npc.get("image_url"):
                        embed.set_image(url=chosen_npc["image_url"])

                    if not chosen_npc.get("topics"):
                        embed.add_field(
                            name="💬 حالة التفاعل",
                            value="هذه الشخصية لا تملك مواضيع حوار كافية حالياً.",
                            inline=False,
                        )
                        await inter.response.edit_message(embed=embed, view=None)
                        return

                    npc_view = NPCView(chosen_npc, member_archetype)
                    await inter.response.edit_message(embed=embed, view=npc_view)

                select.callback = on_select
                self.add_item(select)

        embed = discord.Embed(
            title=f"🌍 شخصيات عالم {world.name}",
            description="اختر الشخصية، ثم اختر موضوع الحوار لتحصل على تفاعل مخصص.",
            color=0x4B3D60
        )
        embed.add_field(name="🧬 شخصيتك الحالية", value=archetype_label, inline=False)
        await interaction.response.send_message(embed=embed, view=NPCPickView(), ephemeral=True)


async def setup(bot):
    await bot.add_cog(NPCCog(bot))
