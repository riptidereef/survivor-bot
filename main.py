import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
import logging
import os
from dotenv import load_dotenv

import database

# Setup
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
    guild = discord.Object(id=guild_id)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
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
    database.add_user(int(member.id), str(member.name))

    role = discord.utils.get(member.guild.roles, name="Viewer")
    if role:
        await member.add_roles(role)
        print(f"Assigned 'Viewer' role to {member.name}")
    else:
        print(f"Role 'Viewer' not found.")

@bot.tree.command(name="hello", description="Say hello to the user.")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.name}!", ephemeral=True)


bot.run(token, log_handler=handler, log_level=logging.DEBUG)