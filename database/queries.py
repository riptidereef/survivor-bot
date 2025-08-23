from .connection import get_connection, logger

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

def add_player(display_name: str, discord_id: int, server_id: int, tribe_name: str = None, tribe_iter: int = 1) -> int:

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
            return -2
        user_id = result[0]

        # Server check
        command = 'SELECT id FROM seasons WHERE server_id = ?'
        c.execute(command, (server_id,))
        result = c.fetchone()
        if result is None:
            logger.warning(f"Season with server_id {server_id} not found.")
            return -3
        season_id = result[0]

        # Tribe check
        tribe_id = None
        if tribe_name is not None:
            command = 'SELECT id FROM tribes WHERE tribe_name = ? AND iteration = ? AND season_id = ?'
            c.execute(command, (tribe_name, tribe_iter, season_id))
            result = c.fetchone()
            if result is None:
                logger.warning(f"Tribe {tribe_name} (iteration {tribe_iter}) not found in season {season_id}.")
                return -4
        
            tribe_id = result[0]

        # Duplicate display name in the same season check
        c.execute("SELECT 1 FROM players WHERE display_name = ? AND season_id = ?", (display_name, season_id))
        result = c.fetchone()
        if result is not None:
            logger.info(f"Display name '{display_name}' already exists in season {season_id}.")
            return -5

        # Duplicate user_id in the same season check
        c.execute("SELECT 1 FROM players WHERE user_id = ? AND season_id = ?", (user_id, season_id))
        result = c.fetchone()
        if result is not None:
            logger.info(f"User {user_id} already registered as a player in season {season_id}.")
            return -6

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
        return 1

    except Exception as e:
        logger.error(f"Error adding player: {e}")
        return -1
    
    finally:
        conn.close()


