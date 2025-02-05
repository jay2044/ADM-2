import sqlite3
import os
from datetime import datetime, timedelta
import re
import json
from core.signals import global_signals


def sanitize_name(name):
    return re.sub(r'\W+', '_', name)


class Task:
    def __init__(self, **kwargs):

        required_attributes = ['name', 'list_name']
        for attr in required_attributes:
            if attr not in kwargs or kwargs[attr] is None:
                raise ValueError(f"'{attr}' is a required attribute and cannot be None.")

        # Dynamically set attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.id = kwargs.get("id", None)
        self.name = kwargs.get("name")
        self.description = kwargs.get("description", None)
        self.notes = kwargs.get("notes", None)
        self.tags = kwargs.get("tags", [])
        self.resources = kwargs.get("resources", [])

        try:
            self.start_date = self._parse_date(
                kwargs.get("start_date", None),
                ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]
            )
            self.due_datetime = self._parse_date(
                kwargs.get("due_datetime", None),
                ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"]
            )
            self.added_date_time = self._parse_date(
                kwargs.get("added_date_time", None),
                ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"]
            )
            self.last_completed_date = self._parse_date(
                kwargs.get("last_completed_date", None),
                ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"]
            )
        except ValueError as e:
            raise ValueError(
                f"Date parsing error for Task '{self.name}' (ID: {self.id}). Details: {str(e)}"
            )

        self.list_order = kwargs.get("list_order", 0)
        self.list_name = kwargs.get("list_name")

        self.recurring = kwargs.get("recurring", False)
        self.recur_every = kwargs.get("recur_every",
                                      None)  # An int for recurrence every x days or a list of weekdays for recurrence.
        self.recurrences = kwargs.get("recurrences", 0)

        self.time_estimate = kwargs.get("time_estimate", 0.25)
        self.time_logged = kwargs.get("time_logged", 0.0)
        self.count_required = kwargs.get("count_required", 0)
        self.count_completed = kwargs.get("count_completed", 0)

        self.auto_chunk = kwargs.get("auto_chunk", True)
        self.min_chunk_size = kwargs.get("min_chunk_size", None)
        self.max_chunk_size = kwargs.get("max_chunk_size", None)

        self.manually_scheduled = kwargs.get("manually_scheduled", False)
        self.manually_scheduled_chunks = kwargs.get("manually_scheduled_chunks", [])  # eg: {"date": datetime obj, "timeblock": "timeblock name", "size": 0.0, "type": either count or time}

        self.assigned = kwargs.get("assigned", False)
        self.assigned_chunks = kwargs.get("assigned_chunks",
                                          [])

        self.single_chunk = kwargs.get("single_chunk", False)

        self.subtasks = kwargs.get("subtasks", None)  # [{"order": 1, "name": "test sub task", "completed": True}]
        self.dependencies = kwargs.get("dependencies", None)

        self.status = kwargs.get("status",
                                 "Not Started")  # ["Not Started", "In Progress", "Completed", "Failed", "On Hold"]
        self.flexibility = kwargs.get("flexibility", "Flexible")  # ["Strict", "Flexible", "Very Flexible]
        self.effort_level = kwargs.get("effort_level", "Medium")  # ["Low", "Medium", "High"]
        self.priority = kwargs.get("priority", 0)  # (0-10)
        self.previous_priority = kwargs.get("previous_priority", self.priority)
        self.preferred_work_days = kwargs.get("preferred_work_days", [])  # ["Monday", "Wednesday", ...]
        self.time_of_day_preference = kwargs.get("time_of_day_preference",
                                                 [])  # ["Morning", "Afternoon", "Evening", "Night"]

        self.progress = self.calculate_progress()

        self.include_in_schedule = kwargs.get("include_in_schedule", False)

        self.global_weight = kwargs.get("global_weight", None)

    @staticmethod
    def _parse_date(date_str, formats):
        """
        Parses a date string or datetime object.

        :param date_str: The date string or datetime object to parse.
        :param formats: A list of date formats to try if input is string.
        :return: Parsed datetime object or None if the date_str is None.
        :raises ValueError: If none of the formats match the date_str.
        """
        if date_str is None:
            return None

        # If already a datetime object, return it
        if isinstance(date_str, datetime):
            return date_str

        # Add format with fractional seconds
        formats.append("%Y-%m-%dT%H:%M:%S.%f")

        # Otherwise parse the string
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Date '{date_str}' does not match any of the provided formats: {formats}")

    def calculate_progress(self):
        if self.subtasks:
            completed_subtasks = sum(1 for subtask in self.subtasks if subtask.get("completed", False))
            total_subtasks = len(self.subtasks)
            if total_subtasks > 0:
                return (completed_subtasks / total_subtasks) * 100

        elif self.count_required:
            return (self.count_completed / self.count_required) * 100 if self.count_required > 0 else 0

        elif self.time_estimate and self.time_logged:
            return (self.time_logged / self.time_estimate) * 100 if self.time_estimate > 0 else 0

        return 0

    def set_attribute(self, attribute_name, value):
        if hasattr(self, attribute_name):
            setattr(self, attribute_name, value)
        else:
            raise AttributeError(f"{attribute_name} is not a valid attribute of Task")

    def get_attribute(self, attribute_name):
        if hasattr(self, attribute_name):
            return getattr(self, attribute_name)
        else:
            raise AttributeError(f"{attribute_name} is not a valid attribute of Task")

    def mark_as_important(self):
        if self.priority != 10:
            self.previous_priority = self.priority
            self.priority = 10

    def is_important(self):
        if self.priority == 10:
            return True
        return False

    def unmark_as_important(self):
        self.priority = self.previous_priority

    def set_priority(self, priority):
        self.priority = priority

    def set_completed(self, completion_date=None):
        if self.status != "Completed":
            self.status = "Completed"
            self.last_completed_date = self._parse_date(completion_date,
                                                        "%Y-%m-%d %H:%M") if completion_date else datetime.now()
            self.progress = 100
            print(f"Task '{self.name}' (ID: {self.id}) marked as completed on {self.last_completed_date}.")

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag):
        return tag in self.tags

    def set_recurring(self, every):
        self.recurring = True
        self.recur_every = every if isinstance(every, list) else every

    def add_subtask(self, name, order=None, completed=False):
        if not self.subtasks:
            self.subtasks = []
        if order is None:
            order = len(self.subtasks) + 1
        self.subtasks.append({"order": order, "name": name, "completed": completed})
        self.subtasks = sorted(self.subtasks, key=lambda x: x["order"])

    def remove_subtask(self, name):
        if self.subtasks:
            self.subtasks = [subtask for subtask in self.subtasks if subtask["name"] != name]

    def mark_subtask_completed(self, name):
        if self.subtasks:
            for subtask in self.subtasks:
                if subtask["name"] == name:
                    subtask["completed"] = True
                    break

    def update_subtask(self, name, **kwargs):
        if self.subtasks:
            for subtask in self.subtasks:
                if subtask["name"] == name:
                    subtask.update(kwargs)
                    if "order" in kwargs:
                        self.subtasks = sorted(self.subtasks, key=lambda x: x["order"])
                    break

    def reorder_subtasks(self, new_order):
        if self.subtasks and len(new_order) == len(self.subtasks):
            reordered = []
            for order in new_order:
                for subtask in self.subtasks:
                    if subtask["order"] == order:
                        reordered.append(subtask)
                        break
            self.subtasks = reordered

    def get_unique_identifier(self):
        return f"{self.name}_{self.due_datetime.strftime('%Y-%m-%d_%H:%M') if self.due_datetime else 'no_due_date'}"


