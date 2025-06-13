import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
import logging
import os
from dotenv import load_dotenv
import re

import database

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
guild_id = int(os.getenv('TEST_GUILD'))

handler = logging.FileHandler(filename='main.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Sync failed: {e}")
        return
    
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    database.setup_tables()
    add_all_users()

def add_all_users():
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot:
                database.add_user(str(member.id), member.name)

@bot.event
async def on_member_join(member):
    database.add_user(str(member.id), str(member.name))

    role = discord.utils.get(member.guild.roles, name="Viewer")
    if role:
        await member.add_roles(role)
    else:
        print(f"Role 'Viewer' not found.")

@bot.tree.command(name="addseason", description="Register a new season to the database.")
async def addseason(interaction: discord.Interaction, name: str, number: int):
    success = database.add_season(name.strip(), number)
    if success:
        await interaction.response.send_message(f"Season **{number}. {name}** added to the database.")
    else:
        await interaction.response.send_message(f"Failed to add season to database.")

@bot.tree.command(name="listseasons", description="List all of the seasons in the database.")
async def listseasons(interaction: discord.Interaction):
    seasons = database.get_all_seasons()

    if not seasons:
        await interaction.response.send_message("No seasons found in the database")
        return
    
    season_list = '**Seasons in the database:**\n'
    for season in seasons:
        season_number = season['number']
        season_name = season['name'].strip()
        season_status = season['status']
        season_list += f"**{season_number}.** **{season_name}** (Status: {season_status})\n"

    await interaction.response.send_message(season_list)


async def autocomplete_season(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    seasons = database.get_all_seasons()
    choices = []

    for season in seasons:
        season_name = season['name'].strip()
        season_number = season['number']
        label = f"{season_number}. {season_name}"

        if current.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=label))

    return choices[-25:]

@bot.tree.command(name="setseason", description="Set an existing season to active and deactivate all others.")
@app_commands.describe(season="Select a season.")
@app_commands.autocomplete(season=autocomplete_season)
async def setseason(interaction: discord.Interaction, season: str):
    try:
        number_part, name_part = season.split('.', 1)
        season_number = int(number_part.strip())
        season_name = name_part.strip()
    except ValueError:
        await interaction.response.send_message("Invalid season format. Please use autocomplete to select a valid one.", ephemeral=True)
        return
    
    success = database.activate_season(season_name, season_number)

    if success:
        await interaction.response.send_message(f"Season **{season_number}. {season_name}** is now active.")
    else:
        await interaction.response.send_message("Could not find that season in the database.", ephemeral=True)

def is_valid_hex_color(color: str) -> bool:
    return re.fullmatch(r"#(?:[0-9a-fA-F]{3}){1,2}", color) is not None

@bot.tree.command(name="addtribe", description="Add a tribe to a certain season.")
@app_commands.describe(season="The season to add the tribe to.", tribe_name="Name of the new tribe", tribe_color="Hex color code (e.g. #FF0000)")
@app_commands.autocomplete(season=autocomplete_season)
async def addtribe(interaction: discord.Interaction, season: str, tribe_name: str, tribe_color: str):

    try:
        number_part, name_part = season.split('.', 1)
        season_number = int(number_part.strip())
        season_name = name_part.strip()
    except ValueError:
        await interaction.response.send_message("Invalid season format. Please use autocomplete to select a valid one.", ephemeral=True)
        return

    if not is_valid_hex_color(tribe_color):
        await interaction.response.send_message(f"Invalid color format. Please use a hex color code like `#FF0000`.", ephemeral=True)
        return
    
    success = database.add_tribe(season_name, tribe_name, tribe_color)

    if success:
        await interaction.response.send_message(f"Tribe **{tribe_name}** with color `{tribe_color}` added to season {season_name}.")
    else:
        await interaction.response.send_message(f"Failed to add tribe. Make sure the season exists and the tribe name is valid.", ephemeral=True)

@bot.tree.command(name="addplayer", description="Add a new player to a season.")
@app_commands.describe(
    season="The season to add the player to.",
    user="The user to register as a player.",
    display_name="The player's in-game name.",
    role_color="The color to assign this player (hex code, e.g. #00ffcc).",
    tribe="Optional: Name of the tribe to assign the player to."
)
@app_commands.autocomplete(season=autocomplete_season)
async def addplayer(interaction: discord.Interaction,
                    season: str,
                    user: discord.Member,
                    display_name: str,
                    role_color: str = '#d3d3d3',
                    tribe: str = None):

    try:
        number_part, name_part = season.split('.', 1)
        season_number = int(number_part.strip())
        season_name = name_part.strip()
    except ValueError:
        await interaction.response.send_message("Invalid season format. Please use autocomplete to select a valid one.", ephemeral=True)
        return
    
    if not is_valid_hex_color(role_color):
        await interaction.response.send_message(f"Invalid color format. Please use a hex color code like `#FF0000`.", ephemeral=True)
        return
    
    success = database.add_player(
        discord_id=str(user.id),
        season_name=season_name,
        display_name=display_name.strip(),
        role_color=role_color.strip(),
        tribe_name=tribe.strip() if tribe else None
    )

    if success:
        await interaction.response.send_message(f"Added **{display_name}** to **{season_name}**!")
    else:
        await interaction.response.send_message("Failed to add player.", ephemeral=True)

async def autocomplete_player(interaction: discord.Interaction, current: str):
    active_season = database.get_active_season()

    if not active_season:
        return []
    
    players = database.get_players(active_season['name'])

    choices = ["ALL"]
    for player in players:
        choices.append(player["display_name"])

    filtered_choices = []
    for name in choices:
        if current.lower() in name.lower():
            filtered_choices.append(app_commands.Choice(name=name, value=name))
    
    filtered_choices = filtered_choices[:25]

    return filtered_choices

@bot.tree.command(name="createsubmissions", description="Create submission channels for players in the current season.")
@app_commands.describe(player="A specific player or type 'ALL' to create channels for all registered players.")
@app_commands.autocomplete(player=autocomplete_player)
async def createsubmissions(interaction: discord.Interaction, player: str):
    
    active_season = database.get_active_season()

    if not active_season:
        await interaction.followup.send("No active season set. Use `/setseason` first.", ephemeral=True)
        return
    



bot.run(token, log_handler=handler, log_level=logging.DEBUG)