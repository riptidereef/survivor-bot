import discord
from discord.ext import commands
from discord import app_commands
import database

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

        result = database.add_season(guild_id, guild_name)

        if result == 1:
            await interaction.response.send_message(f"Season registered for **{guild_name}**!")
        elif result == 0:
            await interaction.response.send_message(f"**{guild_name}** is already registered.")
        else:
            await interaction.response.send_message(f"Failed to register season.")

async def setup(bot: commands.Bot):
    await bot.add_cog(SeasonCommands(bot))