import sqlite3

DB_PATH = 'reptiles.db'


def get_db():
    """Return a connection to the main SQLite database.

    The connection uses :class:`sqlite3.Row` so rows can be treated as
    dictionaries.  The database file is located at :data:`DB_PATH`.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Ensure that all required tables exist in the database.

    This is safe to call multiple times; each ``CREATE TABLE IF NOT EXISTS``
    will silently skip existing tables.  Calling this from the application
    startup guarantees that a fresh install or an existing database will
    always have the schema expected by the code.
    """
    conn = get_db()
    # core tables
    conn.execute('''CREATE TABLE IF NOT EXISTS animals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT, species TEXT, category TEXT,
                        feed_days INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        animal_id INTEGER, action TEXT, value TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    # configuration/settings storage used by the frontend
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (
                        name TEXT PRIMARY KEY,
                        value TEXT)''')

    # add new columns to animals table if they don't already exist
    cur = conn.execute("PRAGMA table_info(animals)").fetchall()
    col_names = [r['name'] for r in cur]
    if 'burmating' not in col_names:
        conn.execute("ALTER TABLE animals ADD COLUMN burmating INTEGER DEFAULT 0")
    if 'strike_retry_days' not in col_names:
        conn.execute("ALTER TABLE animals ADD COLUMN strike_retry_days INTEGER DEFAULT 3")

    conn.commit()
    conn.close()
