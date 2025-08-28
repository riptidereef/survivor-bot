import discord
from discord.ui import View, Button, Select, Modal, TextInput
from models.player import Player

def get_player_embed(player: Player) -> discord.Embed:

    embed = discord.Embed(
        title=player.display_name,
        color=discord.Color.blue()
    )

    return embed

class PlayerSetupButtons(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Test", style=discord.ButtonStyle.blurple)
    async def player_submissions_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Test")