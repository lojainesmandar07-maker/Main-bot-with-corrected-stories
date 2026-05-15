import discord
from typing import List, Dict
from engine.models import Choice

class VoteButton(discord.ui.Button):
    def __init__(self, choice: Choice, custom_id: str):
        style = discord.ButtonStyle.primary
        if choice.color == "secondary": style = discord.ButtonStyle.secondary
        elif choice.color == "success": style = discord.ButtonStyle.success
        elif choice.color == "danger": style = discord.ButtonStyle.danger

        super().__init__(style=style, label=choice.text, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        view: VotingView = self.view
        user_id = interaction.user.id

        if user_id in view.votes:
            # Change vote
            view.votes[user_id] = self.custom_id
            await interaction.response.send_message(f"✅ تم تغيير تصويتك إلى: {self.label}", ephemeral=True)
        else:
            # New vote
            view.votes[user_id] = self.custom_id
            await interaction.response.send_message(f"✅ تم تسجيل تصويتك: {self.label}", ephemeral=True)


class VotingView(discord.ui.View):
    def __init__(self, choices: List[Choice], timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.choices = choices
        self.votes: Dict[int, str] = {} # user_id -> custom_id
        self.message = None

        for i, choice in enumerate(self.choices):
            custom_id = f"choice_{i}"
            self.add_item(VoteButton(choice=choice, custom_id=custom_id))

    def get_results(self) -> Dict[str, int]:
        results = {child.custom_id: 0 for child in self.children if isinstance(child, discord.ui.Button)}
        for vote in self.votes.values():
            results[vote] += 1
        return results

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass
