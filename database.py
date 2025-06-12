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
            name TEXT UNIQUE NOT NULL,
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
            FOREIGN KEY(season) REFERENCES seasons(id),
            UNIQUE(name, season)
        );
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            season_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            role_color TEXT NOT NULL DEFAULT '#d3d3d3',
            tribe_id INTEGER DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (season_id) REFERENCES seasons(id),
            FOREIGN KEY (tribe_id) REFERENCES tribes(id),
            UNIQUE(display_name, season_id)
        );
    ''')

    logger.info("Finished setting up tables.")

    conn.commit()
    conn.close()

def add_user(discord_id: str, username: str) -> bool:
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

def add_season(season_name: str, season_number: int) -> bool:
    conn = get_connection()
    c = conn.cursor()

    command = '''
        INSERT OR IGNORE INTO seasons (name, number)
        VALUES (?, ?);
    '''
    c.execute(command, (season_name, season_number))

    success = c.rowcount > 0
    
    conn.commit()
    conn.close()

    return success

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

def add_tribe(season_name: str, tribe_name: str, color: str = '#d3d3d3') -> bool:
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT id FROM seasons WHERE name = ?', (season_name,))
    result = c.fetchone()

    if not result:
        conn.close()
        return False
    
    season_id = result['id']
    command = '''
        INSERT INTO tribes (name, color, season)
        VALUES (?, ?, ?)
        ON CONFLICT(name, season)
        DO UPDATE SET color = excluded.color;
    '''
    c.execute(command, (tribe_name.strip(), color.strip(), season_id))

    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success

def add_player(discord_id: str, 
               season_name: str, 
               display_name: str,
               role_color: str = '#b3b3b3',
               tribe_name: str = None) -> bool:
    
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT id FROM users WHERE discord_id = ?', (discord_id,))
    result = c.fetchone()

    if result is None:
        conn.close()
        return False
    
    user_id = result['id']

    c.execute('SELECT id FROM seasons WHERE name = ?', (season_name,))
    result = c.fetchone()

    if result is None:
        conn.close()
        return False
    
    season_id = result['id']
    
    tribe_id = None
    if tribe_name is not None:
        c.execute('SELECT id FROM tribes WHERE name = ? AND season = ?', (tribe_name, season_id))
        result = c.fetchone()

        if result is None:
            conn.close()
            return False
    
        tribe_id = result['id']
    
    command = '''
        INSERT OR IGNORE INTO players (user_id, season_id, display_name, role_color, tribe_id)
        VALUES (?, ?, ?, ?, ?)
    '''
    c.execute(command, (user_id, season_id, display_name, role_color, tribe_id))

    success = c.rowcount > 0

    conn.commit()
    conn.close()

    return success