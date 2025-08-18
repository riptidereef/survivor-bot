import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands, Member
import logging
import os
from dotenv import load_dotenv
import re
import database
from server_structure import *

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='main.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def autocomplete_players(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    guild = interaction.guild
    if not guild:
        return []
    
    player_names = database.get_player_names(guild.id)

    choices = [app_commands.Choice(name=p, value=p) for p in player_names if current.lower() in p.lower()]

    return choices[:25]

async def autocomplete_tribes(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    guild = interaction.guild
    if not guild:
        return []
    
    tribe_names = database.get_tribe_names(guild.id)

    seen = set()
    unique_names = []
    for name in tribe_names:
        if name not in seen:
            seen.add(name)
            unique_names.append(name)

    choices = [app_commands.Choice(name=p, value=p) for p in unique_names if current.lower() in p.lower()]

    return choices[:25]

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
    
    guild_id = guild.id
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
                       order_id="The precedence in which the tribe occurs (i.e. starting tribe, swapped, merge, etc).")
async def addtribe(interaction: discord.Interaction, name: str, iteration: int = 1, color: str = 'd3d3d3', order_id: int = 1):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    if not re.fullmatch(r"([A-Fa-f0-9]{6})", color):
        await interaction.followup.send("Invalid color format. Please provide a valid 6-digit hex color code (i.e. #abd123).", ephemeral=True)
        return
    
    server_id = guild.id

    result = database.add_tribe(name, server_id, iteration, color, order_id)

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
@app_commands.autocomplete(tribe=autocomplete_tribes)
async def addplayer(interaction: discord.Interaction, name: str, user: Member, tribe: str = None, iteration: int = 1):

    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    
    discord_id = user.id
    server_id = interaction.guild.id

    player_names = database.get_player_names(server_id)
    if name in player_names:
        await interaction.response.send_message(f"Player **{name}** already exists in the current season.")
        return

    await interaction.response.defer()
    
    result = database.add_player(name, discord_id, server_id, tribe, iteration)

    if result == 1:
        tribe_info = database.get_player_tribe(server_id, name)
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

