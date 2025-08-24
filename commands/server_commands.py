import discord
from discord.ext import commands
from discord import app_commands
from database import queries

class ServerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hello", description="Say hello to the bot.")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

    @app_commands.command(name="test", description="Test out a certain function in the code.")
    async def test(self, interaction: discord.Interaction):
        print(queries.get_player(server_id=interaction.guild.id, tribe_id=1))
        await interaction.response.send_message("Done.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerCommands(bot))