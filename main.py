import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

import database

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    database.setup_tables()
    print(f"{bot.user.name} is ready to go.")

@bot.event
async def on_member_join(member):
    database.add_user(str(member.id), str(member.name))

    role = discord.utils.get(member.guild.roles, name="Viewer")
    if role:
        await member.add_roles(role)
        print(f"Assigned 'Viewer' role to {member.name}")
    else:
        print(f"Role 'Viewer' not found.")

@bot.command(name='registeruser')
async def register_user(ctx, discord_id: str):
    user = ctx.guild.get_member(int(discord_id))

    if user is not None:
        database.add_user(str(user.id), str(user.name))
        await ctx.send(f"User {user.name} ({user.id}) added to database.")

@bot.command(name='addseason')
async def add_season(ctx, name: str, number: int):
    database.add_season(name, number)
    await ctx.send(f"Season {number}: {name} added to database.")

@bot.command(name='removeseason')
async def remove_season(ctx, name: str, number: int):
    database.remove_season(name, number)
    await ctx.send(f"Season {number}: {name} removed from database.")

@bot.command(name='addtribe')
async def add_tribe(ctx, tribe_name: str, season_name: str):
    database.add_tribe(tribe_name, season_name)
    await ctx.send(f"{tribe_name} Tribe added from Season {season_name} added to database.")

@bot.command(name='addplayer')
async def add_player(ctx, discord_id, season_name):
    database.add_player(discord_id, season_name)
    await ctx.send(f"{discord_id} has been added to season {season_name}.")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)