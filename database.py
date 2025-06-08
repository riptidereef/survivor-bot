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

    command = '''
        SELECT id, status FROM seasons
        WHERE name = ? AND number = ?;
    '''
    c.execute(command, (season_name, season_number))
    result = c.fetchone()
