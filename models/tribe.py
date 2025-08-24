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

    def __repr__(self):
        return f"{self.get_tribe_string()}"
    
    def get_tribe_string(self):
        if self.iteration == 1:
            return self.tribe_name
        else:
            return f"{self.tribe_name} {self.iteration}.0"
        