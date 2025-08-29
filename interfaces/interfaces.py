import discord
from discord.ui import View, Button, Select, Modal, TextInput
from models.player import Player
from models.tribe import Tribe
import config
from database import queries
from utils.helpers import *

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

class SetupServerButtons(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Server Categories", style=discord.ButtonStyle.blurple)
    async def setupcategories(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return
    
        await interaction.response.defer()

        previous_category = None
        for category_dict in config.CATEGORY_STRUCTURE:

            if not category_dict.get("create_on_setup", False):
                continue

            category_name = category_dict["name"]
            category = discord.utils.get(guild.categories, name=category_name)

            if category is None:
                category = await guild.create_category(name=category_name)

            if previous_category is None:
                await category.move(beginning=True)
            else:
                await category.move(after=previous_category)

            previous_category = category
        
        await interaction.followup.send("Done.")

    @discord.ui.button(label="(Future) Base Roles", style=discord.ButtonStyle.blurple)
    async def setupplayerroles(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return
        await interaction.response.send_message("Setting up base roles.")

    @discord.ui.button(label="Player Roles", style=discord.ButtonStyle.blurple)
    async def setupplayerroles(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return
        
        await interaction.response.defer()

        players = queries.get_player(server_id=guild.id)
        previous_role = discord.utils.get(guild.roles, name="Castaway")
        for player in players:
            player_role = discord.utils.get(guild.roles, name=player.display_name)
            if player_role is None:
                player_tribe = get_first(queries.get_tribe(server_id=guild.id, player_display_name=player.display_name))
                if player_tribe is not None:
                    player_role = await guild.create_role(name=player.display_name, color=discord.Color(int(player_tribe.color, 16)))
                else:
                    player_role = await guild.create_role(name=player.display_name)

            if previous_role is None:
                await player_role.move(beginning=True)
            else:
                await player_role.move(above=previous_role)

            previous_role = player_role

        await interaction.followup.send("Done.")

    @discord.ui.button(label="Tribe Roles", style=discord.ButtonStyle.blurple)
    async def setuptriberoles(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        await interaction.response.defer()

        tribes = queries.get_tribe(server_id=guild.id)
        previous_role = discord.utils.get(guild.roles, name="Immunity")
        for tribe in tribes:
            tribe_role = discord.utils.get(guild.roles, name=tribe.tribe_string)
            if tribe_role is None:
                tribe_role = await guild.create_role(name=tribe.tribe_string, color=discord.Color(int(tribe.color, 16)))

            if previous_role is None:
                await tribe_role.move(beginning=True)
            else:
                await tribe_role.move(above=previous_role)

            previous_role = tribe_role

        await interaction.followup.send("Done.")