import discord
from typing import List
from engine.models import Choice


class SoloChoiceButton(discord.ui.Button):
    def __init__(self, choice: Choice, index: int, solo_manager, user_id: int):
        style_map = {
            "secondary": discord.ButtonStyle.secondary,
            "success": discord.ButtonStyle.success,
            "danger": discord.ButtonStyle.danger,
        }
        style = style_map.get(choice.color, discord.ButtonStyle.primary)
        super().__init__(
            label=choice.text[:80],
            style=style,
            custom_id=f"solo_{user_id}_{index}"
        )
        self.choice_index = index
        self.solo_manager = solo_manager
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الخيار ليس لك!", ephemeral=True)
            return

        session, error = self.solo_manager.process_choice(self.user_id, self.choice_index)

        if error:
            from ui.embeds import EmbedBuilder
            await interaction.response.send_message(
                embed=EmbedBuilder.error_embed(error), ephemeral=True
            )
            return

        from ui.embeds import EmbedBuilder
        story = session["story"]
        scene = session["scene"]
        points = session["points"]
        round_number = session["round"]

        embed = EmbedBuilder.solo_scene_embed(scene, round_number, story.title, points)

        view = None
        if not scene.is_ending and scene.choices:
            view = SoloView(self.solo_manager, self.user_id, scene.choices)
            if interaction.message:
                view.message = interaction.message
        else:
            self.solo_manager.end_solo_game(self.user_id)

        # First edit the message to finish the interaction response safely
        await interaction.response.edit_message(embed=embed, view=view)

        # Now if it's an ending, we can safely send followups
        if scene.is_ending:
            try:
                from cogs.solo_cog import handle_story_end
                await handle_story_end(interaction, self.user_id, story, scene)
            except Exception as e:
                print(f"Error handling story end: {e}")


class ShareEndingView(discord.ui.View):
    def __init__(self, user_id: int, story_id: int, scene_id: str, ending_text: str, story_title: str):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.story_id = story_id
        self.scene_id = scene_id
        self.ending_text = ending_text
        self.story_title = story_title

        import uuid
        uid = str(uuid.uuid4())[:8]

        btn_share = discord.ui.Button(label="نعم، شارك النهاية", style=discord.ButtonStyle.success, emoji="📣", custom_id=f"share_yes_{uid}")
        btn_share.callback = self.share_btn
        self.add_item(btn_share)

        btn_no = discord.ui.Button(label="لا، احتفظ بها", style=discord.ButtonStyle.secondary, emoji="❌", custom_id=f"share_no_{uid}")
        btn_no.callback = self.no_share_btn
        self.add_item(btn_no)

    async def share_btn(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الخيار ليس لك!", ephemeral=True)
            return

        from core.config import get_config
        import aiosqlite
        import uuid

        # Load endings_channel from config (fallback to test_channel if needed)
        world_channels = get_config("world_channels", {})
        endings_ch_id = world_channels.get("endings_channel") or get_config("test_channel")

        if endings_ch_id:
            try:
                channel = interaction.client.get_channel(int(endings_ch_id))
                if channel:
                    share_id = str(uuid.uuid4())
                    # Format text to avoid overly long messages
                    preview_text = self.ending_text[:1024]

                    embed = discord.Embed(
                        title=f"📣 نهاية شاركها: {interaction.user.display_name}",
                        description=f"**القصة:** {self.story_title}\n\n**النهاية:**\n{preview_text}",
                        color=discord.Color.purple()
                    )
                    embed.set_thumbnail(url=interaction.user.display_avatar.url)
                    embed.set_footer(text=f"معرف المشاركة: {share_id[:8]}")

                    await channel.send(embed=embed)

                    async with aiosqlite.connect("data/nexus.db") as db:
                        await db.execute("""
                            INSERT INTO shared_endings (id, user_id, story_id, ending_id, ending_text)
                            VALUES (?, ?, ?, ?, ?)
                        """, (share_id, self.user_id, self.story_id, self.scene_id, preview_text))
                        await db.commit()

                    await interaction.response.send_message("✅ تم مشاركة نهايتك بنجاح في القناة المخصصة!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ القناة المخصصة للمشاركات غير موجودة.", ephemeral=True)
            except Exception as e:
                print(f"Error sharing: {e}")
                await interaction.response.send_message("⚠️ لم نتمكن من مشاركة النهاية الآن.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ لم يتم إعداد قناة المشاركات في النظام.", ephemeral=True)

        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

    async def no_share_btn(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ هذا الخيار ليس لك!", ephemeral=True)
            return

        await interaction.response.send_message("تفهمنا ذلك، استمتع برحلتك القادمة! 👋", ephemeral=True)
        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)


class SoloView(discord.ui.View):
    def __init__(self, solo_manager, user_id: int, choices: List[Choice]):
        super().__init__(timeout=600)
        self.solo_manager = solo_manager
        self.user_id = user_id
        self.message = None

        for idx, choice in enumerate(choices):
            self.add_item(SoloChoiceButton(choice, idx, solo_manager, user_id))

    async def on_timeout(self):
        self.solo_manager.end_solo_game(self.user_id)
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass
