from .connection import get_connection, logger
from player import Player
from tribe import Tribe

def add_user(discord_id: int, username: str) -> bool:
    conn = get_connection()
    c = conn.cursor()

    try:
        command = '''
            INSERT INTO users (discord_id, username)
            VALUES (?, ?)
            ON CONFLICT(discord_id)
            DO UPDATE SET username = excluded.username
            WHERE users.username IS NOT excluded.username;
        '''
        c.execute(command, (discord_id, username))
        success = c.rowcount > 0
        conn.commit()
        return success

    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return False

    finally:
        conn.close()

def add_season(server_id: int, server_name: str) -> int:
    conn = get_connection()
    c = conn.cursor()

    try:
        command = '''
            INSERT INTO seasons (server_id, season_name)
            VALUES (?, ?)
            ON CONFLICT (server_id)
            DO UPDATE SET season_name = excluded.season_name
            WHERE seasons.season_name IS NOT excluded.season_name;
        '''
        c.execute(command, (server_id, server_name))
        conn.commit()

        if c.rowcount == 0:
            return 0
        else:
            return 1

    except Exception as e:
        logger.error(f"Error adding season: {e}")
        return -1

    finally:
        conn.close()

def add_tribe(tribe_name: str, server_id: int, iteration: int = 1, color: str = '#d3d3d3', order_id: int = 1) -> int:
    # 1 = success.
    # 0 = tribe already in database. 
    # -1 = unexpected error. 
    # -2 = tribe's season not registered in the database yet.

    conn = get_connection()
    c = conn.cursor()

    try:
        command = 'SELECT id FROM seasons WHERE server_id = ?'
        c.execute(command, (server_id,))
        season_row = c.fetchone()

        if season_row is None:
            logger.error(f"Season with ID: {server_id} not found.")
            conn.close()
            return -2
    
        season_id = season_row['id']

        command = '''
            INSERT INTO tribes (tribe_name, iteration, season_id, color, order_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(tribe_name, iteration, season_id) DO NOTHING
        '''
        c.execute(command, (tribe_name, iteration, season_id, color, order_id))
        conn.commit()

        if c.rowcount == 0:
            return 0
        else:
            return 1
    
    except Exception as e:
        logger.error(f"Error adding tribe: {e}")
        return -1

    finally:
        conn.close()

def add_player(display_name: str, discord_id: int, server_id: int, tribe_name: str = None, tribe_iter: int = 1) -> tuple[int, Player | None]:

    # 1  = success.
    # 0  = display_name already exists in this season.
    # -1 = unexpected error.
    # -2 = user with provided discord id not found.
    # -3 = season not found.
    # -4 = tribe not found.
    # -5 = display_name already registered as another player in this season.
    # -6 = user_id already registered as another player in this season.

    conn = get_connection()
    c = conn.cursor()

    try:
        # User check
        c.execute("SELECT id FROM users WHERE discord_id = ?", (discord_id,))
        result = c.fetchone()
        if result is None:
            logger.warning(f"User with discord_id {discord_id} not found.")
            return -2, None
        user_id = result[0]

        # Server check
        command = 'SELECT id FROM seasons WHERE server_id = ?'
        c.execute(command, (server_id,))
        result = c.fetchone()
        if result is None:
            logger.warning(f"Season with server_id {server_id} not found.")
            return -3, None
        season_id = result[0]

        # Tribe check
        tribe_id = None
        if tribe_name is not None:
            command = 'SELECT id FROM tribes WHERE tribe_name = ? AND iteration = ? AND season_id = ?'
            c.execute(command, (tribe_name, tribe_iter, season_id))
            result = c.fetchone()
            if result is None:
                logger.warning(f"Tribe {tribe_name} (iteration {tribe_iter}) not found in season {season_id}.")
                return -4, None
        
            tribe_id = result[0]

        # Duplicate display name in the same season check
        c.execute("SELECT 1 FROM players WHERE display_name = ? AND season_id = ?", (display_name, season_id))
        result = c.fetchone()
        if result is not None:
            logger.info(f"Display name '{display_name}' already exists in season {season_id}.")
            return -5, None

        # Duplicate user_id in the same season check
        c.execute("SELECT 1 FROM players WHERE user_id = ? AND season_id = ?", (user_id, season_id))
        result = c.fetchone()
        if result is not None:
            logger.info(f"User {user_id} already registered as a player in season {season_id}.")
            return -6, None

        command = '''
            INSERT OR IGNORE INTO players (display_name, user_id, season_id, tribe_id)
            VALUES (?, ?, ?, ?);
        '''
        c.execute(command, (display_name, user_id, season_id, tribe_id))
        conn.commit()

        if c.rowcount == 0:
            logger.info(f"User: {user_id} name: {display_name} already exists in season {season_id}.")
            return 0
        
        logger.info(f"User {user_id} added to season {season_id} with tribe {tribe_id}.")

        new_player = Player(
            display_name=display_name,
            user_id=user_id,
            season_id=season_id,
            player_id=c.lastrowid,
            tribe_id=tribe_id,
        )

        return 1, new_player

    except Exception as e:
        logger.error(f"Error adding player: {e}")
        return -1, None
    
    finally:
        conn.close()

def get_user_discord_id(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    discord_id = None

    try:
        c.execute("SELECT discord_id FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if row:
            discord_id = row[0]

    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

    finally:
        conn.close()

    return discord_id

def get_player(server_id: int, 
               player_id: int | None = None,
               display_name: str | None = None,
               user_id: int | None = None,
               discord_id: int | None = None,
               season_id: int | None = None,
               tribe_id: int | None = None,
               tribe_name: str | None = None,
               tribe_iteration: int = 1) -> list[Player]:
    
    conn = get_connection()
    c = conn.cursor()

    try:
        if season_id is None:
            c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
            result = c.fetchone()
            if result is None:
                logger.warning(f"Season with server_id {server_id} not found.")
                return []
            season_id = result[0]

        if player_id is not None:
            query = "SELECT * FROM players WHERE season_id = ? AND id = ?"
            params = (season_id, player_id)

        elif display_name is not None:
            query = "SELECT * FROM players WHERE season_id = ? AND display_name = ?"
            params = (season_id, display_name)

        elif user_id is not None:
            query = "SELECT * FROM players WHERE season_id = ? AND user_id = ?"
            params = (season_id, user_id)

        elif discord_id is not None:
            query = '''
                SELECT p.* FROM players p
                JOIN users u ON p.user_id = u.id
                WHERE p.season_id = ? AND u.discord_id = ?
            '''
            params = (season_id, discord_id)

        elif tribe_id is not None:
            query = "SELECT * FROM players WHERE season_id = ? AND tribe_id = ? ORDER BY display_name"
            params = (season_id, tribe_id)

        elif tribe_name is not None:
            query = '''
                SELECT p.* FROM players p
                JOIN tribes t ON p.tribe_id = t.id
                WHERE p.season_id = ? AND t.tribe_name = ? AND t.iteration = ?
                ORDER BY p.display_name
            '''
            params = (season_id, tribe_name, tribe_iteration)

        else:
            query = "SELECT * FROM players WHERE season_id = ? ORDER BY display_name"
            params = (season_id,)
    
        c.execute(query, params)
        rows = c.fetchall()

        players = []
        for row in rows:
            row_dict = dict(row)
            new_player = Player(display_name=row_dict["display_name"],
                                user_id=row_dict["user_id"],
                                season_id=row_dict["season_id"],
                                player_id=row_dict["id"],
                                tribe_id=row_dict["tribe_id"])
            players.append(new_player)

        return players

    except Exception as e:
        logger.error(f"Error retrieving player: {e}")
        return []

    finally:
        conn.close()

def get_tribe(server_id: int, 
              tribe_id: int | None = None,
              tribe_name: str | None = None,
              tribe_iteration: int = 1,
              player_display_name: str | None = None,
              player_id: int | None = None,
              player_discord_id: int | None = None,
              user_id: int | None = None,
              order_id: int | None = None,
              season_id: int | None = None) -> list[Tribe]:
    
    conn = get_connection()
    c = conn.cursor()

    try:
        if season_id is None:
            c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
            result = c.fetchone()
            if result is None:
                logger.warning(f"Season with server_id {server_id} not found.")
                return []
            season_id = result[0]

        if tribe_id is not None:
            query = "SELECT * FROM tribes WHERE season_id = ? AND id = ?"
            params = (season_id, tribe_id)

        elif tribe_name is not None:
            query = "SELECT * FROM tribes WHERE season_id = ? AND tribe_name = ? AND iteration = ?"
            params = (season_id, tribe_name, tribe_iteration)

        elif player_display_name is not None:
            c.execute("SELECT tribe_id FROM players WHERE season_id = ? AND display_name = ?", (season_id, player_display_name))
            result = c.fetchone()
            if result is None:
                logger.warning(f"Player with display_name {player_display_name} not found.")
                return []
            tribe_id = result[0]
            if tribe_id is None:
                logger.warning(f"Player {player_display_name} exists but is not assigned to a tribe.")
                return []
            query = "SELECT * FROM tribes WHERE season_id = ? AND id = ?"
            params = (season_id, tribe_id)

        elif player_id is not None:
            c.execute("SELECT tribe_id FROM players WHERE season_id = ? AND id = ?", (season_id, player_id))
            result = c.fetchone()
            if result is None:
                logger.warning(f"Player with player_id {player_id} not found.")
                return []
            tribe_id = result[0]
            if tribe_id is None:
                logger.warning(f"Player with ID {player_id} exists but is not assigned to a tribe.")
                return []
            query = "SELECT * FROM tribes WHERE season_id = ? AND id = ?"
            params = (season_id, tribe_id)

        elif player_discord_id is not None:
            c.execute("SELECT id FROM users WHERE discord_id = ?", (player_discord_id,))
            result = c.fetchone()
            if result is None:
                logger.warning(f"User with discord_id {player_discord_id} not found in users table.")
                return []
            user_id = result[0]

            c.execute("SELECT tribe_id FROM players WHERE season_id = ? AND user_id = ?", (season_id, user_id))
            result = c.fetchone()
            if result is None:
                logger.warning(f"No player found in season {season_id} for user_id {user_id} (discord_id {player_discord_id}).")
                return []
            tribe_id = result[0]

            if tribe_id is None:
                logger.warning(f"User with discord_id {player_discord_id} (user_id {user_id}) exists in season {season_id} but is not assigned to a tribe.")
                return []

            query = "SELECT * FROM tribes WHERE season_id = ? AND id = ?"
            params = (season_id, tribe_id)
        
        elif user_id is not None:
            c.execute("SELECT tribe_id FROM players WHERE season_id = ? AND user_id = ?", (season_id, user_id))
            result = c.fetchone()
            if result is None:
                logger.warning(f"No player found in season {season_id} for user_id {user_id}.")
                return []
            tribe_id = result[0]

            if tribe_id is None:
                logger.warning(f"User with user_id {user_id} exists in season {season_id} but is not assigned to a tribe.")
                return []

            query = "SELECT * FROM tribes WHERE season_id = ? AND id = ?"
            params = (season_id, tribe_id)
        
        elif order_id is not None:
            query = "SELECT * FROM tribes WHERE season_id = ? AND order_id = ? ORDER BY tribe_name"
            params = (season_id, order_id)

        else:
            query = "SELECT * FROM tribes WHERE season_id = ? ORDER BY order_id DESC, tribe_name, iteration"
            params = (season_id,)

        c.execute(query, params)
        rows = c.fetchall()

        tribes = []
        for row in rows:
            row_dict = dict(row)
            new_tribe = Tribe(tribe_id=row_dict["id"],
                              tribe_name=row_dict["tribe_name"],
                              iteration=row_dict["iteration"],
                              season_id=row_dict["season_id"],
                              color=row_dict["color"],
                              order_id=row_dict["order_id"])
            tribes.append(new_tribe)

        return tribes


    except Exception as e:
        logger.error(f"Error retrieving tribe: {e}")
        return []
    
    finally:
        conn.close()

def edit_player(server_id: int,
                player: Player | None = None,
                display_name: str | None = None,
                player_id: str | None = None,
                player_discord_id: int | None = None,
                user_id: int | None = None,
                new_display_name: str | None = None,
                new_tribe: Tribe | None = None,
                new_tribe_id: int | None = None,
                new_tribe_name: str | None = None,
                new_tribe_iteration: int = 1) -> bool:
    
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
        result = c.fetchone()
        if result is None:
            logger.warning(f"Season with server_id {server_id} not found.")
            return False
        season_id = result[0]

        if player is None:
            if display_name is not None:
                player = next(iter(get_player(server_id=server_id, display_name=display_name)), None)
            elif player_id is not None:
                player = next(iter(get_player(server_id=server_id, player_id=player_id)), None)
            elif player_discord_id is not None:
                player = next(iter(get_player(server_id=server_id, discord_id=player_discord_id)), None)
            elif user_id is not None:
                player = next(iter(get_player(server_id=server_id, user_id=user_id)), None)

        if player is None:
            logger.warning("No player found to edit (invalid ID, name, or discord_id).")
            return False
        
        queries = []
        params_list = []

        if new_display_name is not None:
            c.execute("SELECT 1 FROM players WHERE season_id = ? AND display_name = ?", (season_id, new_display_name))
            if c.fetchone() is not None:
                logger.warning(f"Player with display name {new_display_name} already exists in this season.")
                return False

            queries.append("UPDATE players SET display_name = ? WHERE id = ?")
            params_list.append((new_display_name, player.player_id))

        if new_tribe is None:
            if new_tribe_id is not None:
                new_tribe = next(iter(get_tribe(server_id=server_id, tribe_id=new_tribe_id)), None)
                if new_tribe is None:
                    logger.warning(f"Tribe with id {new_tribe_id} does not exist.")
                    return False
            
            elif new_tribe_name is not None:
                new_tribe = next(iter(get_tribe(server_id=server_id, tribe_name=new_tribe_name, tribe_iteration=new_tribe_iteration)), None)
                if new_tribe is None:
                    logger.warning(f"Tribe with name {new_tribe_name} and iteration {new_tribe_iteration} does not exist.")
                    return False
                
        if new_tribe is not None:
            queries.append("UPDATE players SET tribe_id = ? WHERE id = ?")
            params_list.append((new_tribe.tribe_id, player.player_id))

        c.execute("BEGIN")
        rows_updated = 0
        for query, params in zip(queries, params_list):
            c.execute(query, params)
            rows_updated += c.rowcount
        conn.commit()
        print(f"Queries made: {rows_updated}")
        return rows_updated > 0

    except Exception as e:
        conn.rollback()
        logger.error(f"Error editing player: {e}")
        return False

    finally:
        conn.close()

def edit_tribe(server_id: int,
               tribe: Tribe | None = None,
               tribe_name: str | None = None,
               tribe_iteration: int = 1,
               tribe_id: int | None = None,
               new_tribe_name: str | None = None,
               new_tribe_iteration: int | None = None,
               new_color: str | None = None,
               new_order_id: int | None = None) -> bool:
    
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
        result = c.fetchone()
        if result is None:
            logger.warning(f"Season with server_id {server_id} not found.")
            return False
        season_id = result[0]

        if tribe is None:
            if tribe_name is not None:
                tribe = next(iter(get_tribe(server_id=server_id, tribe_name=tribe_name, tribe_iteration=tribe_iteration)), None)
            elif tribe_id is not None:
                tribe = next(iter(get_tribe(server_id=server_id, tribe_id=tribe_id)), None)

        if tribe is None:
            logger.warning("No tribe found to edit (invalid ID, name, or iteration).")
            return False
        
        print(f"Updating tribe with id {tribe.tribe_id}")

        queries = []
        params_list = []

        # Update iteration + name
        if new_tribe_name is not None and new_tribe_iteration is not None:
            c.execute("SELECT 1 FROM tribes WHERE season_id = ? AND tribe_name = ? AND iteration = ?", (season_id, new_tribe_name, new_tribe_iteration))
            if c.fetchone() is not None:
                logger.warning("Tribe already exists in this season.")
            else:
                queries.append("UPDATE tribes SET tribe_name = ?, iteration = ? WHERE id = ?")
                params_list.append((new_tribe_name, new_tribe_iteration, tribe.tribe_id))

        # Update name only
        elif new_tribe_name is not None:
            c.execute("SELECT 1 FROM tribes WHERE season_id = ? AND tribe_name = ? AND iteration = ?", (season_id, new_tribe_name, tribe.iteration))
            if c.fetchone() is not None:
                logger.warning("Tribe already exists in this season.")
            else:
                queries.append("UPDATE tribes SET tribe_name = ? WHERE id = ?")
                params_list.append((new_tribe_name, tribe.tribe_id))

        # Update iteration only
        elif new_tribe_iteration is not None:
            c.execute("SELECT 1 FROM tribes WHERE season_id = ? AND tribe_name = ? AND iteration = ?", (season_id, tribe.tribe_name, new_tribe_iteration))
            if c.fetchone() is not None:
                logger.warning("Tribe already exists in this season.")
                return False
            else:
                queries.append("UPDATE tribes SET iteration = ? WHERE id = ?")
                params_list.append((new_tribe_iteration, tribe.tribe_id))

        if new_color is not None:
            queries.append("UPDATE tribes SET color = ? WHERE id = ?")
            params_list.append((new_color, tribe.tribe_id))
        if new_order_id is not None:
            queries.append("UPDATE tribes SET order_id = ? WHERE id = ?")
            params_list.append((new_order_id, tribe.tribe_id))
        
        c.execute("BEGIN")
        rows_updated = 0
        for query, params in zip(queries, params_list):
            c.execute(query, params)
            rows_updated += c.rowcount
        conn.commit()
        print(f"Queries made: {rows_updated}")
        return rows_updated > 0

    except Exception as e:
        conn.rollback()
        logger.error(f"Error editing player: {e}")
        return False
    
    finally:
        conn.close()

def delete_season(server_id: int):
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
        result = c.fetchone()
        if result is None:
            logger.warning(f"Season with server_id {server_id} not found.")
            return False
        season_id = result[0]

        c.execute("BEGIN")
        c.execute("DELETE FROM players WHERE season_id = ?", (season_id,))
        c.execute("DELETE FROM tribes WHERE season_id = ?", (season_id,))
        c.execute("DELETE FROM seasons WHERE id = ?", (season_id,))
        conn.commit()
        return True
    
    except Exception as e:
        conn.rollback()
        logger.warning(f"Error deleting season: {e}")
        return False

    finally:
        conn.close()

def delete_player(server_id: int,
                  player: Player | None = None,
                  display_name: str | None = None,
                  player_id: int | None = None,
                  player_discord_id: int | None = None,
                  user_id: int | None = None):
    
    conn = get_connection()
    c = conn.cursor()

    try:
        if player is None:
            player = next(iter(get_player(server_id=server_id,
                                          player_id=player_id,
                                          display_name=display_name,
                                          user_id=user_id,
                                          discord_id=player_discord_id)), None)
        
        if player is None:
            logger.warning("No player found to delete.")
        else:
            c.execute("DELETE FROM players WHERE id = ?", (player.player_id,))
            conn.commit()

        if c.rowcount > 0:
            logger.info(f"Deleted player {player.display_name} (id={player.player_id})")
            return True
        else:
            logger.warning(f"Player {player.display_name} (id={player.player_id}) not found in database.")
            return False

    except Exception as e:
        conn.rollback()
        logger.warning(f"Error deleting player: {e}")
        return False

    finally:
        conn.close()

def delete_tribe(server_id: int,
                 tribe: Tribe | None = None,
                 tribe_name: str | None = None,
                 tribe_iteration: int = 1,
                 tribe_id: int | None = None,):
    
    conn = get_connection()
    c = conn.cursor()

    try:
        if tribe is None:
            tribe = next(iter(get_tribe(server_id=server_id,
                                                  tribe_name=tribe_name,
                                                  tribe_iteration=tribe_iteration,
                                                  tribe_id=tribe_id)), None)
            
        if tribe is None:
            logger.warning("No tribe found to delete.")
            return False

        c.execute("BEGIN")
        c.execute("UPDATE players SET tribe_id = NULL WHERE tribe_id = ?", (tribe.tribe_id,))
        updated_players = c.rowcount

        c.execute("DELETE FROM tribes WHERE id = ?", (tribe.tribe_id,))
        deleted_tribes = c.rowcount
        conn.commit()

        return (updated_players > 0) or (deleted_tribes > 0)

    except Exception as e:
        conn.rollback()
        logger.warning(f"Error deleting tribe: {e}")
        return False

    finally:
        conn.close()