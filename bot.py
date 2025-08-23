import discord
from discord.ext import commands
import logging
import os
import asyncio
from dotenv import load_dotenv
from database import connection, queries

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "bot.log")

logger = logging.getLogger("bot_logger")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="w")
formatter = logging.Formatter(
    fmt='[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

COGS = [
    "commands.server_commands",
    "commands.season_commands"
]

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

@bot.tree.error
async def on_app_command_error(interaction, error):
    logger.exception(f"Slash command error: {error}")

async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)

        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped manually.")
    except Exception as e:
        print(f"Bot crashed unexpectedly due to {e}.")