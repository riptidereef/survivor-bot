import discord
from discord import app_commands
from utils.helpers import *
import re
from interfaces.interfaces import *

async def deleteallchannels(interaction: discord.Interaction):
    guild = interaction.guild
    await interaction.response.defer()
    for channel in guild.channels:
        await channel.delete()

async def clearallroles(interaction: discord.Interaction):
    guild = interaction.guild
    bot_member = guild.me
    host_role = discord.utils.get(guild.roles, name="Host")

    await interaction.response.defer()

    if host_role is None:
        await interaction.response.send_message("Host role not found.", ephemeral=True)
        return

    for member in guild.members:
        if member == bot_member:
            continue
        if host_role in member.roles or any(r > host_role for r in member.roles):
            continue

        roles_to_remove = [r for r in member.roles if r != guild.default_role]
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason="Clearing all roles")
            except discord.Forbidden:
                print(f"Missing permissions to edit {member}.")
            except Exception as e:
                print(f"Error removing roles from {member}: {e}")

    await interaction.followup.send("All roles cleared (except Host and the bot).")

async def deleteroles(interaction: discord.Interaction):
    EXEMPT_ROLES = {
        'Host',
        'Survivor Bot',
        'Immunity',
        'Castaway',
        'Trusted Viewer',
        'Viewer',
        'Jury',
        'Pre-Jury',
        'Sequester'
    }
    await interaction.response.defer()
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
    bot_member = guild.me
    deleted_roles = []
    for role in guild.roles:
        if role.name in EXEMPT_ROLES or role.is_default():
            continue
        if role >= bot_member.top_role:
            print(f"Cannot delete role {role.name} (higher than bot's role)")
            continue
        try:
            await role.delete(reason="Deleting all non-exempt roles")
            deleted_roles.append(role.name)
        except discord.Forbidden:
            print(f"Missing permissions to delete role: {role.name}")
        except Exception as e:
            print(f"Error deleting role {role.name}: {e}")

    await interaction.followup.send("Done", ephemeral=True)

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

    if iteration == 1:
        tribe_string = tribe_name
    else:
        tribe_string = f"{tribe_name} {iteration}.0"

    embed = discord.Embed(
        title=f"Preview: {tribe_string}",
        color=discord.Color(int(color, 16))
    )
    embed.add_field(name="Color", value=color, inline=False)
    embed.add_field(name="Order ID:", value=order_id, inline=False)

    view = VerifyTribeCreateView(tribe_name=tribe_name, iteration=iteration, color=color, order_id=order_id)

    await interaction.followup.send(embed=embed, view=view)

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
    embed.add_field(name="Confessional Categories", value="Arrange the confessional categories for all tribes.", inline=False)
    embed.add_field(name="Submissions Categories", value="Arrange the submissions categories for all tribes.", inline=False)
    embed.add_field(name="1-1's Categories", value="Arrange the 1-1's categories for all tribes.", inline=False)
    embed.add_field(name="Player Roles", value="Create and arrange the player roles.", inline=False)
    embed.add_field(name="Tribe Roles", value="Create and arrange the tribe roles.", inline=False)

    view = ServerSetupButtons()

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

async def setupseason(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Season Actions"
    )
    embed.add_field(name="Tribe Swap", value="Perform a tribe swap for a variable number of tribes.")

    view = SeasonSetupButtons()

    await interaction.response.send_message(embed=embed, view=view)
