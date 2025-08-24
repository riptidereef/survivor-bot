class Player():
    def __init__(
            self,
            player_id: int | None,
            display_name: str,
            user_id: int,
            season_id: int,
            tribe_id: int | None
    ):
        self.player_id = player_id
        self.display_name = display_name
        self.user_id = user_id
        self.season_id = season_id
        self.tribe_id = tribe_id

    def __repr__(self):
        return f"{self.display_name}"
        