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

def log_update(cursor, positive_msg, negative_msg):
    if cursor.rowcount > 0:
        logger.debug(positive_msg)
    else:
        logger.debug(negative_msg)

def get_connection():
    conn = sqlite3.connect('sharkvivor.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def setup_tables():
    conn = get_connection()
    c = conn.cursor()

    logger.info("Setting up tables.")

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT UNIQUE NOT NULL,
            username TEXT
        );
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            number INT UNIQUE NOT NULL,
            episode INT DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'inactive'
        );
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tribes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '#d3d3d3',
            season INTEGER NOT NULL,
            FOREIGN KEY(season) REFERENCES seasons(id)
        );
    ''')

    logger.info("Finished setting up tables.")

    conn.commit()
    conn.close()

def add_user(discord_id: str, username: str):
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

    log_update(c, 
               f"'users' table updated: discord_id={discord_id}, username={username}.", 
               f"'users' table unchanged: discord_id={discord_id}, username={username}")
    
    conn.commit()
    conn.close()

def add_season(season_name: str, season_number: int):
    conn = get_connection()
    c = conn.cursor()

    command = '''
        INSERT INTO seasons (name, number)
        VALUES (?, ?)
        ON CONFLICT(number)
        DO UPDATE SET name = excluded.name
        WHERE seasons.name IS NOT excluded.name;
    '''
    c.execute(command, (season_name, season_number))

    log_update(c, 
               f"'seasons' table updated: number={season_number}, name={season_name}.", 
               f"'seasons' table unchanged: number={season_number}, name={season_name}")
    
    conn.commit()
    conn.close()

def get_all_seasons():
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT * FROM seasons ORDER BY number')
    rows = c.fetchall()

    conn.close()
    return [dict(row) for row in rows]

def activate_season(season_name: str, season_number: int) -> bool:
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT id FROM seasons WHERE name = ? AND number = ?', (season_name, season_number))
    result = c.fetchone()
    if not result:
        conn.close()
        return False
    
    c.execute('UPDATE seasons SET status = "inactive"')

    c.execute('''
        UPDATE seasons
        SET status = "active"
        WHERE name = ? AND number = ?
    ''', (season_name, season_number))

    conn.commit()
    conn.close()
    return True

def get_active_season():
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT * FROM seasons WHERE status = "active" LIMIT 1')
    row = c.fetchone()

    conn.close()
    return dict(row) if row else None

def add_tribe(name: str, season_number: int, color: str = '#d3d3d3'):
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT id FROM seasons WHERE number = ?', (season_number,))
    result = c.fetchone()

    if not result:
        logger.warning(f"Failed to add tribe '{name}': season #{season_number} does not exist.")
        conn.close()
        return False
    
    season_id = result['id']

    command = '''
        INSERT INTO tribes (name, color, season)
        VALUES (?, ?, ?);
    '''
    c.execute(command, (name.strip(), color.strip(), season_id))

    log_update(
        c,
        f"Added tribe '{name}' to season #{season_number} with color '{color}'.",
        f"Failed to add tribe '{name}' to season #{season_number}."
    )

    conn.commit()
    conn.close()
    return True