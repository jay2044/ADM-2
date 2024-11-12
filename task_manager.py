import sqlite3
import os
from datetime import datetime, timedelta
import re
import json


def sanitize_name(name):
    return re.sub(r'\W+', '_', name)


class Subtask:
    def __init__(self, title, description='', due_date=None, due_time=None,
                 completed=False, subtask_id=None, task_id=None, order=0):
        self.id = subtask_id
        self.task_id = task_id
        self.title = title
        self.completed = completed
        self.order = order

    def __str__(self):
        return f"Subtask: {self.title}, Completed: {self.completed}"


class Task:
    def __init__(self, title, description, due_date, due_time, task_id=None, is_important=False, priority=0,
                 completed=False, categories=None, recurring=False, recur_every=None, last_completed_date=None,
                 list_name=None, status="Not Started", estimate=0.0, count_required=0, count_completed=0,
                 subtasks=None, dependencies=None, deadline_flexibility="Strict", effort_level="Medium",
                 resources=None, notes="", time_logged=0.0, recurring_subtasks=None):
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
        # Allow recur_every to be either an int or a list
        if isinstance(recur_every, int):
            self.recur_every = [recur_every]
        elif isinstance(recur_every, list):
            self.recur_every = recur_every
        else:
            self.recur_every = []
        self.last_completed_date = last_completed_date  # Datetime object
        self.list_name = list_name  # Added to keep track of the task's list name

        # Advanced attributes
        self.status = status  # e.g., 'Not Started', 'In Progress', etc.
        self.estimate = estimate  # float, in hours or days
        self.count_required = count_required  # int
        self.count_completed = count_completed  # int
        self.subtasks = subtasks if subtasks else []  # List of Subtask objects
        self.dependencies = dependencies if dependencies else []
        self.deadline_flexibility = deadline_flexibility  # 'Strict' or 'Flexible'
        self.effort_level = effort_level  # 'Easy', 'Medium', 'Hard'
        self.resources = resources if resources else []
        self.notes = notes
        self.time_logged = time_logged  # float, in hours
        self.recurring_subtasks = recurring_subtasks if recurring_subtasks else []

    def mark_as_important(self):
        self.is_important = True

    def unmark_as_important(self):
        self.is_important = False

    def set_priority(self, priority):
        self.priority = priority

    def set_completed(self):
        self.completed = True
        self.last_completed_date = datetime.now()
        print(f"set completed on {self.last_completed_date}")
        self.status = "Completed"

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

    @property
    def progress(self):
        if self.count_required > 0:
            return (self.count_completed / self.count_required) * 100
        elif self.subtasks:
            if len(self.subtasks) == 0:
                return 0.0
            completed_subtasks = sum(1 for subtask in self.subtasks if subtask.completed)
            return (completed_subtasks / len(self.subtasks)) * 100
        else:
            return 0.0

    def calculate_priority_weighting(self):
        # Example implementation; you can adjust the weighting factors
        priority_score = self.priority
        if self.is_important:
            priority_score += 2
        if self.due_date:
            days_until_due = (datetime.strptime(self.due_date, '%Y-%m-%d') - datetime.now()).days
            if days_until_due <= 0:
                priority_score += 5  # Overdue tasks get higher priority
            elif days_until_due <= 3:
                priority_score += 3
            elif days_until_due <= 7:
                priority_score += 1
        if self.dependencies:
            priority_score -= len(self.dependencies)  # Tasks with dependencies might have lower priority
        if self.estimate:
            priority_score += self.estimate / 10  # Longer tasks might be given slightly higher priority
        return priority_score

    def __str__(self):
        return f"Task: {self.title}\nDue: {self.due_date} at {self.due_time}\nAdded on: {self.added_date_time}\nPriority: {self.priority}\nImportant: {self.is_important}\nCompleted: {self.completed}"


