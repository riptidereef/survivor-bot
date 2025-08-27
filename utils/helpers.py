import discord
from models.player import Player
from models.tribe import Tribe
from database import queries
from discord import app_commands
    
async def autocomplete_players(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    guild = interaction.guild
    if not guild:
        return []
    
    players = queries.get_player(server_id=guild.id)
    choices = [app_commands.Choice(name=p.display_name, value=p.display_name) for p in players if current.lower() in p.display_name.lower()]

    return choices[:25]

async def autocomplete_tribes(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    guild = interaction.guild
    if not guild:
        return []
    
    tribes = queries.get_tribe(server_id=guild.id)
    choices = [app_commands.Choice(name=t.tribe_string, value=t.tribe_string) for t in tribes if current.lower() in t.tribe_string.lower()]

    return choices[:25]