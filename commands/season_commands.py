import discord
from discord import app_commands
from utils.helpers import *
import re
from interfaces.interfaces import *

@app_commands.autocomplete(player_name=autocomplete_players)
async def hello(interaction: discord.Interaction, player_name: str):
    await interaction.response.send_message(f"Hello {player_name}!")

async def registerseason(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return
    guild_id = guild.id
    guild_name = guild.name
    result = queries.add_season(server_id=guild_id, server_name=guild_name)

    if result == 1:
        await interaction.response.send_message(f"Season registered for **{guild_name}**!")
    elif result == 0:
        await interaction.response.send_message(f"**{guild_name}** is already registered.")
    else:
        await interaction.response.send_message(f"Failed to register season.")

@app_commands.describe(
    tribe_name="The name of the tribe.", 
    iteration="The iteration of the tribe (i.e. for swaps, default 1).", 
    color="Hex color code for the tribe (e.g. ff0000).",
    order_id="The precedence in which the tribe occurs (i.e. starting tribe, swapped, merge, etc)."
)
async def addtribe(interaction: discord.Interaction, tribe_name: str, iteration: int = 1, color: str = 'd3d3d3', order_id: int = 1):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
        return
    
    await interaction.response.defer()

    if not re.fullmatch(r"([A-Fa-f0-9]{6})", color):
        await interaction.followup.send("Invalid color format. Please provide a valid 6-digit hex color code (i.e. abd123).", ephemeral=True)
        return

    server_id = guild.id
    result = queries.add_tribe(
            tribe_name=tribe_name, 
            server_id=server_id, 
            iteration=iteration, 
            color=color, 
            order_id=order_id
    )

    new_tribe = get_first(queries.get_tribe(server_id=server_id, tribe_name=tribe_name, tribe_iteration=iteration))
    tribe_string = new_tribe.tribe_string if new_tribe is not None else ""

    if result == 1:
        await interaction.followup.send(f"Successfully added tribe **{tribe_string}**.", ephemeral=False)
    elif result == 0:
        await interaction.followup.send(f"Tribe **{tribe_string}** already exists in the database for this season.", ephemeral=True)
    elif result == -1:
        await interaction.followup.send(f"An unexpected error occurred while adding tribe **{tribe_string}**. Please try again or check the logs.", ephemeral=True)
    elif result == -2:
        await interaction.followup.send(f"Cannot add tribe **{tribe_string}** because no season is registered for this server. Please register a season first using `/registerseason`.", ephemeral=True)
    else:
        await interaction.followup.send(f"Unknown result code `{result}` encountered while adding tribe **{tribe_string}**. Please report this issue.", ephemeral=True)

@app_commands.describe(
    player_name="The name of the player to be added.", 
    discord_user="The Discord account of the player to be added.",
    tribe_string="Optional tribe to assign the player to."
)
@app_commands.autocomplete(tribe_string=autocomplete_tribes)
async def addplayer(interaction: discord.Interaction, player_name: str, discord_user: discord.Member, tribe_string: str = None):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    
    discord_id = discord_user.id
    server_id = interaction.guild.id
    tribe_name, tribe_iteration = parse_tribe_string(tribe_string)

    await interaction.response.defer()
    
    result, player = queries.add_player(player_name, discord_id, server_id, tribe_name, tribe_iteration)

    if result == 1:
        await interaction.followup.send(f"**{player.display_name}** has been added to the current season.")
    elif result == 0:
        await interaction.followup.send(f"A player with the name **{player_name}** already exists in this season.")
    elif result == -1:
        await interaction.followup.send("An unexpected error occurred while adding the player. Please check the logs or try again.")
    elif result == -2:
        await interaction.followup.send(f"The Discord user with ID `{discord_id}` has not been added to the system yet.")
    elif result == -3:
        await interaction.followup.send("No season found for this server. Make sure a season is created before adding players.")
    elif result == -4:
        await interaction.followup.send(f"The tribe **{tribe_name} (iteration {tribe_iteration})** does not exist in the current season.")
    elif result == -5:
        await interaction.followup.send(f"The display name **{player_name}** is already registered to another user in this season.")
    elif result == -6:
        await interaction.followup.send(f"The user with Discord ID `{discord_id}` is already registered as another player in this season.")
    else:
        await interaction.followup.send("An unknown error occurred while trying to add the player.")

async def setupserver(interaction: discord.Interaction):
    # Categories
    # Base Roles
    # Players Roles
    # Tribe Roles
    # All

    embed = discord.Embed(
        title="Configure Server"
    )

    embed.add_field(name="Server Categories", value="Create and arrange the server categories.", inline=False)
    embed.add_field(name="(Future) Base Roles", value="Create and arrange the base roles (excluding host).", inline=False)
    embed.add_field(name="Player Roles", value="Create and arrange the player roles.", inline=False)
    embed.add_field(name="Tribe Roles", value="Create and arrange the tribe roles.", inline=False)

    view = SetupServerButtons()

    await interaction.response.send_message(embed=embed, view=view)

@app_commands.autocomplete(player_name=autocomplete_players)
async def setupplayer(interaction: discord.Interaction, player_name: str):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    
    player = get_first(queries.get_player(server_id=guild.id, display_name=player_name))

    if not player:
        await interaction.response.send_message(f"{player_name} not found on this season.")
        return
    
    embed = await get_player_embed(guild=guild, player=player)
    view = PlayerSetupButtons(player=player)

    await interaction.response.send_message(embed=embed, view=view)

async def setupallplayers(interaction:discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    
    players = queries.get_player(server_id=guild.id)
    await interaction.response.send_message("Setting up all players...", ephemeral=True)

    for player in players:
        embed = await get_player_embed(guild=guild, player=player)
        view = PlayerSetupButtons(player=player)
        await interaction.followup.send(embed=embed, view=view)

@app_commands.autocomplete(tribe_string=autocomplete_tribes)
async def setuptribe(interaction: discord.Interaction, tribe_string: str):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    tribe_name, iteration = parse_tribe_string(tribe_string)
    tribe = get_first(queries.get_tribe(server_id=guild.id, tribe_name=tribe_name, tribe_iteration=iteration))

    if not tribe:
        await interaction.response.send_message("No matching tribe found.", ephemeral=True)
        return
    
    embed = await get_tribe_embed(guild=guild, tribe=tribe)
    view = TribeSetupButtons(tribe=tribe)

    await interaction.response.send_message(embed=embed, view=view)

async def setupalltribes(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    tribes = queries.get_tribe(server_id=guild.id)
    await interaction.response.send_message("Setting up all tribes...", ephemeral=True)

    for tribe in tribes:
        embed = await get_tribe_embed(guild=guild, tribe=tribe)
        view = TribeSetupButtons(tribe=tribe)
        await interaction.followup.send(embed=embed, view=view)