@bot.tree.command(name="listtribes", description="List all tribes in the current season.")
async def listtribes(interaction: discord.Interaction):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return
    
    server_id = guild.id

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
        order_id = tribe["order_id"]

        embed.add_field(
            name=f"{role_name}",
            value=f"Color: `#{color_code}`\nOrder: **{order_id}**",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

async def arrange_roles(guild: discord.Guild):

    bot_member = await guild.fetch_member(guild.me.id)
    bot_top_role = bot_member.top_role

    server_id = guild.id
    tribes = database.get_tribes(server_id)

    all_roles = await guild.fetch_roles()
    role_map = {role.name: role for role in all_roles}

    # List of tribe roles, already sorted by order_id
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
    for name in ROLE_ORDER:
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

@bot.tree.command(name="listplayers", description="List all players in the current season.")
async def listplayers(interaction: discord.Interaction):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return

    server_id = guild.id
    players = database.get_players(server_id)

    if not players:
        await interaction.response.send_message("No players found for this season.", ephemeral=True)
        return

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

@bot.tree.command(name="revealplayer", description="Reveal a castaway on the season and remove viewer role and assign player roles.")
@app_commands.describe(name="The player to reveal as a castaway.")
@app_commands.autocomplete(name=autocomplete_players)
async def revealplayer(interaction: discord.Interaction, name: str):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    
    player_names = database.get_player_names(guild.id)
    if name not in player_names:
        await interaction.response.send_message(f"Player **{name}** does not exist in the current season.")
        return
    
    await interaction.response.defer()

    season_players = database.get_players(guild.id)
    matched_player = next((p for p in season_players if name == p['display_name']), None)

    if not matched_player:
        await interaction.followup.send("This user is not a player in the current season.")
        return

    viewer_role = discord.utils.get(guild.roles, name="Viewer")
    trusted_viewer_role = discord.utils.get(guild.roles, name="Trusted Viewer")
    castaway_role = discord.utils.get(guild.roles, name="Castaway")
    player_role = discord.utils.get(guild.roles, name=matched_player['display_name'])

    if matched_player["tribe_iteration"] == 1:
        tribe_name = matched_player["tribe_name"]
    else:
        tribe_name = f"{matched_player["tribe_name"]} {matched_player["tribe_iteration"]}.0" 

    if tribe_name:
        tribe_role = discord.utils.get(guild.roles, name=tribe_name)
    else:
        tribe_role = None

    user = await guild.fetch_member(matched_player['discord_id'])

    try:
        roles_to_remove = []
        if viewer_role and viewer_role in user.roles:
            roles_to_remove.append(viewer_role)
        if trusted_viewer_role and trusted_viewer_role in user.roles:
            roles_to_remove.append(trusted_viewer_role)
        
        if roles_to_remove is not None:
            await user.remove_roles(*roles_to_remove)

        roles_to_add = []
        if castaway_role is not None and castaway_role not in user.roles:
            roles_to_add.append(castaway_role)

        if player_role is not None and player_role not in user.roles:
            roles_to_add.append(player_role)
        
        if tribe_role is not None and tribe_role not in user.roles:
            roles_to_add.append(tribe_role)

        if roles_to_add is not None:
            await user.add_roles(*roles_to_add)

        await interaction.followup.send(f"Successfully revealed player **{matched_player['display_name']}**.")

    except Exception as e:
        print(f"Failed to reveal castaway: {e}")

@bot.tree.command(name="setupcategories", description="Arrange the server category structure.")
async def setupcategories(interaction: discord.Interaction):
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    
    await interaction.response.defer()

    category_map = {category.name: category for category in guild.categories}

    category_list = []
    for category in CATEGORY_STRUCTURE:

        # Skip category (don't create/arrange on setup)
        create_on_setup = category.get("create_on_setup")
        if not create_on_setup:
            continue

        server_category = category_map.get(category["name"])
        if server_category is not None:
            # Category already exists in the server
            category_list.append(server_category)
        else:
            # Create category because it doesn't exist yet
            new_category = await guild.create_category(name=category["name"])
            category_list.append(new_category)

    for cat in category_list:
        print(cat.name)

    await arrange_categories(guild)
        
    await interaction.followup.send("Done.")

async def arrange_categories(guild: discord.guild):

    category_map = {category.name: category for category in guild.categories}
    
    category_list = []
    for category in CATEGORY_STRUCTURE:

        # TODO: Categories with dyanmic arrangements

        server_category = category_map.get(category["name"])
        if server_category is not None:
            category_list.append(server_category)

    previous_category = None
    for i, category in enumerate(category_list):
        if i == 0:
            await category.move(beginning=True)
        else:
            await category.move(after=previous_category)
        previous_category = category

class TribeSetupButtons(discord.ui.View):
    def __init__(self, tribe: str, iteration: int = 1):
        super().__init__(timeout=None)
        self.tribe = tribe
        self.iteration = iteration

    @discord.ui.button(label="Toggle Tribe Chat", style=discord.ButtonStyle.blurple)
    async def tribe_chat_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="Tribes")
        if category is None:
            await interaction.response.send_message("Tribes category not found. Please use /setupcategories first.", ephemeral=True)
            return
        
        if self.iteration == 1:
            channel_name =  self.tribe.lower()
        else:
            channel_name =  f"{self.tribe.lower()}-{self.iteration}"
        
        channel = discord.utils.get(category.channels, name=channel_name)
        if channel is not None:
            # TODO: Add a second check to make sure channel is meant to be deleted.
            print("Deleting channel.")
            await channel.delete()
            await interaction.response.send_message(
                f"Deleted channel #{channel_name}.", ephemeral=True
            )
        else:
            print("Creating new channel.")
            new_channel = await guild.create_text_channel(name=channel_name, category=category)
            await interaction.response.send_message(
                f"Created tribe chat {new_channel.mention}.", ephemeral=True
            )

    @discord.ui.button(label="Toggle Tribe 1-1's", style=discord.ButtonStyle.blurple)
    async def one_on_one_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Make tribe 1-1's in the correct category.", ephemeral=True)

    @discord.ui.button(label="Toggle Tribe VC", style=discord.ButtonStyle.blurple)
    async def tribe_vc_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="Tribes")
        if category is None:
            await interaction.response.send_message("Tribes category not found. Please use /setupcategories first.", ephemeral=True)
            return
        
        voice_channel_name = f"{self.tribe} VC" if self.iteration == 1 else f"{self.tribe} {self.iteration}.0 VC"

        channel = discord.utils.get(category.voice_channels, name=voice_channel_name)
        if channel is not None:
            # TODO: Add a second check to make sure channel is meant to be deleted.
            await channel.delete()
            await interaction.response.send_message(
                f"Deleted channel {voice_channel_name}.", ephemeral=True
            )
        else:
            new_channel = await guild.create_voice_channel(name=voice_channel_name, category=category)
            await interaction.response.send_message(
                f"Created tribe chat {new_channel.mention}.", ephemeral=True
            )

    @discord.ui.button(label="Toggle Tribe Confessionals", style=discord.ButtonStyle.blurple)
    async def tribe_confessional_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Make tribe confessionals in the correct category.", ephemeral=True)

    @discord.ui.button(label="Toggle Individual Submissions", style=discord.ButtonStyle.blurple)
    async def tribe_submissions_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Make tribe submissions in the correct category.", ephemeral=True)

