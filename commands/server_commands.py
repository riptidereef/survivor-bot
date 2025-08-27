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
    async def test(self,
                   interaction: discord.Interaction,
                   display_name: str = None, 
                   player_id: int = None, 
                   player_discord_id: str = None, 
                   user_id: int = None,
                   new_display_name: str = None,
                   new_tribe_id: int = None,
                   new_tribe_name: str = None,
                   new_tribe_iteration: int = None):
        
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command must be run in a server.", ephemeral=True
            )
            return

        # Call edit_player with all optional parameters

        if player_discord_id is None:
            discord_id = None
        else:
            discord_id = int(player_discord_id)

        success = queries.edit_player(
            server_id=guild.id,
            display_name=display_name,
            player_id=player_id,
            player_discord_id=discord_id,
            user_id=user_id,
            new_display_name=new_display_name,
            new_tribe_id=new_tribe_id,
            new_tribe_name=new_tribe_name,
            new_tribe_iteration=new_tribe_iteration
        )

        # Send a response depending on the result
        if success:
            await interaction.response.send_message(
                "Player updated successfully.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to update player. Check the provided parameters.", ephemeral=True
            )

    @app_commands.command(name="test2", description="Test out the edit_tribe function in the code.")
    async def test2(self,
                    interaction: discord.Interaction,
                    tribe_name: str = None,
                    tribe_iteration: int = 1,
                    tribe_id: int = None,
                    new_tribe_name: str = None,
                    new_tribe_iteration: int = None,
                    new_color: str = None,
                    new_order_id: int = None):
        
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command must be run in a server.", ephemeral=True
            )
            return

        success = queries.edit_tribe(
            server_id=guild.id,
            tribe_name=tribe_name,
            tribe_iteration=tribe_iteration,
            tribe_id=tribe_id,
            new_tribe_name=new_tribe_name,
            new_tribe_iteration=new_tribe_iteration,
            new_color=new_color,
            new_order_id=new_order_id
        )

        if success:
            await interaction.response.send_message(
                "Tribe updated successfully.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to update tribe. Check the provided parameters.", ephemeral=True
            )

    @app_commands.command(name="deleteplayer", description="Test out the delete_player function in the code.")
    async def delete_player(self, 
                            interaction: discord.Interaction, 
                            display_name: str | None = None, 
                            player_id: int | None = None,
                            player_discord_id: str | None = None,
                            user_id: int | None = None):
        
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command must be run in a server.", ephemeral=True
            )
            return

        if player_discord_id is None:
            discord_id = None
        else:
            discord_id = int(player_discord_id)

        success = queries.delete_player(
            server_id=guild.id,
            display_name=display_name,
            player_id=player_id,
            player_discord_id=discord_id,
            user_id=user_id,
        )

        if success:
            await interaction.response.send_message(
                "Player deleted successfully.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to delete player. Check the provided parameters.", ephemeral=True
            )

    @app_commands.command(name="deleteseason", description="Test out the delete_season function in the code.")
    async def deleteseason(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command must be run in a server.", ephemeral=True
            )
            return
        
        success = queries.delete_season(server_id=guild.id)

        if success:
            await interaction.response.send_message(
                "Season deleted successfully.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to delete season. Check the provided parameters.", ephemeral=True
            )

    @app_commands.command(name="deletetribe", description="Test out the delete_tribe function in the code.")
    async def deletetribe(self,
                        interaction: discord.Interaction,
                        tribe_name: str = None,
                        tribe_iteration: int = 1,
                        tribe_id: int = None):
        
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command must be run in a server.", ephemeral=True
            )
            return

        success = queries.delete_tribe(
            server_id=guild.id,
            tribe_name=tribe_name,
            tribe_iteration=tribe_iteration,
            tribe_id=tribe_id
        )

        if success:
            await interaction.response.send_message(
                "Tribe deleted successfully.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to delete tribe. Check the provided parameters.", ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerCommands(bot))