import discord

class Tribe():
    def __init__(
            self,
            tribe_id: int | None,
            tribe_name: str,
            iteration: int,
            season_id: int,
            color: str,
            order_id: int
    ):
        self.tribe_id = tribe_id
        self.tribe_name = tribe_name
        self.iteration = iteration
        self.season_id = season_id
        self.color = color
        self.order_id = order_id

        if self.iteration == 1:
            self.tribe_string = self.tribe_name
        else:
            self.tribe_string = f"{self.tribe_name} {self.iteration}.0"

    def __repr__(self):
        return f"{self.tribe_string}"
    
    def __eq__(self, other):
        if not isinstance(other, Tribe):
            return NotImplemented
        return (
            self.tribe_id == other.tribe_id
            and self.tribe_name == other.tribe_name
            and self.iteration == other.iteration
            and self.season_id == other.season_id
            and self.color == other.color
            and self.order_id == other.order_id
        )
    
    def __hash__(self):
        return hash(self.tribe_id)
    
    def mention(self, guild: discord.Guild):
        tribe_role = discord.utils.get(guild.roles, name=self.tribe_string)
        if tribe_role:
            return tribe_role.mention
        else:
            return ""
