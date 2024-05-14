import sqlite3


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table(conn):
    create_tasks_table = """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        due_time TEXT,
        completed BOOLEAN NOT NULL CHECK (completed IN (0, 1)),
        priority INTEGER,
        is_important BOOLEAN NOT NULL CHECK (is_important IN (0, 1)),
        added_date_time TEXT,
        categories TEXT,
        recurring BOOLEAN NOT NULL CHECK (recurring IN (0, 1)),
        recur_every INTEGER
    );
    """
    try:
        c = conn.cursor()
        c.execute(create_tasks_table)
    except sqlite3.Error as e:
        print(e)


conn = create_connection("tasks.db")
if conn is not None:
    create_table(conn)
    conn.close()
