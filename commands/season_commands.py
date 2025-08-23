import discord
from discord.ext import commands
from discord import app_commands
from database import queries
import re
from utils.helpers import get_tribe_string

class SeasonCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="registerseason", description="Register a server as a new season.")
    async def registerseason(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be run in a server.", ephemeral=True)
            return
    
        guild_id = guild.id
        guild_name = guild.name

        result = queries.add_season(guild_id, guild_name)

        if result == 1:
            await interaction.response.send_message(f"Season registered for **{guild_name}**!")
        elif result == 0:
            await interaction.response.send_message(f"**{guild_name}** is already registered.")
        else:
            await interaction.response.send_message(f"Failed to register season.")

    @app_commands.command(name="addtribe", description="Add a new tribe to the current season.")
    @app_commands.describe(
        tribe_name="The name of the tribe.", 
        iteration="The iteration of the tribe (i.e. for swaps, default 1).", 
        color="Hex color code for the tribe (e.g. ff0000).",
        order_id="The precedence in which the tribe occurs (i.e. starting tribe, swapped, merge, etc)."
    )
    async def addtribe(self, interaction: discord.Interaction, tribe_name: str, iteration: int = 1, color: str = 'd3d3d3', order_id: int = 1):
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
        tribe_string = get_tribe_string(tribe_name, iteration)

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

    @app_commands.command(name="addplayer", description="Add a new player to the current season.")
    @app_commands.describe(
        player_name="The name of the player to be added.", 
        discord_user="The Discord account of the player to be added.",
        tribe_name="Optional tribe to assign the player to.",
        tribe_iteration="Optional season iteration (default is 1)."
    )
    async def addplayer(self, interaction: discord.Interaction, player_name: str, discord_user: discord.Member, tribe_name: str = None, tribe_iteration: int = 1):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return
    
        discord_id = discord_user.id
        server_id = interaction.guild.id

        await interaction.response.defer()
    
        result = queries.add_player(player_name, discord_id, server_id, tribe_name, tribe_iteration)

        if result == 1:
            await interaction.followup.send(f"**{player_name}** has been added to the current season.")
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



async def setup(bot: commands.Bot):
    await bot.add_cog(SeasonCommands(bot))