import discord
from models.player import Player
from models.tribe import Tribe
from database import queries
from discord import app_commands
from typing import Iterable, TypeVar, Optional
import re

T = TypeVar("T")
def get_first(iterable: Iterable[T], default: Optional[T] = None) -> Optional[T]:
    """Return the first item of an iterable, or a default if empty."""
    return next(iter(iterable), default)

def parse_tribe_string(tribe_string: str):
    match = re.match(r"^(.*?)(?:\s+(\d+)\.0)?$", tribe_string.strip())
    if not match:
        raise ValueError(f"Invalid tribe string: {tribe_string}")
    tribe_name = match.group(1).strip()
    iteration = int(match.group(2)) if match.group(2) else 1
    return tribe_name, iteration
    
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