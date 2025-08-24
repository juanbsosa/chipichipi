import sqlite3
from pathlib import Path
from chipichipi.models import Song

def get_db_connection(db_path: Path):
    """Creates a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    # This enables accessing columns by name instead of just index
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path):
    """Initializes the database with the required tables."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Create the songs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            title TEXT,
            artist TEXT,
            album TEXT,
            track_number INTEGER,
            duration INTEGER,
            genre TEXT
        )
    ''')

    conn.commit()
    conn.close()

def insert_song(conn: sqlite3.Connection, song: Song):
    """Inserts a Song object into the database."""
    sql = '''
        INSERT OR REPLACE INTO songs 
        (file_path, title, artist, album, duration)
        VALUES (?, ?, ?, ?, ?)
    '''
    cursor = conn.cursor()
    cursor.execute(sql, (
        str(song.file_path), song.title, song.artist,
        song.album, song.duration
    ))
    conn.commit()