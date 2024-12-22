import os
import sqlite3
import json
import uuid
from datetime import datetime, time, timedelta
import random

from core.task_manager import TaskListManager

DAY_START = time(4, 0)  # Day starts at 4 AM
DAY_DURATION = timedelta(hours=23, minutes=59, seconds=59)


# This means the day ends at 4 AM next day.
# For clarity, the "day" is from 4:00 AM of 'date' to 4:00 AM of 'date' + 1 day.


class TimeBlock:
    def __init__(self,
                 block_id=uuid.uuid4().int,
                 task_manager_instance=None,
                 name="",
                 start_time=None,
                 end_time=None,
                 days_of_week=None,
                 include_categories=None,
                 include_tasks=None,
                 ignore_tasks=None,
                 ignore_categories=None,
                 block_type="empty",
                 color=None):
        """
        block_type can be "user" or "empty" or "unavailable".
        user-defined = "user" and auto-filled = "empty".
        """
        self.id = block_id
        self.task_manager_instance = task_manager_instance if task_manager_instance is not None else None
        self.name = name

        # Validate start_time and end_time
        if start_time is not None and not isinstance(start_time, time):
            raise TypeError("start_time must be a datetime.time object")
        if end_time is not None and not isinstance(end_time, time):
            raise TypeError("end_time must be a datetime.time object")

        self.start_time = start_time
        self.end_time = end_time

        if color:
            if isinstance(color, (list, tuple)) and len(color) == 3 and all(isinstance(c, int) for c in color):
                self.color = tuple(color)
            else:
                raise ValueError("Color must be a tuple of three integers (R, G, B)")
        elif block_type == "empty":
            self.color = (47, 47, 47)  # Grey
        elif block_type == "unavailable":
            self.color = (231, 131, 97)  # Salmon
        else:
            self.color = tuple(random.randint(0, 255) for _ in range(3))  # random color

        # Validate days_of_week
        if isinstance(days_of_week, list):
            self.days_of_week = days_of_week
        else:
            self.days_of_week = []

        # Validate include_categories
        self.include_categories = include_categories if include_categories is not None else []

        # Validate include_task_ids
        if include_tasks is not None:
            if not isinstance(include_tasks, list) or not all(isinstance(task_id, int) for task_id in include_tasks):
                raise TypeError("include_tasks must be a list of integers")
            self.include_task_ids = include_tasks
        else:
            self.include_task_ids = []

        # Validate ignore_task_ids
        if ignore_tasks is not None:
            if not isinstance(ignore_tasks, list) or not all(isinstance(task_id, int) for task_id in ignore_tasks):
                raise TypeError("ignore_tasks must be a list of integers")
            self.ignore_task_ids = ignore_tasks
        else:
            self.ignore_task_ids = []

        self.ignore_categories = ignore_categories if ignore_categories is not None else []
        self.block_type = block_type

        # Store task objects for the block
        self.tasks = []
        if self.block_type != "empty" and self.block_type != "unavailable":
            self.load_tasks()

    def load_tasks(self):
        if self.task_manager_instance is not None:
            # Load tasks from included categories
            for category in self.include_categories:
                self.tasks.extend(self.task_manager_instance.get_tasks_by_category(category))

            # Add tasks by ID if not already included
            for task_id in self.include_task_ids:
                task = self.task_manager_instance.get_task(task_id)
                if task and task not in self.tasks:
                    self.tasks.append(task)

            # Remove tasks by ignore IDs
            self.tasks = [task for task in self.tasks if task.id not in self.ignore_task_ids]

            # Remove tasks from ignored categories
            self.tasks = [task for task in self.tasks if
                          not any(cat in self.ignore_categories for cat in task.categories)]
        else:
            raise ValueError("task_manager_instance must be defined")

    def add_include_task(self, task_id):
        """
        Adds a task ID to the include_task_ids list after validating the type.
        :param task_id: The ID of the task to include.
        """
        if not isinstance(task_id, int):
            raise TypeError("Task ID must be an integer")
        if task_id not in self.include_task_ids:
            self.include_task_ids.append(task_id)

    def add_ignore_task(self, task_id):
        """
        Adds a task ID to the ignore_task_ids list after validating the type.
        :param task_id: The ID of the task to ignore.
        """
        if not isinstance(task_id, int):
            raise TypeError("Task ID must be an integer")
        if task_id not in self.ignore_task_ids:
            self.ignore_task_ids.append(task_id)

    def remove_include_task(self, task_id):
        """
        Removes a task ID from the include_task_ids list.
        :param task_id: The ID of the task to remove.
        """
        if not isinstance(task_id, int):
            raise TypeError("Task ID must be an integer")
        if task_id in self.include_task_ids:
            self.include_task_ids.remove(task_id)

    def remove_ignore_task(self, task_id):
        """
        Removes a task ID from the ignore_task_ids list.
        :param task_id: The ID of the task to remove.
        """
        if not isinstance(task_id, int):
            raise TypeError("Task ID must be an integer")
        if task_id in self.ignore_task_ids:
            self.ignore_task_ids.remove(task_id)

    def get_include_task_ids(self):
        """
        Retrieves the list of included task IDs.
        :return: List of integers representing included task IDs.
        """
        return self.include_task_ids

    def get_ignore_task_ids(self):
        """
        Retrieves the list of ignored task IDs.
        :return: List of integers representing ignored task IDs.
        """
        return self.ignore_task_ids

    def add_include_category(self, category_name):
        """
        Adds a category name to the include_categories list after validating the type.
        :param category_name: The name of the category to include.
        """
        if not isinstance(category_name, str):
            raise TypeError("Category name must be a string")
        if category_name not in self.include_categories:
            self.include_categories.append(category_name)

    def remove_include_category(self, category_name):
        """
        Removes a category name from the include_categories list.
        :param category_name: The name of the category to remove.
        """
        if not isinstance(category_name, str):
            raise TypeError("Category name must be a string")
        if category_name in self.include_categories:
            self.include_categories.remove(category_name)

    def get_include_categories(self):
        """
        Retrieves the list of included categories.
        :return: List of strings representing included category names.
        """
        return self.include_categories

    # Functions for `ignore_categories`
    def add_ignore_category(self, category_name):
        """
        Adds a category name to the ignore_categories list after validating the type.
        :param category_name: The name of the category to ignore.
        """
        if not isinstance(category_name, str):
            raise TypeError("Category name must be a string")
        if category_name not in self.ignore_categories:
            self.ignore_categories.append(category_name)

    def remove_ignore_category(self, category_name):
        """
        Removes a category name from the ignore_categories list.
        :param category_name: The name of the category to remove.
        """
        if not isinstance(category_name, str):
            raise TypeError("Category name must be a string")
        if category_name in self.ignore_categories:
            self.ignore_categories.remove(category_name)

    def get_ignore_categories(self):
        """
        Retrieves the list of ignored categories.
        :return: List of strings representing ignored category names.
        """
        return self.ignore_categories

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_time.strftime("%H:%M") if self.start_time else None,
            "end_time": self.end_time.strftime("%H:%M") if self.end_time else None,
            "days_of_week": self.days_of_week,
            "include_categories": self.include_categories,
            "include_task_ids": self.include_task_ids,
            "ignore_task_ids": self.ignore_task_ids,
            "ignore_categories": self.ignore_categories,
            "block_type": self.block_type,
            "color": self.color,
            "tasks": [task.id for task in self.tasks]
        }