@bot.tree.command(name="setuptribe", description="Perform an action to set up a tribe.")
@app_commands.autocomplete(tribe=autocomplete_tribes)
async def setuptribe(interaction: discord.Interaction, tribe: str, iteration: int = 1):

    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    tribes = database.get_tribes(guild.id)
    
    matching_tribe = next((t for t in tribes if t["name"] == tribe and t["iteration"] == iteration), None)

    if not matching_tribe:
        await interaction.response.send_message("Tribe not found.")
        return
    
    if matching_tribe["iteration"] == 1:
        tribe_name = matching_tribe["name"]
    else:
        tribe_name = f"{matching_tribe["name"]} {matching_tribe["iteration"]}.0"

    color = matching_tribe["color"]
    color_value = int(color, 16)
    discord_color = discord.Color(color_value)
    
    embed = discord.Embed(
        title=tribe_name,
        color=discord_color
    )

    players = database.get_players(guild.id)
    players_string = ""
    for player in players:
        if player["tribe_name"] == matching_tribe["name"] and player["tribe_iteration"] == matching_tribe["iteration"]:
            # Player in the tribe
            players_string += f"{player["display_name"]}\n"
        else:
            continue

    embed.add_field(name="Members:", value=players_string, inline=False)

    view = TribeSetupButtons(tribe=tribe, iteration=iteration)

    await interaction.response.send_message(embed=embed, view=view)

class PlayerSetupButtons(discord.ui.View):
    def __init__(self, name: str):
        super().__init__(timeout=None)
        self.name = name

    @discord.ui.button(label="Toggle Submissions", style=discord.ButtonStyle.blurple)
    async def player_submissions_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="Submissions")
        if category is None:
            await interaction.response.send_message("Submissions category not found. Please use /setupcategories first.", ephemeral=True)
            return
        
        channel_name = f"{self.name.lower()}-submissions"
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is not None:
            # TODO: Add a second check to make sure channel is meant to be deleted.
            await channel.delete()
            await interaction.response.send_message(
                f"Deleted channel {channel_name}.", ephemeral=True
            )
        else:
            new_channel = await guild.create_text_channel(name=channel_name, category=category)
            await interaction.response.send_message(
                f"Created tribe chat {new_channel.mention}.", ephemeral=True
            )

    @discord.ui.button(label="Toggle Confessionals", style=discord.ButtonStyle.blurple)
    async def player_confessionals_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="Confessionals")
        if category is None:
            await interaction.response.send_message("Confessionals category not found. Please use /setupcategories first.", ephemeral=True)
            return
        
        channel_name = f"{self.name.lower()}-confessional"
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is not None:
            # TODO: Add a second check to make sure channel is meant to be deleted.
            await channel.delete()
            await interaction.response.send_message(
                f"Deleted channel {channel_name}.", ephemeral=True
            )
        else:
            new_channel = await guild.create_text_channel(name=channel_name, category=category)
            await interaction.response.send_message(
                f"Created tribe chat {new_channel.mention}.", ephemeral=True
            )

@bot.tree.command(name="setupplayer", description="Perform an action to set up a player.")
@app_commands.autocomplete(name=autocomplete_players)
async def setuptribe(interaction: discord.Interaction, name: str):
    
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    
    player_list = database.get_player_names(guild.id)

    if not name in player_list:
        await interaction.response.send_message("Player not found in season.")
        return
    
    player_tribe = database.get_player_tribe(guild.id, name)
    color = player_tribe["color"]
    color_value = int(color, 16)
    discord_color = discord.Color(color_value)

    player = next((p for p in database.get_players(guild.id) if p["display_name"] == name), None)

    if player is None:
        await interaction.response.send_message("Error: Player data not found.", ephemeral=True)
        return

    discord_user = guild.get_member(player["discord_id"])

    embed = discord.Embed(
        title=name,
        color=discord_color
    )

    embed.add_field(name="User", value=f"{discord_user.mention}: {player["username"]}", inline=False)

    tribe_string = f"{player["tribe_name"]}" if player["tribe_iteration"] == 1 else f"{player["tribe_name"]} {player["tribe_iteration"]}.0"
    tribe_role = discord.utils.get(guild.roles, name=tribe_string)
    embed.add_field(name="Tribe", value=tribe_role.mention, inline=False)

    view = PlayerSetupButtons(name=name)

    await interaction.response.send_message(embed=embed, view=view)


bot.run(token, log_handler=handler, log_level=logging.DEBUG)