class TaskList:
    def __init__(self, list_name, manager, pin=False, queue=False, stack=False, category=None, task_categories=None):
        self.list_name = list_name
        self.manager = manager
        self.pin = pin
        self.queue = queue
        self.stack = stack
        self.category = category
        self.task_categories = task_categories or []
        self.tasks = self.load_tasks()

    def set_category(self, category):
        self.category = category

    def add_task_category(self, task_categories):
        self.task_categories.append(task_categories)

    def remove_task_category(self, task_categories):
        self.task_categories.remove(task_categories)

    def get_task_categories(self):
        return self.task_categories

    def load_tasks(self):
        tasks = self.manager.load_tasks(self.list_name)
        for task in tasks:
            if isinstance(task.categories, list):
                for category in task.categories:
                    if category not in self.task_categories:
                        self.task_categories.append(category)
        return tasks

    def add_task(self, task):
        self.manager.add_task(task, self.list_name)
        self.tasks.append(task)
        # Check if task has categories and update task_categories if new ones are found
        if hasattr(task, 'categories') and isinstance(task.categories, list):
            for category in task.categories:
                if category not in self.task_categories:
                    self.task_categories.append(category)

    def remove_task(self, task):
        self.manager.remove_task(task)
        self.tasks = [t for t in self.tasks if t.id != task.id]

    def update_task(self, task):
        self.manager.update_task(task)

    # Subtask management methods
    def add_subtask(self, task, subtask):
        subtask.task_id = task.id
        self.manager.add_subtask(subtask)
        task.subtasks.append(subtask)

    def remove_subtask(self, task, subtask):
        self.manager.remove_subtask(subtask)
        task.subtasks = [st for st in task.subtasks if st.id != subtask.id]

    def update_subtask(self, subtask):
        self.manager.update_subtask(subtask)

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
        return sorted(filtered_tasks, key=lambda task: task.calculate_priority_weighting(), reverse=True)

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
            task_categories TEXT,
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
            status TEXT,
            estimate REAL,
            count_required INTEGER,
            count_completed INTEGER,
            dependencies TEXT,
            deadline_flexibility TEXT,
            effort_level TEXT,
            resources TEXT,
            notes TEXT,
            time_logged REAL,
            recurring_subtasks TEXT,
            FOREIGN KEY(list_name) REFERENCES task_lists(list_name) ON DELETE CASCADE
        );
        """

        create_subtasks_table = """
            CREATE TABLE IF NOT EXISTS subtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL CHECK (completed IN (0,1)),
                "order" INTEGER,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            );
            """

        try:
            cursor = self.conn.cursor()
            cursor.execute(create_categories_table)
            cursor.execute(create_task_lists_table)
            cursor.execute(create_tasks_table)
            cursor.execute(create_subtasks_table)
            # Check and add missing columns to subtasks table
            cursor.execute("PRAGMA table_info(subtasks)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            if "order" not in existing_columns:
                cursor.execute("ALTER TABLE subtasks ADD COLUMN \"order\" INTEGER")
            self.conn.commit()

            # Check and add missing columns
            cursor.execute("PRAGMA table_info(tasks)")
            existing_columns = [column[1] for column in cursor.fetchall()]

            required_columns = [
                ('status', 'TEXT'),
                ('estimate', 'REAL'),
                ('count_required', 'INTEGER'),
                ('count_completed', 'INTEGER'),
                ('dependencies', 'TEXT'),
                ('deadline_flexibility', 'TEXT'),
                ('effort_level', 'TEXT'),
                ('resources', 'TEXT'),
                ('notes', 'TEXT'),
                ('time_logged', 'REAL'),
                ('recurring_subtasks', 'TEXT'),
            ]

            for column_name, column_def in required_columns:
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_def}")
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
                    "category": category_name,
                    "task_categories": task_list_row["task_categories"]
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
                "category": None,
                "task_categories": task_list_row["task_categories"]
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
                "category": row["category_name"],
                "task_categories": row["task_categories"]
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
                list_name=row['list_name'],
                status=row['status'] if 'status' in row.keys() else "Not Started",
                estimate=row['estimate'] if 'estimate' in row.keys() else 0.0,
                count_required=row['count_required'] if 'count_required' in row.keys() else 0,
                count_completed=row['count_completed'] if 'count_completed' in row.keys() else 0,
                dependencies=json.loads(row['dependencies']) if row['dependencies'] else [],
                deadline_flexibility=row['deadline_flexibility'] if 'deadline_flexibility' in row.keys() else "Strict",
                effort_level=row['effort_level'] if 'effort_level' in row.keys() else "Medium",
                resources=json.loads(row['resources']) if row['resources'] else [],
                notes=row['notes'] if 'notes' in row.keys() else "",
                time_logged=row['time_logged'] if 'time_logged' in row.keys() else 0.0,
                recurring_subtasks=json.loads(row['recurring_subtasks']) if row['recurring_subtasks'] else [],
            )
            task.added_date_time = datetime.fromisoformat(row['added_date_time'])
            # Load subtasks for this task
            task.subtasks = self.load_subtasks(task.id)
            tasks.append(task)
        return tasks

    def load_subtasks(self, task_id):
        subtasks = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM subtasks WHERE task_id=? ORDER BY \"order\"", (task_id,))
        rows = cursor.fetchall()
        for row in rows:
            subtask = Subtask(
                title=row['title'],
                completed=bool(row['completed']),
                subtask_id=row['id'],
                task_id=row['task_id'],
                order=row['order'] if 'order' in row.keys() else 0
            )
            subtasks.append(subtask)
        return subtasks

    def add_subtask(self, subtask):
        cursor = self.conn.cursor()
        # Get the maximum order value
        cursor.execute("SELECT MAX(\"order\") FROM subtasks WHERE task_id=?", (subtask.task_id,))
        max_order = cursor.fetchone()[0]
        if max_order is None:
            max_order = 0
        else:
            max_order += 1
        cursor.execute("""
            INSERT INTO subtasks (task_id, title, completed, "order")
            VALUES (?, ?, ?, ?)
        """, (
            subtask.task_id, subtask.title, int(subtask.completed), max_order
        ))
        self.conn.commit()
        subtask.id = cursor.lastrowid
        subtask.order = max_order

    def update_subtask(self, subtask):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE subtasks
            SET title=?, completed=?, "order"=?
            WHERE id=?
        """, (
            subtask.title, int(subtask.completed), subtask.order,
            subtask.id
        ))
        self.conn.commit()

    def remove_subtask(self, subtask):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM subtasks WHERE id=?", (subtask.id,))
        self.conn.commit()

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
            """
            INSERT INTO tasks (
                list_name, title, description, due_date, due_time, completed, priority, is_important,
                added_date_time, categories, recurring, recur_every, last_completed_date,
                status, estimate, count_required, count_completed, dependencies,
                deadline_flexibility, effort_level, resources, notes, time_logged, recurring_subtasks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                list_name, task.title, task.description, task.due_date, task.due_time, int(task.completed),
                task.priority, int(task.is_important), task.added_date_time.isoformat(),
                ','.join(task.categories), int(task.recurring), json.dumps(task.recur_every),
                task.last_completed_date.isoformat() if task.last_completed_date else None,
                task.status, task.estimate, task.count_required, task.count_completed,
                json.dumps(task.dependencies) if task.dependencies else None,
                task.deadline_flexibility, task.effort_level,
                json.dumps(task.resources) if task.resources else None,
                task.notes, task.time_logged,
                json.dumps(task.recurring_subtasks) if task.recurring_subtasks else None
            )
        )
        self.conn.commit()
        task.id = cursor.lastrowid

        # Add subtasks if any
        for subtask in task.subtasks:
            subtask.task_id = task.id
            self.add_subtask(subtask)

    def update_task(self, task):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET title=?, description=?, due_date=?, due_time=?, completed=?, priority=?, is_important=?, categories=?, recurring=?, recur_every=?, last_completed_date=?,
                status=?, estimate=?, count_required=?, count_completed=?, dependencies=?, deadline_flexibility=?, effort_level=?, resources=?, notes=?, time_logged=?, recurring_subtasks=?
            WHERE id=?
        """, (
            task.title, task.description, task.due_date, task.due_time, int(task.completed), task.priority,
            int(task.is_important), ','.join(task.categories), int(task.recurring),
            json.dumps(task.recur_every),
            task.last_completed_date.isoformat() if task.last_completed_date else None,
            task.status, task.estimate, task.count_required, task.count_completed,
            json.dumps(task.dependencies) if task.dependencies else None,
            task.deadline_flexibility, task.effort_level,
            json.dumps(task.resources) if task.resources else None,
            task.notes, task.time_logged,
            json.dumps(task.recurring_subtasks) if task.recurring_subtasks else None,
            task.id)
                       )
        self.conn.commit()

        # Update subtasks
        existing_subtask_ids = [subtask.id for subtask in task.subtasks if subtask.id]
        cursor.execute("SELECT id FROM subtasks WHERE task_id=?", (task.id,))
        db_subtask_ids = [row['id'] for row in cursor.fetchall()]

        # Remove subtasks that are no longer in the task's subtasks list
        for db_subtask_id in db_subtask_ids:
            if db_subtask_id not in existing_subtask_ids:
                self.remove_subtask(Subtask(subtask_id=db_subtask_id))

        # Add or update subtasks
        for subtask in task.subtasks:
            if subtask.id:
                self.update_subtask(subtask)
            else:
                subtask.task_id = task.id
                self.add_subtask(subtask)

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
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE recurring=1")
        rows = cursor.fetchall()

        # Define weekday mapping for reference
        weekday_mapping = {
            "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4,
            "Fri": 5, "Sat": 6, "Sun": 7
        }

        for row in rows:
            # Interpret recur_every as weekday names or integer days
            recur_every_raw = json.loads(row['recur_every']) if row['recur_every'] else []
            print(f"Processing task '{row['title']}' with recur_every: {recur_every_raw}")

            if isinstance(recur_every_raw, int):
                recur_every = [recur_every_raw]
            elif isinstance(recur_every_raw, list):
                recur_every = [day for day in recur_every_raw if day in weekday_mapping]
            else:
                recur_every = []

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
                recur_every=recur_every,
                last_completed_date=datetime.fromisoformat(row['last_completed_date']) if row[
                    'last_completed_date'] else None,
                list_name=row['list_name']
            )
            task.added_date_time = datetime.fromisoformat(row['added_date_time'])

            # Print last completed date
            if task.last_completed_date:
                print(f"Task '{task.title}' last completed on: {task.last_completed_date.date()}")

            # Skip tasks completed today
            if task.last_completed_date and task.last_completed_date.date() == datetime.now().date():
                print(f"Skipping task '{task.title}' as it was completed today.")
                continue

            # Process recurring tasks based on recur_every
            if task.completed and task.recur_every:
                if len(task.recur_every) == 1 and isinstance(task.recur_every[0], int):
                    days_to_add = task.recur_every[0]
                    next_available_date = (task.last_completed_date + timedelta(days=days_to_add)
                                           if task.last_completed_date else datetime.now() + timedelta(
                        days=days_to_add))

                    print(f"Task '{task.title}' calculated next available date: {next_available_date.date()}")

                    if next_available_date <= datetime.now():
                        print(f"Reopening task '{task.title}' as it has reached its recurrence date.")
                        task.completed = False
                        self.update_task(task)

                else:
                    # Handle weekday names in recur_every
                    today = datetime.now()
                    today_weekday = today.isoweekday()

                    print(
                        f"Today is weekday {today_weekday}. Task '{task.title}' checks against recur_every: {task.recur_every} it was last set complet on {task.last_completed_date}")

                    # Check if today matches any specified weekday in recur_every
                    if any(weekday_mapping[day] == today_weekday for day in task.recur_every):
                        print(f"Reopening task '{task.title}' as today matches one of its specified recurrence days.")
                        task.completed = False
                        self.update_task(task)
                    else:
                        print(f"Task '{task.title}' does not recur today.")

    def __del__(self):
        self.conn.close()
