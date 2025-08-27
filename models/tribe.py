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
