import discord
from discord import app_commands
from discord.ext import commands
import logging
import os
from commands.season_commands import *
from dotenv import load_dotenv
from database import connection, queries

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='logs/bot.log', encoding='utf-8', mode='w')

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

    connection.setup_tables()

    # Add all users from all servers
    user_count = 0
    for guild in bot.guilds:
        print(f"Syncing members from guild: {guild.name}")
        async for member in guild.fetch_members(limit=None):
            if not member.bot:
                discord_id = member.id
                username = str(member)
                success = queries.add_user(discord_id, username)
                if success:
                    user_count += 1

    print(f"Finished syncing {user_count} new users.")
    print("Ready to go.")

bot.tree.add_command(app_commands.Command(
    name="hello",
    description="Say hello to the bot",
    callback=hello
))

bot.tree.add_command(app_commands.Command(
    name="registerseason",
    description="Register a server as a new season in the database.",
    callback=registerseason
))

bot.tree.add_command(app_commands.Command(
    name="addtribe",
    description="Create a new tribe for the season and register it in the database.",
    callback=addtribe
))

bot.tree.add_command(app_commands.Command(
    name="addplayer",
    description="Add a new player to the season and register them in the database.",
    callback=addplayer
))

bot.tree.add_command(app_commands.Command(
    name="setupserver",
    description="Set up the server.",
    callback=setupserver
))

bot.tree.add_command(app_commands.Command(
    name="setupplayer",
    description="Set up a certain player on the season.",
    callback=setupplayer
))

bot.tree.add_command(app_commands.Command(
    name="setupallplayers",
    description="Send all player setup menus registered in the season.",
    callback=setupallplayers
))

bot.tree.add_command(app_commands.Command(
    name="setuptribe",
    description="Set up a certain tribe on the season.",
    callback=setuptribe
))

bot.tree.add_command(app_commands.Command(
    name="setupalltribes",
    description="Send all tribe setup menus registered in the season.",
    callback=setupalltribes
))


bot.run(token, log_handler=handler, log_level=logging.INFO)