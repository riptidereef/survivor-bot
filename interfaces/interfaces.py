import discord
from discord.ui import View, Button, Select, Modal, TextInput
from models.player import Player
from models.tribe import Tribe
from database import queries
from utils.helpers import *

async def get_player_embed(guild: discord.Guild, player: Player) -> discord.Embed:
    player_tribe = get_first(queries.get_tribe(server_id=guild.id, player_display_name=player.display_name))

    user_id = player.get_discord_id()
    user = guild.get_member(user_id)
    if user is None:
        try:
            user = await guild.fetch_member(user_id)
        except discord.NotFound:
            user = None

    if player_tribe is not None:
        tribe_color = discord.Color(int(player_tribe.color, 16))
    else:
        tribe_color = discord.Color.light_gray()

    embed = discord.Embed(
        title=player.display_name,
        color=tribe_color
    )

    if user is not None:
        embed.add_field(
            name="Discord User",
            value=f"{user.mention}",
            inline=False
        )
        embed.set_thumbnail(url=user.display_avatar.url)
    else:
        embed.add_field(
            name="Discord User",
            value=f"<@{user_id}>",
            inline=False
        )

    if player_tribe is not None:
        embed.add_field(
            name="Tribe",
            value=f"{player_tribe.tribe_string}",
            inline=True
        )
    else:
        embed.add_field(
            name="Tribe",
            value="Not assigned",
            inline=True
        )

    embed.set_footer(
        text=f"Player ID: {player.player_id} | User ID: {player.user_id} | Season ID: {player.season_id}"
    )

    return embed

async def get_tribe_embed(guild: discord.Guild, tribe: Tribe) -> discord.Embed:
    tribe_players = queries.get_player(server_id=guild.id, tribe_id=tribe.tribe_id)

    embed = discord.Embed(
        title=tribe.tribe_string,
        color=discord.Color(int(tribe.color, 16))
    )

    if not tribe_players:
        embed.add_field(name="No Members", value="This tribe is currently empty.", inline=False)
        return embed

    for player in tribe_players:
        embed.add_field(name=player.display_name, value=f"<@{player.get_discord_id()}>", inline=False)

    embed.set_footer(text=f"Tribe ID: {tribe.tribe_id} | Season ID: {tribe.season_id}")

    return embed