class TaskList:
    def __init__(self, **kwargs):

        required_attributes = ['category', 'name']
        for attr in required_attributes:
            if attr not in kwargs or kwargs[attr] is None:
                raise ValueError(f"'{attr}' is a required attribute and cannot be None.")

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.id = kwargs.get("id")
        self.order = kwargs.get("order", 0)
        self.name = kwargs.get("name")
        self.description = kwargs.get("description", "")
        self.category = kwargs.get("category", "Uncategorized")
        self.notifications_enabled = kwargs.get("notifications_enabled", True)
        self.archived = kwargs.get("archived", False)
        self.in_trash = kwargs.get("in_trash", False)

        self.creation_date = self._parse_date(kwargs.get("creation_date"), "%Y-%m-%d")
        self.default_start_date = self._parse_date(kwargs.get("default_start_date"), "%Y-%m-%d")
        self.default_due_datetime = self._parse_date(kwargs.get("default_due_datetime"), "%Y-%m-%d %H:%M")
        self.default_time_of_day_preference = kwargs.get("default_time_of_day_preference", None)
        self.default_flexibility = kwargs.get("default_flexibility", None)
        self.default_effort_level = kwargs.get("default_effort_level", None)
        self.default_priority = kwargs.get("default_priority", None)
        self.default_preferred_work_days = kwargs.get("default_preferred_work_days", None)

        self.consider_in_schedule = kwargs.get("consider_in_schedule", True)

        self.sort_by_queue = kwargs.get("sort_by_queue", False)
        self.sort_by_stack = kwargs.get("sort_by_stack", False)
        self.sort_by_priority = kwargs.get("sort_by_priority", False)
        self.sort_by_due_datetime = kwargs.get("sort_by_due_datetime", False)
        self.sort_by_tags = kwargs.get("sort_by_tags", False)

        self.tasks = kwargs.get("tasks", [])
        self.progress = self.calculate_progress()

    @staticmethod
    def _parse_date(date_str, fmt):
        if date_str:
            return datetime.strptime(date_str, fmt)
        return None

    def calculate_progress(self):
        progress = 0
        if not self.tasks:
            return progress
        for task in self.tasks:
            progress += task.progress
        return progress

    def get_task_tags(self):
        task_tags = []
        # Collect all tags from the current tasks
        current_tags = set()
        for task in self.tasks:
            if isinstance(task.tags, list):
                current_tags.update(task.tags)

        # Remove leftover tags not present in any task
        task_tags = [tag for tag in task_tags if tag in current_tags]

        # Add new tags from current tasks
        for tag in current_tags:
            if tag not in task_tags:
                task_tags.append(tag)

        return task_tags

    def add_task_to_model_list(self, task):
        """
        Adds a task to the list while maintaining proper list_order.
        Sets the task's list_order if not specified, or adjusts other tasks if needed.
        """
        if not self.tasks:
            task.list_order = 0
            self.tasks = [task]
            return

        # If task.list_order is not set, append to end
        if task.list_order == 0:
            task.list_order = max(t.list_order for t in self.tasks) + 1
            self.tasks.append(task)
            return

        # If list_order is specified, shift existing tasks to make room
        for existing_task in self.tasks:
            if existing_task.list_order >= task.list_order:
                existing_task.list_order += 1

        self.tasks.append(task)
        # Sort tasks by list_order to maintain order
        self.tasks.sort(key=lambda t: t.list_order)

    def get_tasks(self):
        important_tasks = [task for task in self.tasks if
                           task.priority == 10 and task.status not in ["Completed", "Failed"]]
        other_tasks = [task for task in self.tasks if
                       task.priority < 10 and task.status not in ["Completed", "Failed"]]

        def safe_sort_key(task):
            return task.added_date_time or datetime.min

        if self.sort_by_queue:
            other_tasks.sort(key=safe_sort_key)
            important_tasks.sort(key=safe_sort_key)
            return important_tasks + other_tasks
        elif self.sort_by_stack:
            other_tasks.sort(key=safe_sort_key)
            important_tasks.sort(key=safe_sort_key)
            return list(reversed(important_tasks)) + list(reversed(other_tasks))
        return important_tasks + other_tasks

    def get_completed_tasks(self):
        completed_tasks = [task for task in self.tasks if task.status == "Completed"]

        def safe_sort_key(task):
            return task.added_date_time or datetime.min

        if self.sort_by_queue:
            return sorted(completed_tasks, key=safe_sort_key)
        elif self.sort_by_stack:
            sorted_completed_tasks = sorted(completed_tasks, key=safe_sort_key)
            return list(reversed(sorted_completed_tasks))
        return completed_tasks

    def get_tasks_filtered_by_tag(self, tag):
        important_tasks = [task for task in self.tasks if task.priority == 10 and task.has_tag(tag)]
        other_tasks = [task for task in self.tasks if not task.priority == 10 and task.has_tag(tag)]

        def safe_sort_key(task):
            return task.added_date_time or datetime.min

        if self.sort_by_queue:
            important_tasks.sort(key=safe_sort_key)
            other_tasks.sort(key=safe_sort_key)
            return important_tasks + other_tasks
        elif self.sort_by_stack:
            important_tasks.sort(key=safe_sort_key)
            other_tasks.sort(key=safe_sort_key)
            return list(reversed(important_tasks)) + list(reversed(other_tasks))
        return important_tasks + other_tasks

    def get_tasks_filter_priority(self):
        filtered_tasks = [task for task in self.tasks if task.status not in ["Completed", "Failed"]]

        def safe_priority_key(task):
            return task.priority if task.priority is not None else float('inf')

        return sorted(filtered_tasks, key=safe_priority_key)

    def disable_all_filters(self):
        self.sort_by_queue = False
        self.sort_by_stack = False
        self.sort_by_priority = False
        self.sort_by_due_datetime = False
        self.sort_by_tags = False

    def __str__(self):
        return '\n'.join(str(task) for task in self.tasks if not task.status == "Completed")


