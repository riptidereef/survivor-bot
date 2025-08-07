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
    
    await interaction.response.defer()
    
    if not re.fullmatch(r"([A-Fa-f0-9]{6})", color):
        await interaction.followup.send("Invalid color format. Please provide a valid 6-digit hex color code (i.e. #abd123).", ephemeral=True)
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

        await arrange_roles(guild)

        await interaction.followup.send(f"Tribe **{role_name}** added to season **{guild.name}**!")

    elif result == 0:
        if iteration == 1:
            await interaction.followup.send(f"Tribe **{name}** already exists for this season.")
        else:
            await interaction.followup.send(f"Tribe **{name}** {iteration}.0 already exists for this season.")
    else:
        await interaction.followup.send(f"Something went wrong while adding the tribe.")

@bot.tree.command(name="addplayer", description="Add a new player to the current season.")
@app_commands.describe(
    name="The name of the player to be added.", 
    user="The Discord account of the player to be added.",
    tribe="Optional tribe to assign the player to.",
    iteration="Optional season iteration (default is 1)."
)
async def addplayer(interaction: discord.Interaction, name: str, user: Member, tribe: str = None, iteration: int = 1):

    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    
    await interaction.response.defer()

    discord_id = user.id
    server_id = interaction.guild.id

    result = database.add_player(name, discord_id, server_id, tribe, iteration)

    if result == 1:
        tribe_info = database.get_user_tribe(server_id, discord_id)
        role_color = discord.Color.default()

        if tribe_info and tribe_info.get("color"):
            try:
                color_value = int(tribe_info["color"], 16)
                role_color = discord.Color(color_value)
            except Exception as e:
                pass

        await guild.create_role(name=name, 
                                color=role_color,
                                mentionable=True,
                                reason=f"Created player role for {name}.")

        await arrange_roles(guild)

        await interaction.followup.send(f"**{name}** has been added to the current season.")

    elif result == 0:
        await interaction.followup.send(f"**{name}** is already a player in the current season.")
    elif result == -1:
        await interaction.followup.send("That user has not been added to the system yet.")
    elif result == -2:
        await interaction.followup.send("No season found for this server. Make sure a season is created before adding players.")
    elif result == -3:
        await interaction.followup.send(f"The tribe **{tribe} (iteration {iteration})** does not exist in the current season.")
    else:
        await interaction.followup.send("An unknown error occurred while trying to add the player.")

# FIXME: MAKE CUSTOM
@bot.tree.command(name="listtribes", description="List all tribes in the current season.")
async def listtribes(interaction: discord.Interaction):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return
    
    server_id = str(guild.id)

    tribes = database.get_tribes(server_id)

    if not tribes:
        await interaction.response.send_message("No tribes found for this season.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"Tribes in {guild.name}",
        color=discord.Color.blue()
    )

    for tribe in tribes:
        role_name = tribe["name"] if tribe["iteration"] == 1 else f"{tribe['name']} {tribe['iteration']}.0"
        color_code = tribe["color"]
        rank = tribe["rank"]

        embed.add_field(
            name=f"{role_name}",
            value=f"Color: `#{color_code}`\nRank: **{rank}**",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

role_arrangement = ['Host', 'Survivor Bot', 'Immunity', 'Tribes', 'Castaway', 'Players', 'Trusted Viewer', 'Viewer']
async def arrange_roles(guild: discord.Guild):

    bot_member = await guild.fetch_member(guild.me.id)
    bot_top_role = bot_member.top_role

    server_id = str(guild.id)
    tribes = database.get_tribes(server_id)

    if not tribes:
        print("No tribes found.")
        return

    all_roles = await guild.fetch_roles()
    role_map = {role.name: role for role in all_roles}

    # List of tribe roles, already sorted by rank
    tribe_roles = []
    for tribe in tribes:
        if tribe["iteration"] == 1:
            role_name = tribe["name"]
        else:
            role_name = f"{tribe['name']} {tribe['iteration']}.0"

        role = role_map.get(role_name)
        if role:
            # Role already exists in the server
            if role.position < bot_top_role.position:
                tribe_roles.append(role)
            else: # Role above the bot's role, can't change
                pass
        else:
            # Role doesn't exist in the server yet
            pass


    players = database.get_players(server_id)
    player_roles = []
    for player in players:
        player_name = player["display_name"]
        role = role_map.get(player_name)
        if role:
            if role.position < bot_top_role.position:
                player_roles.append(role)
            else:
                pass
        else:
            pass


    arranged_roles = []
    for name in role_arrangement:
        if name == "Tribes":
            arranged_roles.extend(tribe_roles)
        elif name == "Players":
            arranged_roles.extend(player_roles)
        else:
            role = role_map.get(name)
            if role and role.position < bot_top_role.position:
                arranged_roles.append(role)

    prev_role = bot_top_role
    for role in arranged_roles:
        if role.position >= bot_top_role.position:
            continue
        
        try:
            await role.move(above=prev_role)
            prev_role = role

        except Exception as e:
            print(f"Failed to move role '{role.name}': {e}")

# FIXME: MAKE CUSTOM
@bot.tree.command(name="listplayers", description="List all players in the current season.")
async def listplayers(interaction: discord.Interaction):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return

    server_id = str(guild.id)
    players = database.get_players(server_id)

    if not players:
        await interaction.response.send_message("No players found for this season.", ephemeral=True)
        return

    # Print to console for debugging
    for player in players:
        print(
            f"ID: {player['id']}, "
            f"Display Name: {player['display_name']}, "
            f"Discord ID: {player['discord_id']}, "
            f"Username: {player['username']}, "
            f"Tribe: {player['tribe_name'] or 'None'} "
            f"(Iteration: {player['tribe_iteration'] or 'N/A'})"
        )

    # Also send to Discord
    embed = discord.Embed(
        title=f"Players in {guild.name}",
        color=discord.Color.green()
    )

    for player in players:
        tribe_display = (
            f"{player['tribe_name']} {player['tribe_iteration']}.0"
            if player['tribe_name'] else "No Tribe"
        )
        embed.add_field(
            name=player['display_name'],
            value=f"User: {player['username']} (`{player['discord_id']}`)\nTribe: {tribe_display}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)



bot.run(token, log_handler=handler, log_level=logging.DEBUG)