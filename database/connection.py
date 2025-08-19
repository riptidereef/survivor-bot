import sqlite3
import logging
import os

log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "database.log")

logger = logging.getLogger("database_logger")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_path)
formatter = logging.Formatter(
    fmt='[%(asctime)s] [%(levelname)-8s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

DB_PATH = os.path.join(os.path.dirname(__file__), "sharkvivor.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def setup_tables():
    conn = get_connection()
    c = conn.cursor()

    commands = {
        "users": '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INT UNIQUE NOT NULL,
                username TEXT
            );
        ''',
        
        "seasons": '''
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INT UNIQUE NOT NULL,
                season_name TEXT NOT NULL
            );
        ''',

        "tribes": '''
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
        ''',

        "players": '''
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
    }

    for name, command in commands.items():
        try:
            c.execute(command)
            logger.info(f"{name.capitalize()} table setup completed.")
        except Exception as e:
            logger.error(f"Error setting up {name} table: {e}")

    conn.commit()
    conn.close()
