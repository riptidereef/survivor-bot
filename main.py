import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
import logging
import os
from dotenv import load_dotenv

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

@bot.tree.command(name="hello", description="Say hello to the user.")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.name}!")

@bot.tree.command(name="addseason", description="Register a new season to the database.")
async def addseason(interaction: discord.Interaction, name: str, number: int):
    database.add_season(name.strip(), number)
    await interaction.response.send_message(f"Season **{name} (#{number})** added to the database.")

@bot.tree.command(name="listseasons", description="List all of the seasons in the database.")
async def listseasons(interaction: discord.Interaction):
    seasons = database.get_all_seasons()

    if not seasons:
        await interaction.response.send_message("No seasons found in the database")
        return
    
    season_list = "**Seasons in the database:**\n"
    for season in seasons:
        season_number = season['number']
        season_name = season['name'].strip()
        season_status = season['status']
        season_list += f"**{season_number}. {season_name}** (Status: {season_status})\n"

    await interaction.response.send_message(season_list)

async def autocomplete_season(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    seasons = database.get_all_seasons()

@bot.tree.command(name="setseason", description="Set an existing season to active and deactivate all others.")
async def setseason(interaction: discord.Interaction, season: str):
    pass

bot.run(token, log_handler=handler, log_level=logging.DEBUG)