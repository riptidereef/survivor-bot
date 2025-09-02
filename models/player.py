from database import queries
import discord

class Player():
    def __init__(
            self,
            player_id: int,
            display_name: str,
            user_id: int,
            season_id: int,
            tribe_id: int
    ):
        self.player_id = player_id
        self.display_name = display_name
        self.user_id = user_id
        self.season_id = season_id
        self.tribe_id = tribe_id

    def __repr__(self):
        return f"{self.display_name}"
    
    def get_discord_id(self):
        return queries.get_user_discord_id(self.user_id)
    
    def mention(self, guild: discord.Guild):
        player_role = discord.utils.get(guild.roles, name=self.display_name)
        if player_role:
            return player_role.mention
        else:
            return ""
    
    async def get_discord_user(self, guild: discord.Guild) -> discord.Member:
        discord_id = self.get_discord_id()
        try:
            member = await guild.fetch_member(discord_id)
            return member
        except discord.NotFound:
            return None
        