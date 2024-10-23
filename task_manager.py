import sqlite3
import os
from datetime import datetime, timedelta
import re
import json


def sanitize_name(name):
    return re.sub(r'\W+', '_', name)


class Task:
    def __init__(self, title, description, due_date, due_time, task_id=None, is_important=False, priority=0,
                 completed=False, categories=None, recurring=False, recur_every=None, last_completed_date=None,
                 list_name=None):
        self.id = task_id
        self.title = title
        self.description = description
        self.due_date = due_date  # Expected format: 'YYYY-MM-DD'
        self.due_time = due_time  # Expected format: 'HH:MM'
        self.completed = completed
        self.priority = priority
        self.is_important = is_important
        self.added_date_time = datetime.now()
        self.categories = categories if categories else []
        self.recurring = recurring
        self.recur_every = recur_every if isinstance(recur_every, list) else []
        self.last_completed_date = last_completed_date  # Datetime object
        self.list_name = list_name  # Added to keep track of the task's list name

    def mark_as_important(self):
        self.is_important = True

    def unmark_as_important(self):
        self.is_important = False

    def set_priority(self, priority):
        self.priority = priority

    def set_completed(self):
        self.completed = True
        self.last_completed_date = datetime.now()

    def add_category(self, category):
        if category not in self.categories:
            self.categories.append(category)

    def is_category(self, category):
        return category in self.categories

    def set_recurring(self, every):
        self.recurring = True
        self.recur_every = every if isinstance(every, list) else [every]

    def get_unique_identifier(self):
        return f"{self.title}_{self.due_date}_{self.due_time}"

    def __str__(self):
        return f"Task: {self.title}\nDue: {self.due_date} at {self.due_time}\nAdded on: {self.added_date_time}\nPriority: {self.priority}\nImportant: {self.is_important}\nCompleted: {self.completed}"


class TaskList:
    def __init__(self, list_name, manager, pin=False, queue=False, stack=False, category=None):
        self.list_name = list_name
        self.manager = manager
        self.tasks = self.load_tasks()
        self.pin = pin
        self.queue = queue
        self.stack = stack
        self.category = category

    def load_tasks(self):
        return self.manager.load_tasks(self.list_name)

    def add_task(self, task):
        self.manager.add_task(task, self.list_name)
        self.tasks.append(task)

    def remove_task(self, task):
        self.manager.remove_task(task)
        self.tasks = [t for t in self.tasks if t.id != task.id]

    def update_task(self, task):
        self.manager.update_task(task)

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
            other_tasks = list(reversed(other_tasks))
            important_tasks = list(reversed(important_tasks))
            return important_tasks + other_tasks
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
        filtered_tasks = [task for task in self.tasks if not task.completed]
        return sorted(filtered_tasks, key=lambda task: task.priority, reverse=True)

    def __str__(self):
        return '\n'.join(str(task) for task in self.tasks if not task.completed)