class PlayerSetupButtons(View):
    def __init__(self, player: Player):
        super().__init__(timeout=None)
        self.player = player

    @discord.ui.button(label="Submissions", style=discord.ButtonStyle.blurple)
    async def player_submissions_callback(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="Submissions")
        if category is None:
            await interaction.response.send_message("Submissions category not found. Please use `/setupserver` first.", ephemeral=True)
            return
        
        channel_name = f"{self.player.display_name.strip().lower().replace(' ', '-')}-submissions"
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is not None:
            await channel.delete()
            await interaction.response.send_message(
                f"Deleted channel {channel_name}.", ephemeral=True
            )
        else:
            new_channel = await guild.create_text_channel(name=channel_name, category=category)
            await interaction.response.send_message(
                f"Created chat {new_channel.mention}.", ephemeral=True
            )

    @discord.ui.button(label="Confessional", style=discord.ButtonStyle.blurple)
    async def player_confessionals_callback(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="Confessionals")
        if category is None:
            await interaction.response.send_message("Confessionals category not found. Please use `/setupserver` first.", ephemeral=True)
            return
        
        channel_name = f"{self.player.display_name.strip().lower().replace(' ', '-')}-confessionals"
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is not None:
            await channel.delete()
            await interaction.response.send_message(
                f"Deleted channel {channel_name}.", ephemeral=True
            )
        else:
            new_channel = await guild.create_text_channel(name=channel_name, category=category)
            await interaction.response.send_message(
                f"Created chat {new_channel.mention}.", ephemeral=True
            )

    @discord.ui.button(label="Reveal Player", style=discord.ButtonStyle.green)
    async def player_reveal_callback(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild

        player_tribe = get_first(queries.get_tribe(server_id=guild.id, player_display_name=self.player.display_name))

        viewer_role = discord.utils.get(guild.roles, name="Viewer")
        trusted_viewer_role = discord.utils.get(guild.roles, name="Trusted Viewer")
        castaway_role = discord.utils.get(guild.roles, name="Castaway")
        player_role = discord.utils.get(guild.roles, name=self.player.display_name)
        tribe_role = discord.utils.get(guild.roles, name=player_tribe.tribe_string)

        user = await guild.fetch_member(self.player.get_discord_id())

        if user is None:
            return
        else:
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

            await interaction.response.send_message(f"Successfully revealed player **{self.player.display_name}**.")

class SetupServerButtons(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Server Categories", style=discord.ButtonStyle.blurple)
    async def setupcategories(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return
    
        await interaction.response.defer()
        await arrange_categories(guild)
        await interaction.followup.send("Done.")

    @discord.ui.button(label="Confessional Categories", style=discord.ButtonStyle.blurple)
    async def setupconfessionalcategories(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        await interaction.response.defer()
        await arrange_tribe_confessionals(guild)
        await interaction.followup.send("Done.")

    @discord.ui.button(label="Submissions Categories", style=discord.ButtonStyle.blurple)
    async def setupsubmissionscategories(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        await interaction.response.defer()
        await arrange_tribe_submissions(guild)
        await interaction.followup.send("Done.")

    @discord.ui.button(label="1-1's Categories", style=discord.ButtonStyle.blurple)
    async def setup1_1scategories(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        await interaction.response.defer()
        await interaction.followup.send("Done.")

    @discord.ui.button(label="(Future) Base Roles", style=discord.ButtonStyle.blurple)
    async def setupplayerroles(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return
        await interaction.response.send_message("Setting up base roles.")

    @discord.ui.button(label="Player Roles", style=discord.ButtonStyle.blurple)
    async def setupplayerroles(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return
        
        await interaction.response.defer()
        await arrange_player_roles(guild)
        await interaction.followup.send("Done.")

    @discord.ui.button(label="Tribe Roles", style=discord.ButtonStyle.blurple)
    async def setuptriberoles(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        await interaction.response.defer()
        await arrange_tribe_roles(guild)
        await interaction.followup.send("Done.")

class TribeSetupButtons(View):
    def __init__(self, tribe: Tribe):
        super().__init__(timeout=None)
        self.tribe = tribe

    @discord.ui.button(label="Tribe Chat", style=discord.ButtonStyle.blurple)
    async def setuptribechat(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tribes")
        if category is None:
            await interaction.response.send_message("Tribes category not found. Please use /setupcategories first.", ephemeral=True)
            return
        
        if self.tribe.iteration == 1:
            channel_name = f"{self.tribe.tribe_name.strip().lower()}-camp"
        else:
            channel_name = f"{self.tribe.tribe_name.strip().lower()}-{self.tribe.iteration}-camp"

        channel = discord.utils.get(category.channels, name=channel_name)
        if channel is not None:
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

    @discord.ui.button(label="Tribe VC", style=discord.ButtonStyle.blurple)
    async def setuptribevc(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tribes")
        if category is None:
            await interaction.response.send_message("Tribes category not found. Please use /setupcategories first.", ephemeral=True)
            return
        
        channel_name = f"{self.tribe.tribe_string} VC"
        channel = discord.utils.get(category.voice_channels, name=channel_name)
        if channel is not None:
            await channel.delete()
            await interaction.response.send_message(
                f"Deleted channel {channel_name}.", ephemeral=True
            )
        else:
            print("Creating new voice channel.")
            new_channel = await guild.create_voice_channel(name=channel_name, category=category)
            await interaction.response.send_message(
                f"Created tribe voice chat {new_channel.mention}.", ephemeral=True
            )

    @discord.ui.button(label="Submissions", style=discord.ButtonStyle.blurple)
    async def setuptribesubmissions(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild

        category_name = f"{self.tribe.tribe_string} Submissions"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(name=category_name)
        
        tribe_players = queries.get_player(server_id=guild.id, tribe_id=self.tribe.tribe_id)
        for player in tribe_players:
            channel_name = f"{player.display_name.strip().lower().replace(' ', '-')}-submissions"
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if not channel:
                channel = await guild.create_text_channel(name=channel_name, category=category)
            else:
                if channel.category is not category:
                    await channel.edit(category=category)

        await interaction.response.send_message("Done")

    @discord.ui.button(label="Confessionals", style=discord.ButtonStyle.blurple)
    async def setuptribeconfessionals(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild

        category_name = f"{self.tribe.tribe_string} Confessionals"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(name=category_name)
        
        tribe_players = queries.get_player(server_id=guild.id, tribe_id=self.tribe.tribe_id)
        for player in tribe_players:
            channel_name = f"{player.display_name.strip().lower().replace(' ', '-')}-confessionals"
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if not channel:
                channel = await guild.create_text_channel(name=channel_name, category=category)
            else:
                if channel.category is not category:
                    await channel.edit(category=category)

        await interaction.response.send_message("Done")

    @discord.ui.button(label="1-1's", style=discord.ButtonStyle.blurple)
    async def setuptribe1_1s(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("1-1's")

    @discord.ui.button(label="Arrange Categories", style=discord.ButtonStyle.blurple)
    async def arrangetribecategories(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Arrange Categories")

    @discord.ui.button(label="Reveal Tribe", style=discord.ButtonStyle.green)
    async def arrangetribecategories(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Reveal Tribe")