import sqlite3
import logging

logger = logging.getLogger("database_logger")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("database.log")
formatter = logging.Formatter(
    fmt='[%(asctime)s] [%(levelname)-8s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_connection():
    conn = sqlite3.connect('sharkvivor.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def setup_tables():
    conn = get_connection()
    c = conn.cursor()

    # Set up users table
    try:
        command = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INT UNIQUE NOT NULL,
                username TEXT
            );
        '''
        c.execute(command)
        logger.info("User table setup completed.")
    except Exception as e:
        logger.error(f"Error setting up users table: {e}")

    # Set up seasons table
    try:
        command = '''
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INT UNIQUE NOT NULL,
                season_name TEXT NOT NULL
            );
        '''
        c.execute(command)
        logger.info("Seasons table setup completed.")
    except Exception as e:
        logger.error(f"Error setting up seasons table: {e}")

    # Set up tribes table
    try:
        command = '''
            CREATE TABLE IF NOT EXISTS tribes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                iteration INTEGER DEFAULT 1,
                season INTEGER NOT NULL,
                color TEXT NOT NULL DEFAULT 'd3d3d3',
                order_id INT NOT NULL DEFAULT 1,
                FOREIGN KEY(season) REFERENCES seasons(id),
                UNIQUE(name, iteration, season)
            );
        '''
        c.execute(command)
        logger.info("Tribes table setup completed.")
    except Exception as e:
        logger.error(f"Error setting up tribes table: {e}")

    # Set up players table
    try:
        command = '''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                user INTEGER NOT NULL,
                season INTEGER NOT NULL,
                tribe INTEGER DEFAULT NULL,
                FOREIGN KEY (user) REFERENCES users(id),
                FOREIGN KEY (season) REFERENCES seasons(id),
                FOREIGN KEY (tribe) REFERENCES tribes(id),
                UNIQUE (user, season),
                UNIQUE (display_name, season)
            );
        '''
        c.execute(command)
        logger.info("Seasons table setup completed.")
    except Exception as e:
        logger.error(f"Error setting up seasons table: {e}")

def add_user(discord_id: int, username: str) -> bool:
    conn = get_connection()
    c = conn.cursor()

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
    conn.close()
    return success

def add_season(server_id: int, server_name: str) -> int:
    conn = get_connection()
    c = conn.cursor()

    try:
        command = '''
            INSERT INTO seasons (server_id, season_name)
            VALUES (?, ?)
            ON CONFLICT(server_id)
            DO UPDATE SET season_name = excluded.season_name
            WHERE seasons.season_name IS NOT excluded.season_name;
        '''
        c.execute(command, (server_id, server_name))

        conn.commit()
        conn.close()

        if c.rowcount == 0:
            return 0
        else:
            return 1
    
    except Exception as e:
        logger.error(f"Error adding season: {e}")
        return -1

def add_tribe(tribe_name: str, server_id: int, iteration: int = 1, color: str = '#d3d3d3', order_id: int = 1) -> int:
    conn = get_connection()
    c = conn.cursor()

    try:
        command = 'SELECT id FROM seasons WHERE server_id = ?'
        c.execute(command, (server_id,))
        season_row = c.fetchone()

        if season_row is None:
            logger.error(f"Season with ID: {server_id} not found.")
            conn.close()
            return -1
    
        season_id = season_row['id']

        command = '''
            INSERT INTO tribes (name, iteration, season, color, order_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name, iteration, season) DO NOTHING
        '''
        c.execute(command, (tribe_name, iteration, season_id, color, order_id))
        conn.commit()
        conn.close()

        if c.rowcount == 0:
            return 0
        else:
            return 1
    
    except Exception as e:
        logger.error(f"Error adding tribe: {e}")
        conn.close()
        return -1

def add_player(display_name: str, discord_id: int, server_id: int, tribe_name: str = None, tribe_iter: int = 1) -> int:
    conn = get_connection()
    c = conn.cursor()

    try:
        # Find the target user (must already be added)
        command = 'SELECT id FROM users WHERE discord_id = ?'
        c.execute(command, (discord_id,))
        result = c.fetchone()
        if result is None:
            logger.warning(f"User with discord_id {discord_id} not found.")
            conn.close()
            return -1
        user_id = result[0]

        # Find target server
        command = 'SELECT id FROM seasons WHERE server_id = ?'
        c.execute(command, (server_id,))
        result = c.fetchone()
        if result is None:
            logger.warning(f"Season with server_id {server_id} not found.")
            conn.close()
            return -2
        season_id = result[0]

        # Find target tribe (if provided, otherwise NULL)
        tribe_id = None
        if tribe_name is not None:
            command = 'SELECT id FROM tribes WHERE name = ? AND iteration = ? AND season = ?'
            c.execute(command, (tribe_name, tribe_iter, season_id))
            result = c.fetchone()
            if result is None:
                logger.warning(f"Tribe {tribe_name} (iteration {tribe_iter}) not found in season {season_id}.")
                conn.close()
                return -3
        
            tribe_id = result[0]

        command = '''
            INSERT OR IGNORE INTO players (display_name, user, season, tribe)
            VALUES (?, ?, ?, ?);
        '''
        c.execute(command, (display_name, user_id, season_id, tribe_id))
        conn.commit()

        if c.rowcount == 0:
            logger.info(f"User: {user_id} name: {display_name} already exists in season {season_id}.")
            conn.close()
            return 0
        
        logger.info(f"User {user_id} added to season {season_id} with tribe {tribe_id}.")
        conn.close()
        return 1

    except Exception as e:
        logger.error(f"Error adding player: {e}")
        conn.close()
        return -99

def get_tribes(server_id: int, ascending: bool = False) -> list[dict]:
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute('SELECT id FROM seasons WHERE server_id = ?', (server_id,))
        season_row = c.fetchone()

        if season_row is None:
            logger.warning(f"No season found for server_id {server_id}")
            return []
        
        season_id = season_row['id']

        if not ascending:
            command = '''
                SELECT id, name, iteration, color, order_id
                FROM tribes
                WHERE season = ?
                ORDER BY order_id DESC, name ASC, iteration ASC; 
            '''
        else:
            command = '''
                SELECT id, name, iteration, color, order_id
                FROM tribes
                WHERE season = ?
                ORDER BY order_id ASC, name ASC, iteration ASC; 
            '''
        c.execute(command, (season_id,))

        tribes = [dict(row) for row in c.fetchall()]
        return tribes
    
    
    except Exception as e:
        logger.error(f"Error fetching tribes for server {server_id}: {e}")
        return []
    
    finally:
        conn.close()

def get_players(server_id: int) -> list[dict]:
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
        season_row = c.fetchone()

        if season_row is None:
            logger.warning(f"No season found for server_id {server_id}")
            return []
        
        season_id = season_row['id']

        command = '''
            SELECT p.id, 
                   p.display_name, 
                   u.discord_id, 
                   u.username, 
                   t.name as tribe_name,
                   t.iteration as tribe_iteration
            FROM players p
            JOIN users u ON p.user = u.id
            LEFT JOIN tribes t ON p.tribe = t.id
            WHERE p.season = ?
            ORDER BY p.display_name ASC, p.user ASC
        '''
        c.execute(command, (season_id,))

        players = [dict(row) for row in c.fetchall()]
        return players

    except Exception as e:
        logger.error(f"Error fetching players for server {server_id}: {e}")
        return []

    finally:
        conn.close()

def get_player_names(server_id: int) -> list[str]:
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
        season_row = c.fetchone()

        if season_row is None:
            logger.warning(f"No season found for server_id {server_id}")
            return []
        
        season_id = season_row['id']

        c.execute('SELECT display_name FROM players WHERE season = ?', (season_id,))
        result = c.fetchall()

        return [row["display_name"] for row in result]

    except Exception as e:
        logger.error(f"Error fetching player names for server_id {server_id}: {e}")
        return []

    finally:
        conn.close()

def get_tribe_names(server_id: int) -> list[str]:
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
        season_row = c.fetchone()

        if season_row is None:
            logger.warning(f"No season found for server_id {server_id}")
            return []
        
        season_id = season_row['id']

        c.execute('SELECT name FROM tribes WHERE season = ?', (season_id,))
        result = c.fetchall()

        return [row["name"] for row in result]

    except Exception as e:
        logger.error(f"Error fetching tribe names for server_id {server_id}: {e}")
        return []

    finally:
        conn.close()

def get_player_tribe(server_id: int, name: str) -> dict:
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
        season_row = c.fetchone()
        if season_row is None:
            logger.warning(f"No season found for server_id {server_id}")
            return None
        season_id = season_row['id']
        
        command = '''
            SELECT t.id, t.name, t.iteration, t.color, t.order_id
            FROM players p
            LEFT JOIN tribes t ON p.tribe = t.id
            WHERE p.season = ? AND p.display_name = ?
        '''
        c.execute(command, (season_id, name))
        tribe_row = c.fetchone()

        if tribe_row is None:
            logger.info(f"Player {name} is not currently in a tribe for season {season_id}")
            return None

        return dict(tribe_row)

    except Exception as e:
        logger.error(f"Error fetching player tribe: {e}")
        return None

    finally:
        conn.close()

def get_tribe_order(server_id: int) -> list[str]:
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM seasons WHERE server_id = ?", (server_id,))
        season_row = c.fetchone()
        if season_row is None:
            logger.warning(f"No season found for server_id {server_id}")
            return None
        season_id = season_row['id']
        
        command = '''
            SELECT name, iteration FROM tribes WHERE season = ?
            ORDER BY order_id ASC, name ASC;
        '''
        c.execute(command, (season_id,))
        tribes = [dict(row) for row in c.fetchall()]

        tribe_names = []
        for tribe in tribes:
            name = tribe["name"]
            iteration = tribe["iteration"]
            if iteration == 1:
                tribe_names.append(name)
            else:
                tribe_names.append(f"{name} {iteration}.0")

        return tribe_names

    except Exception as e:
        logger.error(f"Error fetching player tribe: {e}")
        return None

    finally:
        conn.close()