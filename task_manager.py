import sqlite3
from datetime import datetime


class Task:
    def __init__(self, title, description, due_date, due_time, task_id=None):
        self.id = task_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.due_time = due_time
        self.completed = False
        self.priority = 0
        self.is_important = False
        self.added_date_time = datetime.now()
        self.categories = []
        self.recurring = False
        self.recur_every = 0

    def mark_as_important(self):
        self.is_important = True

    def set_priority(self, priority):
        self.priority = priority

    def set_completed(self):
        self.completed = True

    def add_category(self, category):
        if category not in self.categories:
            self.categories.append(category)

    def is_category(self, category):
        return category in self.categories

    def set_recurring(self, every):
        self.recurring = True
        self.recur_every = every

    def get_unique_identifier(self):
        return f"{self.title}_{self.due_date}_{self.due_time}"

    def __str__(self):
        return f"Task: {self.title}\nDue: {self.due_date} at {self.due_time}\nAdded on: {self.added_date_time}\nPriority: {self.priority}\nImportant: {self.is_important}\nCompleted: {self.completed}"


class TaskList:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.create_table()
        self.tasks = self.load_tasks()
        self.pin = False
        self.queue = False
        self.stack = False

    def create_table(self):
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
            cursor = self.conn.cursor()
            cursor.execute(create_tasks_table)
        except sqlite3.Error as e:
            print(e)

    def load_tasks(self):
        tasks = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        rows = cursor.fetchall()
        for row in rows:
            task = Task(
                title=row['title'],
                description=row['description'],
                due_date=row['due_date'],
                due_time=row['due_time'],
                task_id=row['id']
            )
            task.completed = row['completed']
            task.priority = row['priority']
            task.is_important = row['is_important']
            task.added_date_time = datetime.fromisoformat(row['added_date_time'])
            task.categories = row['categories'].split(',') if row['categories'] else []
            task.recurring = row['recurring']
            task.recur_every = row['recur_every']
            tasks.append(task)
        return tasks

    def add_task(self, task):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, due_date, due_time, completed, priority, is_important, added_date_time, categories, recurring, recur_every) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task.title, task.description, task.due_date, task.due_time, task.completed, task.priority,
             task.is_important,
             task.added_date_time.isoformat(), ','.join(task.categories), task.recurring, task.recur_every)
        )
        self.conn.commit()
        task.id = cursor.lastrowid
        self.tasks.append(task)

    def remove_task(self, task):
        cursor = self.conn.cursor()
        unique_identifier = task.get_unique_identifier()
        cursor.execute("DELETE FROM tasks WHERE title=? AND due_date=? AND due_time=?",
                       (task.title, task.due_date, task.due_time))
        self.conn.commit()
        self.tasks = [t for t in self.tasks if t.get_unique_identifier() != unique_identifier]

    def update_task(self, task):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET title=?, description=?, due_date=?, due_time=?, completed=?, priority=?, is_important=?, categories=?, recurring=?, recur_every=?
            WHERE id=?
        """, (
            task.title, task.description, task.due_date, task.due_time, task.completed, task.priority,
            task.is_important,
            ','.join(task.categories), task.recurring, task.recur_every, task.id)
                       )
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def get_tasks(self):
        important_tasks = [task for task in self.tasks if task.is_important and not task.completed]
        other_tasks = [task for task in self.tasks if not task.is_important and not task.completed]
        if self.queue:
            other_tasks.sort(key=lambda task: task.added_date_time)
            important_tasks.sort(key=lambda task: task.added_date_time)
            return important_tasks + other_tasks
        elif self.stack:
            other_tasks.sort(key=lambda task: task.added_date_time)
            important_tasks.sort(key=lambda task: task.added_date_time)
            return list(reversed(important_tasks + other_tasks))
        return important_tasks + other_tasks

    def get_completed_tasks(self):
        completed_tasks = [task for task in self.tasks if task.completed]
        if self.queue:
            return sorted(completed_tasks, key=lambda task: task.added_date_time)
        elif self.stack:
            sorted_completed_tasks = sorted(completed_tasks, key=lambda task: task.added_date_time)
            return list(reversed(sorted_completed_tasks))
        return completed_tasks

    def get_important_tasks(self):
        return [task for task in self.tasks if task.is_important and not task.completed]

    def get_tasks_filter_category(self, category):
        important_tasks = [task for task in self.tasks if task.is_important and task.is_category(category)]
        other_tasks = [task for task in self.tasks if not task.is_important and task.is_category(category)]
        if self.queue:
            important_tasks.sort(key=lambda task: task.added_date_time)
            other_tasks.sort(key=lambda task: task.added_date_time)
            return important_tasks + other_tasks
        elif self.stack:
            important_tasks.sort(key=lambda task: task.added_date_time)
            other_tasks.sort(key=lambda task: task.added_date_time)
            return list(reversed(important_tasks + other_tasks))
        return important_tasks + other_tasks

    def get_tasks_filter_priority(self):
        return sorted(self.tasks, key=lambda task: task.priority, reverse=True)

    def __str__(self):
        return '\n'.join(str(task) for task in self.tasks if not task.completed)

# if __name__ == "__main__":
#     first = Task("task", "wadawd", "2024-02-29", "12:00")
#     task_list = TaskList("tasks.db")
#     task_list.add_task(first)
#     task_list.remove_task(first)
#     for task in task_list.get_tasks():
#         print(task)
