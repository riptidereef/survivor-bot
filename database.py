import sqlite3
import logging

logger = logging.getLogger("database_logger")
logger.setLevel(logging.INFO)

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
    return sqlite3.connect('sharkvivor.db', check_same_thread=False)

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
               f"users table unchanged: discord_id={discord_id}, username={username}")
    
    conn.commit()
    conn.close()

