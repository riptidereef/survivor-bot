import discord
from discord.ext import commands
from discord import app_commands

class ServerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hello", description="Say hello to the bot.")
    async def hello(self, interaction: discord.Interaction):
        await interaction.followup.send("Hello!")

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerCommands(bot))