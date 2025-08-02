import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands, Member
import logging
import os
from dotenv import load_dotenv
import re

import database

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='main.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    database.setup_tables()

    # Add all users
    for guild in bot.guilds:
        print(f"Syncing members from guild: {guild.name}")
        async for member in guild.fetch_members(limit=None):
            if not member.bot:
                discord_id = str(member.id)
                username = str(member)
                database.add_user(discord_id, username)

    print("Finished syncing users.")

    print("Ready to go.")

@bot.tree.command(name="registerseason", description="Register a server as a new season.")
async def registerseason(interaction: discord.Interaction):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return
    
    guild_id = str(guild.id)
    guild_name = guild.name

    result = database.add_season(guild_id, guild_name)

    if result == 1:
        await interaction.response.send_message(f"Season registered for **{guild_name}**!")
    elif result == 0:
        await interaction.response.send_message(f"**{guild_name}** is already registered.")
    else:
        await interaction.response.send_message(f"Failed to register season.")

@bot.tree.command(name="addtribe", description="Add a new tribe to the current season.")
@app_commands.describe(name="The name of the tribe.", 
                       iteration="The iteration of the tribe (i.e. for swaps, default 1).", 
                       color="Hex color code for the tribe (e.g. ff0000).",
                       rank="The precedence in which the tribe occurs (i.e. starting tribe, swapped, merge, etc).")
async def addtribe(interaction: discord.Interaction, name: str, iteration: int = 1, color: str = 'd3d3d3', rank: int = 1):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return
    
    if not re.fullmatch(r"([A-Fa-f0-9]{6})", color):
        await interaction.response.send_message("Invalid color format. Please provide a valid 6-digit hex color code (i.e. #abd123).", ephemeral=True)
        return
    
    server_id = str(guild.id)

    result = database.add_tribe(name, server_id, iteration, color, rank)

    if result == 1:

        role_name = None
        color_value = int(color, 16)
        discord_color = discord.Color(color_value)

        if iteration == 1:
            role_name = name
        else:
            role_name = f"{name} {iteration}.0"

        await guild.create_role(name=role_name, color=discord_color, mentionable=True, reason="Created tribe role.")

        await interaction.response.send_message(f"Tribe **{role_name}** added to season **{guild.name}**!")

    elif result == 0:
        if iteration == 1:
            await interaction.response.send_message(f"Tribe **{name}** already exists for this season.")
        else:
            await interaction.response.send_message(f"Tribe **{name}** {iteration}.0 already exists for this season.")
    else:
        await interaction.response.send_message(f"Something went wrong while adding the tribe.")

@bot.tree.command(name="addplayer", description="Add a new player to the current season.")
@app_commands.describe(
    name="The name of the player to be added.", 
    user="The Discord account of the player to be added.",
    tribe="Optional tribe to assign the player to.",
    iteration="Optional season iteration (default is 1)."
)
async def addplayer(interaction: discord.Interaction, name: str, user: Member, tribe: str = None, iteration: int = 1):

    if interaction.guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    guild = interaction.guild
    discord_id = user.id
    server_id = interaction.guild.id

    result = database.add_player(name, discord_id, server_id, tribe, iteration)

    if result == 1:
        await interaction.response.send_message(f"**{name}** has been added to the current season.")
    elif result == 0:
        await interaction.response.send_message(f"**{name}** is already a player in the current season.")
    elif result == -1:
        await interaction.response.send_message("That user has not been added to the system yet.")
    elif result == -2:
        await interaction.response.send_message("No season found for this server. Make sure a season is created before adding players.")
    elif result == -3:
        await interaction.response.send_message(f"The tribe **{tribe} (iteration {iteration})** does not exist in the current season.")
    else:
        await interaction.response.send_message("An unknown error occurred while trying to add the player.")

async def arrange_tribe_roles(guild: discord.Guild):
    


bot.run(token, log_handler=handler, log_level=logging.DEBUG)