class TaskListManager:
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_file = os.path.join(self.data_dir, "task_lists.db")
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.categories = self.load_categories()
        self.task_lists = self.load_task_lists()
        self.manage_recurring_tasks()

    def create_tables(self):
        create_categories_table = """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                pin BOOLEAN NOT NULL DEFAULT 0
            );
            """

        create_task_lists_table = """
        CREATE TABLE IF NOT EXISTS task_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_name TEXT NOT NULL UNIQUE,
            category_id INTEGER,
            pin BOOLEAN NOT NULL DEFAULT 0,
            queue BOOLEAN NOT NULL DEFAULT 0,
            stack BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
        );
        """
        create_tasks_table = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_name TEXT NOT NULL,
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
            recur_every TEXT,
            last_completed_date TEXT,
            FOREIGN KEY(list_name) REFERENCES task_lists(list_name) ON DELETE CASCADE
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_categories_table)
            cursor.execute(create_task_lists_table)
            cursor.execute(create_tasks_table)
            self.conn.commit()

            # Check if 'pin' column exists and add if necessary
            cursor.execute("PRAGMA table_info(categories)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'pin' not in columns:
                cursor.execute("ALTER TABLE categories ADD COLUMN pin BOOLEAN NOT NULL DEFAULT 0")
                self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def pin_category(self, category_name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE categories SET pin = NOT pin WHERE name = ?", (category_name,))
        self.conn.commit()
        # Update in-memory data
        self.categories = self.load_categories()

    def load_categories(self):
        categories = {}
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM categories")
        category_rows = cursor.fetchall()
        for category_row in category_rows:
            category_id = category_row["id"]
            category_name = category_row["name"]
            category_pin = bool(category_row["pin"]) if "pin" in category_row.keys() else False  # Get the 'pin' value
            categories[category_name] = {
                "pin": category_pin,
                "task_lists": []
            }
            cursor.execute("SELECT * FROM task_lists WHERE category_id=?", (category_id,))
            task_list_rows = cursor.fetchall()
            for task_list_row in task_list_rows:
                categories[category_name]["task_lists"].append({
                    "list_name": task_list_row["list_name"],
                    "pin": bool(task_list_row["pin"]),
                    "queue": bool(task_list_row["queue"]),
                    "stack": bool(task_list_row["stack"]),
                    "category": category_name
                })

        # Always include "Uncategorized" category
        categories["Uncategorized"] = {
            "pin": False,
            "task_lists": []
        }

        # Handle uncategorized task lists
        cursor.execute("SELECT * FROM task_lists WHERE category_id IS NULL")
        uncategorized_task_lists = cursor.fetchall()
        for task_list_row in uncategorized_task_lists:
            categories["Uncategorized"]["task_lists"].append({
                "list_name": task_list_row["list_name"],
                "pin": bool(task_list_row["pin"]),
                "queue": bool(task_list_row["queue"]),
                "stack": bool(task_list_row["stack"]),
                "category": None
            })

        return categories

    def load_task_lists(self):
        task_lists = []
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT tl.*, c.name as category_name
            FROM task_lists tl
            LEFT JOIN categories c ON tl.category_id = c.id
        """)
        rows = cursor.fetchall()
        for row in rows:
            task_lists.append({
                "list_name": row["list_name"],
                "pin": bool(row["pin"]),
                "queue": bool(row["queue"]),
                "stack": bool(row["stack"]),
                "category": row["category_name"]
            })
        return task_lists

    def load_tasks(self, list_name):
        tasks = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE list_name=?", (list_name,))
        rows = cursor.fetchall()
        for row in rows:
            task = Task(
                title=row['title'],
                description=row['description'],
                due_date=row['due_date'],
                due_time=row['due_time'],
                task_id=row['id'],
                is_important=bool(row['is_important']),
                priority=row['priority'],
                completed=bool(row['completed']),
                categories=row['categories'].split(',') if row['categories'] else [],
                recurring=bool(row['recurring']),
                recur_every=json.loads(row['recur_every']) if row['recur_every'] else [],
                last_completed_date=datetime.fromisoformat(row['last_completed_date']) if row[
                    'last_completed_date'] else None,
                list_name=row['list_name']
            )
            task.added_date_time = datetime.fromisoformat(row['added_date_time'])
            tasks.append(task)
        return tasks

    def add_category(self, category_name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
        self.conn.commit()
        self.categories[category_name] = []

    def rename_category(self, old_name, new_name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE categories SET name=? WHERE name=?", (new_name, old_name))
        self.conn.commit()
        # Reload categories
        self.categories = self.load_categories()

    def remove_category(self, category_name):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM categories WHERE name=?", (category_name,))
        self.conn.commit()
        self.categories = self.load_categories()  # Refresh in-memory categories after removal

    def get_categories(self):
        self.categories = self.load_categories()
        return self.categories

    def add_task_list(self, list_name, pin=False, queue=False, stack=False, category=None):
        if list_name not in [task_list["list_name"] for task_list in self.task_lists]:
            cursor = self.conn.cursor()
            category_id = None
            if category:
                cursor.execute("SELECT id FROM categories WHERE name=?", (category,))
                result = cursor.fetchone()
                if result:
                    category_id = result["id"]
            cursor.execute(
                "INSERT INTO task_lists (list_name, category_id, pin, queue, stack) VALUES (?, ?, ?, ?, ?)",
                (list_name, category_id, int(pin), int(queue), int(stack))
            )
            self.conn.commit()
            # Reload task lists and categories
            self.task_lists = self.load_task_lists()
            self.categories = self.load_categories()

    def remove_task_list(self, list_name):
        if list_name in [task_list["list_name"] for task_list in self.task_lists]:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM task_lists WHERE list_name=?", (list_name,))
            cursor.execute("DELETE FROM tasks WHERE list_name=?", (list_name,))
            self.conn.commit()
            self.task_lists = [task_list for task_list in self.task_lists if task_list["list_name"] != list_name]
            # Remove from categories
            for category_name, task_lists in self.categories.items():
                self.categories[category_name] = [tl for tl in task_lists if tl != list_name]

    def change_task_list_name(self, task_list, new_name):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE task_lists
            SET list_name = ?
            WHERE list_name = ?
        """, (new_name, task_list.list_name))
        cursor.execute("""
            UPDATE tasks
            SET list_name = ?
            WHERE list_name = ?
        """, (new_name, task_list.list_name))
        self.conn.commit()
        for tl in self.task_lists:
            if tl["list_name"] == task_list.list_name:
                tl["list_name"] = new_name
                break
        # Update in categories
        if task_list.category:
            for tl in self.categories[task_list.category]:
                if tl["list_name"] == task_list.list_name:
                    tl["list_name"] = new_name
                    break
        task_list.list_name = new_name

    def change_task_list_name_by_name(self, old_name, new_name):
        cursor = self.conn.cursor()

        # Update task list name in task_lists table
        cursor.execute("""
            UPDATE task_lists
            SET list_name = ?
            WHERE list_name = ?
        """, (new_name, old_name))

        # Update task list name in tasks table
        cursor.execute("""
            UPDATE tasks
            SET list_name = ?
            WHERE list_name = ?
        """, (new_name, old_name))

        self.conn.commit()

        # Update in-memory task lists
        self.task_lists = [new_name if tl == old_name else tl for tl in self.task_lists]

        # Update in categories
        for category_name, task_list_info in self.categories.items():
            for task_list in task_list_info['task_lists']:
                if task_list["list_name"] == old_name:
                    task_list["list_name"] = new_name
                    break

    def add_task(self, task, list_name):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (list_name, title, description, due_date, due_time, completed, priority, is_important, added_date_time, categories, recurring, recur_every, last_completed_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (list_name, task.title, task.description, task.due_date, task.due_time, int(task.completed), task.priority,
             int(task.is_important), task.added_date_time.isoformat(), ','.join(task.categories), int(task.recurring),
             json.dumps(task.recur_every),
             task.last_completed_date.isoformat() if task.last_completed_date else None)
        )
        self.conn.commit()
        task.id = cursor.lastrowid

    def update_task(self, task):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET title=?, description=?, due_date=?, due_time=?, completed=?, priority=?, is_important=?, categories=?, recurring=?, recur_every=?, last_completed_date=?
            WHERE id=?
        """, (
            task.title, task.description, task.due_date, task.due_time, int(task.completed), task.priority,
            int(task.is_important), ','.join(task.categories), int(task.recurring),
            json.dumps(task.recur_every),
            task.last_completed_date.isoformat() if task.last_completed_date else None, task.id)
                       )
        self.conn.commit()

    def remove_task(self, task):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id=?", (task.id,))
        self.conn.commit()

    def update_task_list(self, task_list):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE task_lists
                SET pin = ?, queue = ?, stack = ?
                WHERE list_name = ?
            """, (int(task_list.pin), int(task_list.queue), int(task_list.stack), task_list.list_name))
            self.conn.commit()
        except Exception as e:
            print(f"Error in update_task_list: {e}")

    def pin_task_list(self, list_name):
        for task_list in self.task_lists:
            if task_list["list_name"] == list_name:
                task_list["pin"] = not task_list["pin"]
                self.update_task_list(task_list)
                break

    def get_task_lists(self):
        # Returns all task lists, you can modify this method if needed
        return self.task_lists

    def get_task_list(self, task_list_name):
        for task_list in self.task_lists:
            if task_list["list_name"] == task_list_name:
                return task_list

    def get_task_list_count(self):
        return len(self.task_lists)

    def manage_recurring_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE recurring=1")
        rows = cursor.fetchall()

        for row in rows:
            task = Task(
                title=row['title'],
                description=row['description'],
                due_date=row['due_date'],
                due_time=row['due_time'],
                task_id=row['id'],
                is_important=bool(row['is_important']),
                priority=row['priority'],
                completed=bool(row['completed']),
                categories=row['categories'].split(',') if row['categories'] else [],
                recurring=bool(row['recurring']),
                recur_every=json.loads(row['recur_every']) if row['recur_every'] else [],
                last_completed_date=datetime.fromisoformat(row['last_completed_date']) if row[
                    'last_completed_date'] else None,
                list_name=row['list_name']
            )
            task.added_date_time = datetime.fromisoformat(row['added_date_time'])

            if task.completed:
                if task.recur_every:
                    if len(task.recur_every) == 1:
                        # "Every N days" recurrence
                        days_to_add = task.recur_every[0]
                        new_due_date = datetime.strptime(task.due_date, '%Y-%m-%d') + timedelta(days=days_to_add)
                    else:
                        # "Specific weekdays" recurrence
                        today = datetime.now()
                        today_weekday = today.isoweekday()  # 1 (Monday) - 7 (Sunday)
                        days_ahead_list = [((weekday - today_weekday) % 7 or 7) for weekday in task.recur_every]
                        days_until_next = min(days_ahead_list)
                        new_due_date = today + timedelta(days=days_until_next)
                    # Update task with new due date and reset completion status
                    task.due_date = new_due_date.strftime('%Y-%m-%d')
                    task.completed = False
                    self.update_task(task)
                else:
                    # Handle the case where recur_every is empty
                    pass

    def __del__(self):
        self.conn.close()
