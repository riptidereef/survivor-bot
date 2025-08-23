def get_tribe_string(tribe_name: str, iteration: int):
    if iteration == 1:
        return tribe_name
    else:
        return f"{tribe_name} {iteration}.0"