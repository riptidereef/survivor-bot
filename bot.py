import discord
from discord.ext import commands
import logging
import os
import asyncio
from dotenv import load_dotenv
from database import connection

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.FileHandler(filename='logs/main.log', encoding='utf-8', mode='w')]
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

COGS = [
    "commands.server_commands"
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

    print("Ready to go.")

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