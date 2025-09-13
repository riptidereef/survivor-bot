import discord
from database import queries
from discord import app_commands
from typing import Iterable, TypeVar, Optional
import re
import config
from player import Player
from tribe import Tribe
import asyncio

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

async def arrange_categories(guild: discord.Guild):
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

async def arrange_player_roles(guild: discord.Guild):
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
        else:
            player_tribe = get_first(queries.get_tribe(server_id=guild.id, player_display_name=player.display_name))
            if player_tribe is not None:
                await player_role.edit(color=discord.Color(int(player_tribe.color, 16)))
            else:
                await player_role.edit(color=discord.Color.default)

        if previous_role is None:
            await player_role.move(beginning=True)
        else:
            await player_role.move(above=previous_role)

        previous_role = player_role

async def arrange_tribe_roles(guild: discord.Guild):
    tribes = queries.get_tribe(server_id=guild.id)
    previous_role = discord.utils.get(guild.roles, name="Immunity")
    for tribe in tribes:
        tribe_role = discord.utils.get(guild.roles, name=tribe.tribe_string)
        if tribe_role is None:
            tribe_role = await guild.create_role(name=tribe.tribe_string, color=discord.Color(int(tribe.color, 16)))
        else:
            await tribe_role.edit(color=discord.Color(int(tribe.color, 16)))

        if previous_role is None:
            await tribe_role.move(beginning=True)
        else:
            await tribe_role.move(above=previous_role)

        previous_role = tribe_role

async def arrange_tribe_confessionals(guild: discord.Guild):
    confessional_category = discord.utils.get(guild.categories, name="Confessionals")
    tribes_list = queries.get_tribe(server_id=guild.id)

    category_order = [confessional_category]
    for tribe in tribes_list:
        category_name = f"{tribe.tribe_string} Confessionals"
        found_category = discord.utils.get(guild.categories, name=category_name)
        if found_category:
            category_order.append(found_category)

    prev_category = category_order[0]
    for category in category_order:
        if category is not confessional_category:
            await category.move(after=prev_category)
        prev_category = category

async def arrange_tribe_submissions(guild: discord.Guild):
    submissions_category = discord.utils.get(guild.categories, name="Submissions")
    tribes_list = queries.get_tribe(server_id=guild.id)

    category_order = [submissions_category]
    for tribe in tribes_list:
        category_name = f"{tribe.tribe_string} Submissions"
        found_category = discord.utils.get(guild.categories, name=category_name)

        if found_category:
            category_order.append(found_category)

    prev_category = category_order[0]
    for category in category_order:
        if category is not submissions_category:
            await category.move(after=prev_category)
        prev_category = category

async def arrange_tribe_1_1_categories(guild: discord.Guild):
    one_on_ones_category = discord.utils.get(guild.categories, name="1-1's")
    tribes_list = queries.get_tribe(server_id=guild.id)

    category_order = [one_on_ones_category]
    for tribe in tribes_list:
        category_name = f"{tribe.tribe_string} 1-1's"
        found_category = discord.utils.get(guild.categories, name=category_name)

        if found_category:
            category_order.append(found_category)

    prev_category = category_order[0]
    for category in category_order:
        if category is not one_on_ones_category:
            await category.move(after=prev_category)
        prev_category = category

async def swap_player_tribe(guild: discord.Guild, player: Player, new_tribe: Tribe):
    player.tribe_id = new_tribe.tribe_id

    queries.edit_player(server_id=guild.id, player=player, new_tribe=new_tribe)

    tribe_role = discord.utils.get(guild.roles, name=new_tribe.tribe_string)
    player_role = discord.utils.get(guild.roles, name=player.display_name)
    player_user = await player.get_discord_user(guild)

    if player_user:
        castaway_role = discord.utils.get(player_user.roles, name="Castaway")

    if castaway_role and tribe_role and player_user:
        await player_user.add_roles(tribe_role)

    if player_role:
        await player_role.edit(color=discord.Color(int(new_tribe.color, 16)))

async def alphabetize_category(category: discord.CategoryChannel):
    text_channels = list(category.text_channels)
    sorted_channels = sorted(text_channels, key=lambda c: c.name)

    previous_channel = None
    for channel in sorted_channels:
        if previous_channel is None:
            await channel.move(beginning=True)
        else:
            await channel.move(after=previous_channel)
        previous_channel = channel
        await asyncio.sleep(0.25)

def extract_number(name: str) -> int:
    match = re.search(r"(\d+)", name)
    return int(match.group(1)) if match else 0

async def arrange_tribal_channels(category: discord.CategoryChannel):
    text_channels = [ch for ch in category.text_channels]

    sorted_channels = sorted(text_channels, key=lambda c: (extract_number(c.name), c.name))

    previous_channel = None
    for channel in sorted_channels:
        if previous_channel is None:
            await channel.move(beginning=True)
        else:
            await channel.move(after=previous_channel)
        previous_channel = channel

async def lock_1_1(guild: discord.Guild, channel: discord.TextChannel, role1: discord.Role, role2: discord.Role):
    if not channel.name.endswith("-🔒"):
        new_name = f"{channel.name}-🔒"
        await channel.edit(name=new_name)

    for role in (role1, role2):
        overwrite = channel.overwrites_for(role)
        overwrite.send_messages = False
        await channel.set_permissions(role, overwrite=overwrite)

async def unlock_1_1(guild: discord.Guild, channel: discord.TextChannel, role1: discord.Role, role2: discord.Role):
    if channel.name.endswith("-🔒"):
        new_name = channel.name[:-2]
        await channel.edit(name=new_name)

    for role in (role1, role2):
        overwrite = channel.overwrites_for(role)
        overwrite.send_messages = False
        await channel.set_permissions(role, overwrite=overwrite)

async def alphabetize_categories(guild: discord.Guild, categories: list[discord.CategoryChannel]):
    
    all_channels = []
    for c in categories:
        all_channels.extend(c.text_channels)

    all_channels.sort(key=lambda ch: ch.name)

    buckets: list[list[discord.TextChannel]] = []
    for i in range(0, len(all_channels), 50):
        buckets.append(all_channels[i:i+50])

    new_category_list = []
    for category in categories:
        new_category = await guild.create_category(name=category.name, overwrites=category.overwrites)
        await new_category.move(after=category)
        new_category_list.append(new_category)

    for i, bucket in enumerate(buckets):
        for pos, channel in enumerate(bucket):
            await channel.edit(category=new_category_list[i], position=pos)
            await asyncio.sleep(0.25)

    for category in categories:
        await category.delete()
    
