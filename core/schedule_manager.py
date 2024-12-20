import os
import sqlite3
from .task_manager import TaskListManager


class ScheduleManager:
    def __init__(self):
        self.task_manager = TaskListManager()
        self.data_dir = "../data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_file = os.path.join(self.data_dir, "adm.db")
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS day_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS time_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id INTEGER,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    task_id INTEGER,
                    FOREIGN KEY (schedule_id) REFERENCES day_schedule (id),
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)

    def get_day_schedule(self, date):
        # Returns the DaySchedule for a given date
        return DaySchedule(date, self.conn, self.task_manager)


class DaySchedule:
    def __init__(self, date, conn, task_manager):
        self.date = date
        self.conn = conn
        self.task_manager = task_manager
        self.tasks = self.load_tasks()
        self.time_blocks = self.load_time_blocks()

    def load_tasks(self):
        return self.task_manager.get_tasks_for_date(self.date)

    def load_time_blocks(self):
        query = """
            SELECT * FROM time_blocks
            WHERE schedule_id = (
                SELECT id FROM day_schedule WHERE date = ?
            )
        """
        return [dict(row) for row in self.conn.execute(query, (self.date,))]

    def add_time_block(self, start_time, end_time, task_id):
        with self.conn:
            schedule_id = self.get_or_create_schedule_id()
            self.conn.execute("""
                INSERT INTO time_blocks (schedule_id, start_time, end_time, task_id)
                VALUES (?, ?, ?, ?)
            """, (schedule_id, start_time, end_time, task_id))
        self.time_blocks = self.load_time_blocks()

    def get_or_create_schedule_id(self):
        row = self.conn.execute("SELECT id FROM day_schedule WHERE date = ?", (self.date,)).fetchone()
        if row:
            return row["id"]
        return self.conn.execute("INSERT INTO day_schedule (date) VALUES (?)", (self.date,)).lastrowid
