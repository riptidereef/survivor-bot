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