class TaskManager:
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_file = os.path.join(self.data_dir, "adm.db")
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.task_lists = self.load_task_lists()
        self.categories = self.load_categories()
        self.manage_recurring_tasks()

    def create_tables(self):
        create_categories_table = """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                `order` INTEGER,
                name TEXT NOT NULL UNIQUE
            );
            """

        create_task_lists_table = """
            CREATE TABLE IF NOT EXISTS task_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            `order` INTEGER,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            category TEXT NOT NULL,
            notifications_enabled BOOLEAN NOT NULL DEFAULT 1,
            archived BOOLEAN NOT NULL DEFAULT 0,
            in_trash BOOLEAN NOT NULL DEFAULT 0,
            creation_date TEXT,
            default_start_date TEXT,
            default_due_datetime TEXT,
            default_time_of_day_preference TEXT,
            default_flexibility TEXT,
            default_effort_level TEXT,
            default_priority INTEGER,
            default_preferred_work_days TEXT,
            consider_in_schedule BOOLEAN NOT NULL DEFAULT 1,
            sort_by_queue BOOLEAN NOT NULL DEFAULT 0,
            sort_by_stack BOOLEAN NOT NULL DEFAULT 0,
            sort_by_priority BOOLEAN NOT NULL DEFAULT 0,
            sort_by_due_datetime BOOLEAN NOT NULL DEFAULT 0,
            sort_by_tags BOOLEAN NOT NULL DEFAULT 0
        );
        """

        create_tasks_table = """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                notes TEXT,
                tags TEXT DEFAULT '[]',
                resources TEXT DEFAULT '[]',
                start_date TEXT,
                due_datetime TEXT,
                added_date_time TEXT,
                last_completed_date TEXT,
                list_order INTEGER DEFAULT 0,
                list_name TEXT NOT NULL,

                recurring BOOLEAN NOT NULL CHECK (recurring IN (0,1)) DEFAULT 0,
                recur_every TEXT,
                recurrences INTEGER DEFAULT 0,

                time_estimate REAL,
                time_logged REAL,
                count_required INTEGER,
                count_completed INTEGER,

                auto_chunk BOOLEAN NOT NULL CHECK (auto_chunk IN (0,1)) DEFAULT 1,
                min_chunk_size REAL,
                max_chunk_size REAL,

                manually_scheduled BOOLEAN NOT NULL CHECK (manually_scheduled IN (0,1)) DEFAULT 0,
                manually_scheduled_chunks TEXT DEFAULT '[]',

                assigned BOOLEAN NOT NULL CHECK (assigned IN (0,1)) DEFAULT 0,
                assigned_chunks TEXT DEFAULT '[]',
                
                single_chunk BOOLEAN NOT NULL CHECK (single_chunk IN (0,1)) DEFAULT 0,

                subtasks TEXT,
                dependencies TEXT,

                status TEXT DEFAULT 'Not Started',
                flexibility TEXT DEFAULT 'Flexible',
                effort_level TEXT DEFAULT 'Medium',
                priority INTEGER DEFAULT 0,
                previous_priority INTEGER DEFAULT 0,
                preferred_work_days TEXT DEFAULT '[]',
                time_of_day_preference TEXT,

                progress REAL DEFAULT 0,
                include_in_schedule BOOLEAN NOT NULL CHECK (include_in_schedule IN (0,1)) DEFAULT 0,
                global_weight REAL,

                FOREIGN KEY(list_name) REFERENCES task_lists(list_name) ON DELETE CASCADE
            );
        """

        try:
            cursor = self.conn.cursor()
            cursor.execute(create_categories_table)
            print("Categories table created successfully.")
            cursor.execute(create_task_lists_table)
            print("Task lists table created successfully.")
            cursor.execute(create_tasks_table)
            print("Tasks table created successfully.")
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def load_task_lists(self):
        task_lists = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM task_lists")
        rows = cursor.fetchall()
        for row in rows:
            task_list_data = dict(row)
            task_list_data["notifications_enabled"] = bool(task_list_data["notifications_enabled"])
            task_list_data["archived"] = bool(task_list_data["archived"])
            task_list_data["in_trash"] = bool(task_list_data["in_trash"])
            task_list_data["consider_in_schedule"] = bool(task_list_data["consider_in_schedule"])
            task_list_data["sort_by_queue"] = bool(task_list_data["sort_by_queue"])
            task_list_data["sort_by_stack"] = bool(task_list_data["sort_by_stack"])
            task_list_data["sort_by_priority"] = bool(task_list_data["sort_by_priority"])
            task_list_data["sort_by_due_datetime"] = bool(task_list_data["sort_by_due_datetime"])
            task_list_data["sort_by_tags"] = bool(task_list_data["sort_by_tags"])
            task_list_data["default_preferred_work_days"] = json.loads(
                task_list_data["default_preferred_work_days"]) if task_list_data.get(
                "default_preferred_work_days") else None
            task_list_data["tasks"] = self.get_tasks_by_list_name(task_list_data["name"])
            task_list = TaskList(**task_list_data)
            task_lists.append(task_list)
        return task_lists

    def get_tasks_by_list_name(self, list_name):
        tasks = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE list_name=?", (list_name,))
        rows = cursor.fetchall()
        for row in rows:
            task_data = dict(row)
            task_data["tags"] = json.loads(task_data["tags"]) if task_data.get("tags") else []
            task_data["resources"] = json.loads(task_data["resources"]) if task_data.get("resources") else []
            task_data["recur_every"] = json.loads(task_data["recur_every"]) if task_data.get("recur_every") else None
            task_data["subtasks"] = json.loads(task_data["subtasks"]) if task_data.get("subtasks") else []
            task_data["dependencies"] = json.loads(task_data["dependencies"]) if task_data.get("dependencies") else []
            task_data["recurring"] = bool(task_data["recurring"])
            task_data['include_in_schedule'] = bool(task_data['include_in_schedule'])
            task_data["auto_chunk"] = bool(task_data["auto_chunk"])
            task_data["manually_scheduled"] = bool(task_data["manually_scheduled"])
            task_data["assigned"] = bool(task_data["assigned"])
            task_data["single_chunk"] = bool(task_data["single_chunk"])

            task = Task(**task_data)
            tasks.append(task)
        return tasks

    def load_categories(self):
        categories = {
            "Uncategorized": {
                "order": float('inf'),  # Ensures Uncategorized appears last
                "task_lists": []
            }
        }

        cursor = self.conn.cursor()

        # Load categories from database
        cursor.execute("SELECT * FROM categories ORDER BY `order`")
        category_rows = cursor.fetchall()

        # Create category entries
        for category_row in category_rows:
            category_order = category_row["order"]
            category_name = category_row["name"]

            categories[category_name] = {
                "order": category_order,
                "task_lists": []
            }

        # Distribute task lists to their categories
        for task_list in self.task_lists:
            category_name = task_list.category if task_list.category else "Uncategorized"

            # If category doesn't exist, fallback to Uncategorized
            if category_name not in categories:
                print(f"Category {category_name} not found. Falling back to Uncategorized.")
                category_name = "Uncategorized"

            # Ensure the task list is valid before adding
            if isinstance(task_list, TaskList):
                categories[category_name]["task_lists"].append(task_list)
            else:
                print(f"Invalid task list object: {task_list}")

        # Sort task lists within each category
        for category_name, category_data in categories.items():
            if isinstance(category_data, dict) and "task_lists" in category_data:
                category_data["task_lists"].sort(key=lambda tl: getattr(tl, "order", float('inf')))
            else:
                print(f"Invalid category data for {category_name}: {category_data}")

        # Ensure Uncategorized remains even if empty
        if "Uncategorized" not in categories:
            categories["Uncategorized"] = {
                "order": float('inf'),
                "task_lists": []
            }

        return categories

    def get_category_tasklist_names(self):
        try:
            cursor = self.conn.cursor()

            # Fetch categories
            cursor.execute("SELECT id, name FROM categories ORDER BY `order`")
            categories = cursor.fetchall()

            # Initialize dictionary
            category_tasklists = {category[1]: [] for category in categories}  # category[1] is 'name'
            category_tasklists["Uncategorized"] = []  # Ensure "Uncategorized" always exists

            # Fetch task lists and their associated categories
            cursor.execute("""
                SELECT task_lists.name AS task_list_name, categories.name AS category_name
                FROM task_lists
                LEFT JOIN categories ON task_lists.category = categories.name
                ORDER BY task_lists.`order`
            """)
            task_lists = cursor.fetchall()

            # Populate category_tasklists
            for task_list_name, category_name in task_lists:
                category_name = category_name or "Uncategorized"  # Handle uncategorized task lists
                category_tasklists.setdefault(category_name, []).append(task_list_name)

            return category_tasklists
        except sqlite3.Error as e:
            print(f"Database error while fetching categories and task lists: {e}")
            return {}

    def add_category(self, category_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT MAX(`order`) FROM categories")
            max_order = cursor.fetchone()[0]
            new_order = max_order + 1 if max_order is not None else 1
            cursor.execute("INSERT INTO categories (name, `order`) VALUES (?, ?)", (category_name, new_order))
            self.conn.commit()
            self.categories[category_name] = {
                "order": new_order,
                "task_lists": []
            }
        except sqlite3.IntegrityError as e:
            print(f"Error adding category '{category_name}': {e}")
        except Exception as e:
            print(f"Unexpected error while adding category '{category_name}': {e}")

    def remove_category(self, category_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM categories WHERE name=?", (category_name,))
            self.conn.commit()
            self.categories = self.load_categories()
        except sqlite3.IntegrityError as e:
            print(f"Error removing category '{category_name}': {e}")
        except Exception as e:
            print(f"Unexpected error while removing category '{category_name}': {e}")

    def rename_category(self, old_name, new_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE categories SET name=? WHERE name=?", (new_name, old_name))
            self.conn.commit()
            self.categories = self.load_categories()
        except sqlite3.IntegrityError as e:
            print(f"Error renaming category from '{old_name}' to '{new_name}': {e}")
        except Exception as e:
            print(f"Unexpected error while renaming category from '{old_name}' to '{new_name}': {e}")

    def update_category_order(self, category_name, new_order):
        cursor = self.conn.cursor()

        try:
            cursor.execute("UPDATE categories SET `order` = ? WHERE name = ?", (new_order, category_name))
            self.conn.commit()

            if category_name in self.categories:
                self.categories[category_name]["order"] = new_order
        except sqlite3.Error as e:
            print(f"Failed to update order for category '{category_name}': {e}")

    def add_task_list(self, task_list: TaskList):
        try:
            cursor = self.conn.cursor()

            # Determine the order value
            new_order = max((t.order for t in self.task_lists), default=0) + 1

            cursor.execute("""
                INSERT INTO task_lists (
                    `order`, name, description, category, 
                    notifications_enabled, archived, in_trash, 
                    creation_date, default_start_date, default_due_datetime, 
                    default_time_of_day_preference, default_flexibility, 
                    default_effort_level, default_priority, 
                    default_preferred_work_days, consider_in_schedule, 
                    sort_by_queue, sort_by_stack, sort_by_priority, 
                    sort_by_due_datetime, sort_by_tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_order,
                task_list.name,
                task_list.description,
                task_list.category,
                int(task_list.notifications_enabled),
                int(task_list.archived),
                int(task_list.in_trash),
                task_list.creation_date.strftime("%Y-%m-%d") if task_list.creation_date else None,
                task_list.default_start_date.strftime("%Y-%m-%d") if task_list.default_start_date else None,
                task_list.default_due_datetime.strftime("%Y-%m-%d %H:%M") if task_list.default_due_datetime else None,
                task_list.default_time_of_day_preference,
                task_list.default_flexibility,
                task_list.default_effort_level,
                task_list.default_priority,
                json.dumps(task_list.default_preferred_work_days) if task_list.default_preferred_work_days else None,
                int(task_list.consider_in_schedule),
                int(task_list.sort_by_queue),
                int(task_list.sort_by_stack),
                int(task_list.sort_by_priority),
                int(task_list.sort_by_due_datetime),
                int(task_list.sort_by_tags)
            ))

            self.conn.commit()

            self.task_lists.append(task_list)
            self.categories[task_list.category]["task_lists"].append(task_list)

        except sqlite3.Error as e:
            print(f"Database error while adding task_list: {e}")
        except Exception as e:
            print(f"Unexpected error while adding task list: {e}")

    def remove_task_list(self, name):
        try:
            cursor = self.conn.cursor()

            cursor.execute("DELETE FROM task_lists WHERE name = ?", (name,))
            if cursor.rowcount == 0:
                raise ValueError(f"Task list '{name}' does not exist.")

            self.conn.commit()

            # Remove from existing task_lists list
            self.task_lists[:] = [tl for tl in self.task_lists if tl.name != name]

            # Update categories in-place
            for category in self.categories.values():
                category["task_lists"][:] = [tl for tl in category["task_lists"] if tl.name != name]

        except sqlite3.Error as e:
            print(f"Database error while removing task list '{name}': {e}")
        except Exception as e:
            print(f"Unexpected error while removing task list '{name}': {e}")

    def update_task_list(self, task_list: TaskList):
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                UPDATE task_lists
                SET 
                    `order` = ?, 
                    description = ?, 
                    category = ?, 
                    notifications_enabled = ?, 
                    archived = ?, 
                    in_trash = ?, 
                    creation_date = ?, 
                    default_start_date = ?, 
                    default_due_datetime = ?, 
                    default_time_of_day_preference = ?, 
                    default_flexibility = ?, 
                    default_effort_level = ?, 
                    default_priority = ?, 
                    default_preferred_work_days = ?, 
                    consider_in_schedule = ?, 
                    sort_by_queue = ?, 
                    sort_by_stack = ?, 
                    sort_by_priority = ?, 
                    sort_by_due_datetime = ?, 
                    sort_by_tags = ?
                WHERE name = ?
            """, (
                task_list.order,
                task_list.description,
                task_list.category,
                int(task_list.notifications_enabled),
                int(task_list.archived),
                int(task_list.in_trash),
                task_list.creation_date.strftime("%Y-%m-%d") if task_list.creation_date else None,
                task_list.default_start_date.strftime("%Y-%m-%d") if task_list.default_start_date else None,
                task_list.default_due_datetime.strftime("%Y-%m-%d %H:%M") if task_list.default_due_datetime else None,
                task_list.default_time_of_day_preference,
                task_list.default_flexibility,
                task_list.default_effort_level,
                task_list.default_priority,
                json.dumps(task_list.default_preferred_work_days) if task_list.default_preferred_work_days else None,
                int(task_list.consider_in_schedule),
                int(task_list.sort_by_queue),
                int(task_list.sort_by_stack),
                int(task_list.sort_by_priority),
                int(task_list.sort_by_due_datetime),
                int(task_list.sort_by_tags),
                task_list.name
            ))

            if cursor.rowcount == 0:
                raise ValueError(f"Task list '{task_list.name}' does not exist.")

            self.conn.commit()

            # Update category references if category changed
            old_task_list = next((tl for tl in self.task_lists if tl.id == task_list.id), None)
            if old_task_list and old_task_list.category != task_list.category:
                # Remove from old category
                if old_task_list.category in self.categories:
                    self.categories[old_task_list.category]["task_lists"][:] = [
                        tl for tl in self.categories[old_task_list.category]["task_lists"]
                        if tl.id != task_list.id
                    ]

                # Add to new category
                if task_list.category in self.categories:
                    self.categories[task_list.category]["task_lists"].append(task_list)
                    # Re-sort category task lists
                    self.categories[task_list.category]["task_lists"].sort(key=lambda tl: tl.order)

            # Update task list reference in self.task_lists
            for i, tl in enumerate(self.task_lists):
                if tl.id == task_list.id:
                    self.task_lists[i] = task_list
                    break

        except sqlite3.Error as e:
            print(f"Database error while updating task list '{task_list.name}': {e}")
        except Exception as e:
            print(f"Unexpected error while updating task list '{task_list.name}': {e}")

    def update_task_list_order(self, task_list_name, new_order):
        try:
            cursor = self.conn.cursor()

            # Update the order in the database
            cursor.execute("UPDATE task_lists SET `order` = ? WHERE name = ?", (new_order, task_list_name))
            if cursor.rowcount == 0:
                raise ValueError(f"Task list '{task_list_name}' does not exist.")
            self.conn.commit()

            # Update the in-memory representation
            updated = False
            for category in self.categories.values():
                for task_list in category["task_lists"]:
                    if task_list.name == task_list_name:
                        task_list.order = new_order
                        updated = True
                        break
                if updated:
                    break

            if not updated:
                raise ValueError(f"Task list '{task_list_name}' not found in loaded categories.")

        except sqlite3.Error as e:
            print(f"Database error while updating task list order: {e}")
        except Exception as e:
            print(f"Unexpected error while updating task list order: {e}")

    def add_task(self, task: Task):
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT INTO tasks (
                    name,
                    description,
                    notes,
                    tags,
                    resources,
                    start_date,
                    due_datetime,
                    added_date_time,
                    last_completed_date,
                    list_order,
                    list_name,

                    recurring,
                    recur_every,
                    recurrences,
                    time_estimate,
                    time_logged,
                    count_required,
                    count_completed,

                    auto_chunk,
                    min_chunk_size,
                    max_chunk_size,

                    manually_scheduled,
                    manually_scheduled_chunks,

                    assigned,
                    assigned_chunks,
                    
                    single_chunk,

                    subtasks,
                    dependencies,

                    status,
                    flexibility,
                    effort_level,
                    priority,
                    previous_priority,
                    preferred_work_days,
                    time_of_day_preference,
                    progress,
                    include_in_schedule,
                    global_weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.name,
                task.description,
                task.notes,
                json.dumps(task.tags) if task.tags else None,
                json.dumps(task.resources) if task.resources else None,
                task.start_date.strftime("%Y-%m-%d") if task.start_date else None,
                task.due_datetime.strftime("%Y-%m-%d %H:%M") if task.due_datetime else None,
                task.added_date_time.strftime("%Y-%m-%d %H:%M") if task.added_date_time else None,
                task.last_completed_date.strftime("%Y-%m-%d %H:%M") if task.last_completed_date else None,
                task.list_order,
                task.list_name,

                int(task.recurring),
                json.dumps(task.recur_every) if task.recur_every else None,
                task.recurrences,
                task.time_estimate,
                task.time_logged,
                task.count_required,
                task.count_completed,

                int(task.auto_chunk),
                task.min_chunk_size,
                task.max_chunk_size,

                int(task.manually_scheduled),
                json.dumps(task.manually_scheduled_chunks) if task.manually_scheduled_chunks else None,

                int(task.assigned),
                json.dumps(task.assigned_chunks) if task.assigned_chunks else None,

                int(task.single_chunk),

                json.dumps(task.subtasks) if task.subtasks else None,
                json.dumps(task.dependencies) if task.dependencies else None,

                task.status,
                task.flexibility,
                task.effort_level,
                task.priority,
                task.previous_priority,
                json.dumps(task.preferred_work_days) if task.preferred_work_days else None,
                json.dumps(task.time_of_day_preference) if task.time_of_day_preference else None,
                task.progress,
                int(task.include_in_schedule),
                task.global_weight
            ))

            self.conn.commit()
            task.id = cursor.lastrowid

            for task_list in self.task_lists:
                if task_list.name == task.list_name:
                    task_list.add_task_to_model_list(task)
                    break

            print(f"Task '{task.name}' successfully added with ID: {task.id}")
        except sqlite3.Error as e:
            print(f"Database error while adding task '{task.name}': {e}")
        except Exception as e:
            print(f"Unexpected error while adding task '{task.name}': {e}")

    def remove_task(self, task):
        """
        Removes a task from the database.

        :param task: Can be either a Task object or task ID
        """
        try:
            cursor = self.conn.cursor()
            task_id = task.id if isinstance(task, Task) else task

            if task_id is None:
                raise ValueError("Task has no ID")

            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

            if cursor.rowcount == 0:
                raise ValueError(f"Task with ID {task_id} does not exist.")

            self.conn.commit()
            list_name = task_obj.list_name
            for task_list in self.task_lists:
                if task_list.name == list_name:
                    task_list.tasks[:] = [t for t in task_list.tasks if t.id != task_id]
                    break
            print(f"Task '{task.name if isinstance(task, Task) else task_id}' successfully removed.")

        except sqlite3.Error as e:
            print(f"Database error while removing task: {e}")
        except Exception as e:
            print(f"Unexpected error while removing task: {e}")

    def update_task(self, task: Task):
        try:
            cursor = self.conn.cursor()

            # Store old task list name before update to check if it changed
            old_task = self.get_task(task.id)
            old_list_name = old_task.list_name if old_task else None

            cursor.execute("""
                UPDATE tasks
                SET
                    name = ?,
                    description = ?,
                    notes = ?,
                    tags = ?,
                    resources = ?,
                    start_date = ?,
                    due_datetime = ?,
                    added_date_time = ?,
                    last_completed_date = ?,
                    list_order = ?,
                    list_name = ?,

                    recurring = ?,
                    recur_every = ?,
                    recurrences = ?,

                    time_estimate = ?,
                    time_logged = ?,
                    count_required = ?,
                    count_completed = ?,

                    auto_chunk = ?,
                    min_chunk_size = ?,
                    max_chunk_size = ?,

                    manually_scheduled = ?,
                    manually_scheduled_chunks = ?,

                    assigned = ?,
                    assigned_chunks = ?,
                    
                    single_chunk = ?,

                    subtasks = ?,
                    dependencies = ?,

                    status = ?,
                    flexibility = ?,
                    effort_level = ?,
                    priority = ?,
                    previous_priority = ?,
                    preferred_work_days = ?,
                    time_of_day_preference = ?,

                    progress = ?,
                    include_in_schedule = ?,
                    global_weight = ?

                WHERE id = ?
            """, (
                task.name,
                task.description,
                task.notes,
                json.dumps(task.tags) if task.tags else None,
                json.dumps(task.resources) if task.resources else None,
                task.start_date.isoformat() if task.start_date else None,
                task.due_datetime.isoformat() if task.due_datetime else None,
                task.added_date_time.isoformat() if task.added_date_time else None,
                task.last_completed_date.isoformat() if task.last_completed_date else None,
                task.list_order,
                task.list_name,

                int(task.recurring),
                json.dumps(task.recur_every) if task.recur_every else None,
                task.recurrences,

                task.time_estimate,
                task.time_logged,
                task.count_required,
                task.count_completed,

                int(task.auto_chunk),
                task.min_chunk_size,
                task.max_chunk_size,

                int(task.manually_scheduled),
                json.dumps(task.manually_scheduled_chunks) if task.manually_scheduled_chunks else None,

                int(task.assigned),
                json.dumps(task.assigned_chunks) if task.assigned_chunks else None,

                int(task.single_chunk),

                json.dumps(task.subtasks) if task.subtasks else None,
                json.dumps(task.dependencies) if task.dependencies else None,

                task.status,
                task.flexibility,
                task.effort_level,
                task.priority,
                task.previous_priority,
                json.dumps(task.preferred_work_days) if task.preferred_work_days else None,
                task.time_of_day_preference,

                task.progress,
                int(task.include_in_schedule),
                task.global_weight,

                task.id
            ))

            if cursor.rowcount == 0:
                raise ValueError(f"Task with ID {task.id} does not exist.")

            self.conn.commit()

            # Update task list references in-place
            if old_list_name:
                # If the task moved to a different list
                if old_list_name != task.list_name:
                    # Remove from old list
                    old_task_list = next((tl for tl in self.task_lists if tl.name == old_list_name), None)
                    if old_task_list:
                        old_task_list.tasks[:] = [t for t in old_task_list.tasks if t.id != task.id]

                    # Add to new list
                    new_task_list = next((tl for tl in self.task_lists if tl.name == task.list_name), None)
                    if new_task_list:
                        new_task_list.tasks.append(task)
                else:
                    # Update task in the same list
                    task_list = next((tl for tl in self.task_lists if tl.name == task.list_name), None)
                    if task_list:
                        for i, t in enumerate(task_list.tasks):
                            if t.id == task.id:
                                task_list.tasks[i] = task
                                break
        except sqlite3.Error as e:
            print(f"Database error while updating task with ID {task.id}: {e}")
        except Exception as e:
            print(f"Unexpected error while updating task with ID {task.id}: {e}")

    def get_task(self, task_id):
        """
        Fetches a task by its ID.
        :param task_id: ID of the task to fetch.
        :return: Task object if found, None otherwise.
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task_row = cursor.fetchone()

            if not task_row:
                return None

            task_data = dict(task_row)
            task_data["tags"] = json.loads(task_data["tags"]) if task_data.get("tags") else []
            task_data["resources"] = json.loads(task_data["resources"]) if task_data.get("resources") else []
            task_data["recur_every"] = json.loads(task_data["recur_every"]) if task_data.get("recur_every") else None
            task_data["subtasks"] = json.loads(task_data["subtasks"]) if task_data.get("subtasks") else []
            task_data["dependencies"] = json.loads(task_data["dependencies"]) if task_data.get("dependencies") else []
            task_data["recurring"] = bool(task_data["recurring"])
            task_data["include_in_schedule"] = bool(task_data["include_in_schedule"])
            task_data["auto_chunk"] = bool(task_data["auto_chunk"])
            task_data["manually_scheduled"] = bool(task_data["manually_scheduled"])
            task_data["assigned"] = bool(task_data["assigned"])
            task_data["single_chunk"] = bool(task_data["single_chunk"])

            return Task(**task_data)

        except sqlite3.Error as e:
            print(f"Error fetching task by ID {task_id}: {e}")
            return None

    def manage_recurring_tasks(self):
        try:
            cursor = self.conn.cursor()

            # Fetch all recurring tasks
            cursor.execute("SELECT * FROM tasks WHERE recurring = 1")
            rows = cursor.fetchall()

            weekday_mapping = {
                "mon": 0, "monday": 0,
                "tue": 1, "tuesday": 1,
                "wed": 2, "wednesday": 2,
                "thu": 3, "thursday": 3,
                "fri": 4, "friday": 4,
                "sat": 5, "saturday": 5,
                "sun": 6, "sunday": 6,
            }

            for row in rows:
                task_data = dict(row)
                task_data["tags"] = json.loads(task_data["tags"]) if task_data.get("tags") else []
                task_data["resources"] = json.loads(task_data["resources"]) if task_data.get("resources") else []
                task_data["recur_every"] = json.loads(task_data["recur_every"]) if task_data.get(
                    "recur_every") else None
                task_data["subtasks"] = json.loads(task_data["subtasks"]) if task_data.get("subtasks") else []
                task_data["dependencies"] = json.loads(task_data["dependencies"]) if task_data.get(
                    "dependencies") else []
                task_data["recurring"] = bool(task_data["recurring"])
                task_data["include_in_schedule"] = bool(task_data["include_in_schedule"])

                task = Task(**task_data)

                if task.status != "Completed":
                    continue

                # Handle recurrence based on recur_every
                if isinstance(task.recur_every, int):
                    next_due = (task.last_completed_date or datetime.now()) + timedelta(days=task.recur_every)
                elif isinstance(task.recur_every, list):
                    today = datetime.now().date()
                    today_weekday = today.weekday()
                    days_to_next = min(
                        (weekday_mapping[day.lower()] - today_weekday) % 7
                        for day in task.recur_every
                    )
                    next_due = datetime.combine(today + timedelta(days=days_to_next), task.due_datetime.time())
                else:
                    continue

                if next_due <= datetime.now():
                    # Reset task status and attributes
                    task.status = "Not Started"
                    task.time_logged = 0 if task.time_estimate else task.time_logged
                    task.count_completed = 0 if task.count_required else task.count_completed
                    task.recurrences += 1
                    task.due_datetime = next_due

                    self.update_task(task)

        except sqlite3.Error as e:
            print(f"Database error while managing recurring tasks: {e}")
        except Exception as e:
            print(f"Unexpected error while managing recurring tasks: {e}")

    def get_task_list_categories(self):
        return list(self.categories.keys())

    def get_all_active_task_tags(self):
        tags = set()
        for task_list in self.task_lists:
            if not task_list.archived and not task_list.in_trash:
                for task in task_list.tasks:
                    tags.update(task.tags)
        return list(tags)

    def get_active_tasks(self):
        active_tasks = []
        for task_list in self.task_lists:
            for task in task_list.tasks:
                if task.status != "Completed":
                    active_tasks.append(task)
        return active_tasks

    def get_task_list_category_name(self, task_list_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT category FROM task_lists WHERE name = ?", (task_list_name,))
        result = cursor.fetchone()
        if result:
            return result["category"]
        return None

    def __del__(self):
        self.conn.close()