class ScheduleManager:
    def __init__(self, task_manager: TaskListManager):
        self.task_manager = task_manager
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_file = os.path.join(self.data_dir, "adm.db")
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS time_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id INTEGER,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    task_id INTEGER,
                    name TEXT DEFAULT '',
                    include_tasks TEXT DEFAULT '[]',
                    include_categories TEXT DEFAULT '[]',
                    ignore_tasks TEXT DEFAULT '[]',
                    ignore_categories TEXT DEFAULT '[]',
                    days_of_week TEXT DEFAULT '[]',
                    block_type TEXT DEFAULT 'empty',
                    color TEXT DEFAULT '',
                    FOREIGN KEY (schedule_id) REFERENCES day_schedule (id),
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)

    def update_timeblock(self, timeblock):
        if not isinstance(timeblock, TimeBlock):
            raise TypeError("Argument must be a TimeBlock instance")

        with self.conn:
            self.conn.execute("""
                UPDATE time_blocks
                SET 
                    start_time = ?,
                    end_time = ?,
                    name = ?,
                    include_tasks = ?,
                    include_categories = ?,
                    ignore_tasks = ?,
                    ignore_categories = ?,
                    days_of_week = ?,
                    block_type = ?,
                    color = ?
                WHERE id = ?
            """, (
                timeblock.start_time.strftime("%H:%M") if timeblock.start_time else None,
                timeblock.end_time.strftime("%H:%M") if timeblock.end_time else None,
                timeblock.name,
                json.dumps(timeblock.include_task_ids),
                json.dumps(timeblock.include_categories),
                json.dumps(timeblock.ignore_task_ids),
                json.dumps(timeblock.ignore_categories),
                json.dumps(timeblock.days_of_week),
                timeblock.block_type,
                ','.join(map(str, timeblock.color)) if timeblock.color else "",
                timeblock.id
            ))

    def get_timeblock(self, timeblock_id):
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM time_blocks WHERE id = ?", (timeblock_id,)).fetchone()
        if row:
            color = tuple(map(int, row["color"].split(','))) if row["color"] else None
            return TimeBlock(
                block_id=row["id"],
                task_manager_instance=self.task_manager,
                name=row["name"],
                start_time=datetime.strptime(row["start_time"], "%H:%M").time() if row["start_time"] else None,
                end_time=datetime.strptime(row["end_time"], "%H:%M").time() if row["end_time"] else None,
                include_categories=json.loads(row["include_categories"]),
                include_tasks=json.loads(row["include_tasks"]),
                ignore_tasks=json.loads(row["ignore_tasks"]),
                ignore_categories=json.loads(row["ignore_categories"]),
                days_of_week=json.loads(row["days_of_week"]),
                block_type=row["block_type"],
                color=color
            )
        return None

    def add_timeblock(self, timeblock):
        """
        Adds a new TimeBlock instance to the database, creating/retrieving the
        corresponding day_schedule entry based on date_str.
        :param timeblock: A TimeBlock instance.
        :param date_str: The date (YYYY-MM-DD) for which this block is scheduled.
        """
        if not isinstance(timeblock, TimeBlock):
            raise TypeError("Argument must be a TimeBlock instance")
        color_str = ','.join(map(str, timeblock.color)) if timeblock.color else ""

        with self.conn:
            self.conn.execute("""
                INSERT INTO time_blocks (
                    start_time, end_time, name, 
                    include_tasks, include_categories, ignore_tasks, 
                    ignore_categories, days_of_week, block_type, color
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timeblock.start_time.strftime("%H:%M") if timeblock.start_time else None,
                timeblock.end_time.strftime("%H:%M") if timeblock.end_time else None,
                timeblock.name,
                json.dumps(timeblock.include_task_ids),
                json.dumps(timeblock.include_categories),
                json.dumps(timeblock.ignore_task_ids),
                json.dumps(timeblock.ignore_categories),
                json.dumps(timeblock.days_of_week),
                timeblock.block_type,
                color_str
            ))
            timeblock.id = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_day_schedule(self, date_str):
        return DaySchedule(date_str, self.conn, self.task_manager)

    def get_week_schedule(self, year, week_number):
        # Empty shell
        return []

    def get_month_schedule(self, year, month):
        # Empty shell
        return []


class DaySchedule:
    def __init__(self, date_str, conn, task_manager):
        self.date_str = date_str
        self.conn = conn
        self.task_manager = task_manager
        self.day_start = self._get_day_start()
        self.day_end = self.day_start + DAY_DURATION
        self.user_blocks = self._load_user_defined_blocks()

    def _get_day_start(self):
        date_obj = datetime.strptime(self.date_str, "%Y-%m-%d").date()
        return datetime.combine(date_obj, DAY_START)

    def _parse_time(self, time_str):
        return datetime.strptime(time_str, "%H:%M").time()

    def _load_user_defined_blocks(self):
        query = """
            SELECT tb.* FROM time_blocks tb
            ORDER BY tb.start_time
        """
        rows = self.conn.execute(query).fetchall()

        # today's day of week (Monday=0, Sunday=6)
        today_day_of_week = datetime.strptime(self.date_str, "%Y-%m-%d").weekday()

        blocks = []
        for row in rows:
            start_t = self._parse_time(row["start_time"])
            end_t = self._parse_time(row["end_time"])
            include_tasks = json.loads(row["include_tasks"]) if row["include_tasks"] else []
            include_categories = json.loads(row["include_categories"]) if row["include_categories"] else []
            ignore_tasks = json.loads(row["ignore_tasks"]) if row["ignore_tasks"] else []
            ignore_categories = json.loads(row["ignore_categories"]) if row["ignore_categories"] else []
            days_of_week = json.loads(row["days_of_week"]) if row["days_of_week"] else []
            block_type = row["block_type"]
            color = tuple(map(int, row["color"].split(','))) if row["color"] else None

            # Create the TimeBlock (no block_id passed so it uses random uuid)
            tb = TimeBlock(
                task_manager_instance=self.task_manager,
                name=row["name"],
                start_time=start_t,
                end_time=end_t,
                days_of_week=days_of_week,
                include_categories=include_categories,
                include_tasks=include_tasks,
                ignore_tasks=ignore_tasks,
                ignore_categories=ignore_categories,
                block_type=block_type,
                color=color
            )

            # Only add if today is in the block's days_of_week or days_of_week is empty (means all days)
            if not tb.days_of_week or today_day_of_week in tb.days_of_week:
                blocks.append(tb)

        return blocks

    def _compare_times(self, t1, t2):
        """
        Compare two times t1 and t2 within a schedule that runs from 4am to 4am the next day.

        Returns:
           -1 if t1 < t2
            0 if t1 == t2
            1  if t1 > t2
        """
        # The "day" starts at 4 AM (DAY_START) and ends at 4 AM next day.
        # If the time is before 4 AM, we assume it belongs to "the next day's" cycle.
        # This method interprets t1, t2 accordingly.

        day_start_time = time(4, 0)
        base_date = datetime.today().date()

        # Convert times to datetimes
        dt1 = datetime.combine(base_date, t1)
        dt2 = datetime.combine(base_date, t2)

        # If time is before 4 AM, treat it as belonging to the next day (+1 day)
        if t1 < day_start_time:
            dt1 += timedelta(days=1)
        if t2 <= day_start_time:
            dt2 += timedelta(days=1)

        # Now do a straightforward comparison
        if dt1 < dt2:
            return -1
        elif dt1 == dt2:
            return 0
        else:
            return 1

    def get_full_day_schedule(self):
        user_blocks = sorted(self.user_blocks, key=lambda b: b.start_time)
        day_start_time = self.day_start.time()
        final_end_time = self.day_end.time()  # This is 4am next day

        # If no user blocks, return one big empty block for the full 24-hour period
        if not user_blocks:
            return [TimeBlock(
                task_manager_instance=self.task_manager,
                name="Empty Block",
                start_time=day_start_time,
                end_time=final_end_time,
                block_type="empty"
            )]

        full_schedule = []
        current_start = day_start_time

        for ub in user_blocks:
            # Fill the gap before this user block if it starts after current_start
            if self._compare_times(current_start, ub.start_time) < 0:
                full_schedule.append(TimeBlock(
                    task_manager_instance=self.task_manager,
                    name="Empty Block",
                    start_time=current_start,
                    end_time=ub.start_time,
                    block_type="empty"
                ))

            # Add the user-defined block
            full_schedule.append(ub)
            current_start = ub.end_time

        # After processing all user blocks, fill the gap until final_end_time if any
        if self._compare_times(current_start, final_end_time) < 0:
            full_schedule.append(TimeBlock(
                task_manager_instance=self.task_manager,
                name="Empty Block",
                start_time=current_start,
                end_time=final_end_time,
                block_type="empty"
            ))

        return full_schedule
