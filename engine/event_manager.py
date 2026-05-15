import asyncio
import random
import discord
from discord.ext import commands
from typing import Optional
from engine.story_manager import StoryManager
from engine.models import Story, Scene
from ui.embeds import EmbedBuilder
from ui.views import VotingView

class EventManager:
    def __init__(self, bot: commands.Bot, story_manager: StoryManager):
        self.bot = bot
        self.story_manager = story_manager

        self.active_event: bool = False
        self.current_story: Optional[Story] = None
        self.current_scene: Optional[Scene] = None
        self.round_number: int = 0
        self.event_channel: Optional[discord.TextChannel] = None

        self.voting_timeout: float = 30.0
        self.is_stopped: bool = False
        self.event_task: Optional[asyncio.Task] = None

    async def start_event(self, channel: discord.TextChannel, story_id: int | str, voting_timeout: Optional[float] = None):
        if self.active_event:
            await channel.send(embed=EmbedBuilder.error_embed("هناك حدث جارٍ بالفعل في الخادم!"))
            return

        story = self.story_manager.get_story(story_id)
        if not story:
            await channel.send(embed=EmbedBuilder.error_embed(f"القصة رقم {story_id} غير موجودة."))
            return

        self.active_event = True
        self.is_stopped = False
        self.current_story = story
        self.event_channel = channel
        self.round_number = 1
        self.voting_timeout = voting_timeout if voting_timeout is not None else 30.0

        start_scene_id = story.start_scene
        self.current_scene = story.get_scene(start_scene_id)

        if not self.current_scene:
            await channel.send(embed=EmbedBuilder.error_embed("خطأ: المشهد الأول غير موجود في بيانات القصة."))
            self._reset_state()
            return

        # Start the event loop
        try:
            await channel.send(embed=EmbedBuilder.event_start_embed(story))
            await asyncio.sleep(5) # give players a moment to read intro
            self.event_task = self.bot.loop.create_task(self._run_event_loop())
        except Exception as e:
            print(f"Error starting event in channel {channel}: {e}")
            await channel.send(embed=EmbedBuilder.error_embed(f"حدث خطأ أثناء محاولة بدء القصة: {e}"))
            self._reset_state()

    async def stop_event(self, channel: discord.TextChannel):
        if not self.active_event:
            await channel.send(embed=EmbedBuilder.error_embed("لا يوجد حدث نشط حالياً لإيقافه."))
            return

        self.is_stopped = True
        if self.event_task and not self.event_task.done():
            self.event_task.cancel()

        await channel.send(embed=EmbedBuilder.event_stopped_embed())
        self._reset_state()

    async def _run_event_loop(self):
        try:
            while self.active_event and not self.is_stopped:
                # 1. Post the scene
                embed = EmbedBuilder.scene_embed(
                    self.current_scene,
                    self.round_number,
                    self.current_story.title,
                    int(self.voting_timeout),
                )

                # If it's an ending scene, stop here
                if self.current_scene.is_ending or not self.current_scene.choices:
                    await self.event_channel.send(embed=embed)
                    # Notify profile system — credit all recent voters
                    try:
                        from cogs.profile_cog import on_story_complete
                        if 'view' in locals() and view and hasattr(view, 'votes'):
                            for voter_id in view.votes.keys():
                                await on_story_complete(voter_id, self.event_channel)
                    except Exception:
                        pass
                    self._reset_state()
                    break

                # 2. Setup Voting
                view = VotingView(choices=self.current_scene.choices, timeout=self.voting_timeout)
                message = await self.event_channel.send(embed=embed, view=view)
                view.message = message

                # 3. Wait for voting to finish
                await asyncio.sleep(self.voting_timeout)

                # Check if event was stopped during voting
                if self.is_stopped:
                    break

                # 4. Tally votes and pick winner
                results = view.get_results()
                try:
                    await message.edit(view=view) # Updates the view to disabled state (from on_timeout if needed)
                except (discord.NotFound, discord.Forbidden):
                    pass # Ignore if the original message was deleted

                # Dramatic Pause
                loading_msg = await self.event_channel.send("⏳ يتم فرز الأصوات الآن...")
                await asyncio.sleep(2)
                try:
                    await loading_msg.edit(content="🥁 يتم تحديد مصير القصة...")
                except (discord.NotFound, discord.Forbidden):
                    pass
                await asyncio.sleep(2)

                max_votes = -1
                winning_choices = []

                for choice_id, votes in results.items():
                    if votes > max_votes:
                        max_votes = votes
                        winning_choices = [choice_id]
                    elif votes == max_votes:
                        winning_choices.append(choice_id)

                # 5. Handle Tie breaking
                if len(winning_choices) > 1:
                    winning_id = random.choice(winning_choices)
                    choice_index = int(winning_id.split('_')[1])
                    winning_choice = self.current_scene.choices[choice_index]

                    try:
                        await loading_msg.edit(content="", embed=EmbedBuilder.tie_break_embed(
                            winning_choice_text=winning_choice.text,
                            total_votes=max_votes
                        ))
                    except (discord.NotFound, discord.Forbidden):
                        await self.event_channel.send(embed=EmbedBuilder.tie_break_embed(
                            winning_choice_text=winning_choice.text,
                            total_votes=max_votes
                        ))
                else:
                    winning_id = winning_choices[0]
                    choice_index = int(winning_id.split('_')[1])
                    winning_choice = self.current_scene.choices[choice_index]

                    try:
                        await loading_msg.edit(content="", embed=EmbedBuilder.voting_result_embed(
                            winning_choice_text=winning_choice.text,
                            total_votes=max_votes
                        ))
                    except (discord.NotFound, discord.Forbidden):
                        await self.event_channel.send(embed=EmbedBuilder.voting_result_embed(
                            winning_choice_text=winning_choice.text,
                            total_votes=max_votes
                        ))

                # 6. Advance to next scene
                next_scene_id = winning_choice.next_scene
                next_scene = self.current_story.get_scene(next_scene_id)

                if not next_scene:
                    await self.event_channel.send(embed=EmbedBuilder.error_embed(f"خطأ: المشهد التالي ({next_scene_id}) غير موجود."))
                    self._reset_state()
                    break

                self.current_scene = next_scene
                self.round_number += 1

                # Give a short delay before next round starts
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            # Task was cancelled, exit cleanly
            pass
        except Exception as e:
            print(f"Unexpected error in _run_event_loop: {e}")
            if self.event_channel:
                try:
                    await self.event_channel.send(embed=EmbedBuilder.error_embed("حدث خطأ غير متوقع أثناء تشغيل الحدث. تم الإيقاف."))
                except Exception:
                    pass
            self._reset_state()


    def _reset_state(self):
        self.active_event = False
        self.current_story = None
        self.current_scene = None
        self.round_number = 0
        self.event_channel = None
        self.is_stopped = False
        self.event_task = None
