import sqlite3

def get_connection():
    return sqlite3.connect('sharkvivor.db', check_same_thread=False)

def setup_tables():
    conn = get_connection()
    c = conn.cursor()

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
            number INTEGER UNIQUE NOT NULL
        );
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tribes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            season_id INTEGER NOT NULL,
            FOREIGN KEY (season_id) REFERENCES seasons(id),
            UNIQUE(name, season_id)
        );       
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            season_id INTEGER NOT NULL,
            current_tribe_id INTEGER,
            status TEXT DEFAULT 'active', 
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (season_id) REFERENCES seasons(id),
            FOREIGN KEY (current_tribe_id) REFERENCES tribes(id),
            UNIQUE(user_id, season_id)
        );       
    ''')

    conn.commit()
    conn.close()

def add_user(discord_id, username):
    conn = get_connection()
    c = conn.cursor()

    c.execute('INSERT OR REPLACE INTO users (discord_id, username) VALUES (?, ?)', (discord_id, username))

    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT id, discord_id, username FROM users')
    rows = c.fetchall()

    conn.close()
    return rows

def add_season(name, number):
    conn = get_connection()
    c = conn.cursor()

    c.execute('INSERT OR REPLACE INTO seasons (name, number) VALUES (?, ?)', (name, number))

    conn.commit()
    conn.close()

def get_all_seasons():
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT id, name, number FROM seasons')
    rows = c.fetchall()

    conn.close()
    return rows()

def remove_season(name, number):
    conn = get_connection()
    c = conn.cursor()

    c.execute('DELETE FROM seasons WHERE name = ? AND number = ?', (name, number))

    conn.commit()
    conn.close()

def add_tribe(tribe_name, season_name):
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT id FROM seasons WHERE name = ?', (season_name,))
    result = c.fetchone()

    if result is None:
        print(f"Season '{season_name}' not found.")
        conn.close()
        return
    
    season_id = result[0]

    c.execute('INSERT INTO tribes (name, season_id) VALUES (?, ?)', (tribe_name, season_id))
    conn.commit()
    print(f"Tribe '{tribe_name}' added to Season '{season_name}'")

    conn.close()

def add_player(discord_id, season_name):
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT id FROM users WHERE discord_id = ?', (discord_id,))
    user_result = c.fetchone()
    if not user_result:
        print(f"User with Discord ID {discord_id} not found.")
        conn.close()
        return
    
    user_id = user_result[0]

    c.execute('SELECT id FROM seasons WHERE name = ?', (season_name,))
    season_result = c.fetchone()
    if not season_result:
        print(f"Season '{season_name}' not found.")
        conn.close()
        return
    
    season_id = season_result[0]

    c.execute('INSERT INTO players (user_id, season_id) VALUES (?, ?)', (user_id, season_id))
    print(f"Player added to season {season_name}.")
    conn.commit()
    conn.close()