import os
import sqlite3
import json
import uuid
from datetime import datetime, date, time, timedelta
import random
from core.task_manager import *


class ScheduleSettings:
    def __init__(self, db_path='data/adm.db'):
        self.db_path = db_path
        self.create_table()
        self.load_settings()

    def create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_start TEXT,
                ideal_sleep_duration REAL,
                overtime_flexibility TEXT,
                hours_of_day_available REAL,
                peak_productivity_start TEXT,
                peak_productivity_end TEXT,
                off_peak_start TEXT,
                off_peak_end TEXT,
                task_notifications INTEGER,
                task_status_popup_frequency INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def load_settings(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM schedule_settings LIMIT 1")
        row = cursor.fetchone()
        if row:
            self.day_start = self.parse_time(row[1])
            self.ideal_sleep_duration = row[2]
            self.overtime_flexibility = row[3]
            self.hours_of_day_available = row[4]
            self.peak_productivity_hours = (
                self.parse_time(row[5]),
                self.parse_time(row[6]),
            )
            self.off_peak_hours = (
                self.parse_time(row[7]),
                self.parse_time(row[8]),
            )
            self.task_notifications = bool(row[9])
            self.task_status_popup_frequency = row[10]
        else:
            self.day_start = time(4, 0)
            self.ideal_sleep_duration = 8.0
            self.overtime_flexibility = "auto"
            self.hours_of_day_available = float(24.0 - self.ideal_sleep_duration)
            self.peak_productivity_hours = (time(17, 0), time(19, 0))
            self.off_peak_hours = (time(22, 0), time(6, 0))
            self.task_notifications = True
            self.task_status_popup_frequency = 20
            self.save_settings()
        conn.close()

    def save_settings(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedule_settings")
        cursor.execute('''
            INSERT INTO schedule_settings (
                day_start, ideal_sleep_duration, overtime_flexibility,
                hours_of_day_available, peak_productivity_start, peak_productivity_end,
                off_peak_start, off_peak_end, task_notifications, task_status_popup_frequency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.day_start.strftime("%H:%M"),
            self.ideal_sleep_duration,
            self.overtime_flexibility,
            self.hours_of_day_available,
            self.peak_productivity_hours[0].strftime("%H:%M"),
            self.peak_productivity_hours[1].strftime("%H:%M"),
            self.off_peak_hours[0].strftime("%H:%M"),
            self.off_peak_hours[1].strftime("%H:%M"),
            int(self.task_notifications),
            self.task_status_popup_frequency
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def parse_time(time_str):
        if time_str:
            hours, minutes = map(int, time_str.split(':'))
            return time(hours, minutes)
        return None

    def set_day_start(self, new_time):
        self.day_start = new_time
        self.save_settings()

    def set_ideal_sleep_duration(self, duration):
        self.ideal_sleep_duration = duration
        self.save_settings()

    def set_overtime_flexibility(self, flexibility):
        self.overtime_flexibility = flexibility
        self.save_settings()

    def set_hours_of_day_available(self, hours):
        self.hours_of_day_available = hours
        self.save_settings()

    def set_peak_productivity_hours(self, start, end):
        self.peak_productivity_hours = (start, end)
        self.save_settings()

    def set_off_peak_hours(self, start, end):
        self.off_peak_hours = (start, end)
        self.save_settings()

    def set_task_notifications(self, enabled):
        self.task_notifications = enabled
        self.save_settings()

    def set_task_status_popup_frequency(self, frequency):
        self.task_status_popup_frequency = frequency
        self.save_settings()


# Example of how the dictionaries might look:
# schedule = {
#     'monday': (time(8, 0), time(9, 0)),
#     'thursday': (time(17, 0), time(18, 0))
# }
# list_categories = {
#     'include': ['Work', 'Personal'],
#     'exclude': ['Errands']
# }
# task_tags = {
#     'include': ['urgent', 'high-priority'],
#     'exclude': ['low-priority', 'optional']
# }
# tasks = {
#     'include': [101, 102],
#     'exclude': [202, 305]
# }
class TimeBlock:
    def __init__(
            self,
            block_id=None,
            name="",
            schedule=None,
            list_categories=None,
            task_tags=None,
            tasks=None,
            block_type="user_defined",
            color=None
    ):
        self.id = block_id if block_id else uuid.uuid4().int
        self.name = name
        self.schedule = schedule if schedule else {}
        self.list_categories = list_categories if list_categories else {"include": [], "exclude": []}
        self.task_tags = task_tags if task_tags else {"include": [], "exclude": []}
        self.tasks_dict = tasks if tasks else {"include": [], "exclude": []}
        self.block_type = block_type
        if color and isinstance(color, tuple) and len(color) == 3 and all(isinstance(c, int) for c in color):
            self.color = color
        elif block_type == "system_defined":
            self.color = (47, 47, 47)
        elif block_type == "unavailable":
            self.color = (231, 131, 97)
        else:
            self.color = tuple(random.randint(0, 255) for _ in range(3))
        self.tasks = []
        # if self.block_type not in ("system_defined", "unavailable"):
        #     self.load_tasks()

        self.start_time = None
        self.end_time = None
        self.duration = None

    def add_task_if_time_available(self, task_to_add: Task):
        if self.duration is None:
            return False

        if duration - sum(task.time_estimate for task in self.tasks) < task_to_add.time_estimate:
            return False

        self.tasks.append(task_to_add)
        return True


class ScheduleManager:
    def __init__(self, task_manager_instance: TaskManager):
        self.task_manager_instance = task_manager_instance
        self.schedule_settings = ScheduleSettings()

        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_file = os.path.join(self.data_dir, "adm.db")
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

        # Weighting coefficients
        self.alpha = 0.4
        self.beta = 0.3
        self.gamma = 0.1
        self.delta = 0.2
        self.epsilon = 0.2
        self.zeta = 0.3
        self.eta = 0.2
        self.theta = 0.1

        self.time_blocks = []
        self.load_time_blocks()
        self.update_task_global_weights()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS time_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT DEFAULT '',
                    schedule TEXT DEFAULT '{}',
                    list_categories TEXT DEFAULT '{"include": [], "exclude": []}',
                    task_tags TEXT DEFAULT '{"include": [], "exclude": []}',
                    tasks TEXT DEFAULT '{"include": [], "exclude": []}',
                    block_type TEXT DEFAULT 'system_defined',
                    color TEXT DEFAULT '',
                    FOREIGN KEY (schedule_id) REFERENCES day_schedule (id)
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_date TEXT NOT NULL,
                    time_blocks TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def load_time_blocks(self):
        """
        Load time blocks from the database and create TimeBlock objects.
        Converts stored JSON strings back into Python dictionaries.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM time_blocks")
            rows = cursor.fetchall()

            self.time_blocks = []

            for row in rows:
                # Convert JSON strings back to dictionaries
                schedule = json.loads(row['schedule'])
                list_categories = json.loads(row['list_categories'])
                task_tags = json.loads(row['task_tags'])
                tasks = json.loads(row['tasks'])

                # Convert color string to tuple
                color_str = row['color']
                if color_str:
                    color = tuple(map(int, color_str.strip('()').split(',')))
                else:
                    color = None

                # Create TimeBlock object
                time_block = TimeBlock(
                    block_id=row['id'],
                    name=row['name'],
                    schedule=schedule,
                    list_categories=list_categories,
                    task_tags=task_tags,
                    tasks=tasks,
                    block_type=row['block_type'],
                    color=color
                )

                # Convert schedule times from strings to time objects
                for day, times in time_block.schedule.items():
                    if isinstance(times, tuple) and len(times) == 2:
                        start_str, end_str = times
                        if isinstance(start_str, str) and isinstance(end_str, str):
                            try:
                                # Parse time strings in format "HH:MM"
                                start_time = datetime.strptime(start_str, "%H:%M").time()
                                end_time = datetime.strptime(end_str, "%H:%M").time()
                                time_block.schedule[day] = (start_time, end_time)
                            except ValueError:
                                print(f"Warning: Invalid time format for {day} in block {time_block.id}")

                self.time_blocks.append(time_block)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
        except Exception as e:
            print(f"Error loading time blocks: {e}")
        finally:
            cursor.close()

    def add_time_block(self, time_block: TimeBlock):
        """
        Add a TimeBlock object to memory and persist it to the database.

        Args:
            time_block (TimeBlock): The TimeBlock object to add

        Returns:
            int: The ID of the newly added time block
        """
        try:
            # Convert time objects in schedule to string format for storage
            schedule_for_storage = {}
            for day, times in time_block.schedule.items():
                if isinstance(times, tuple) and len(times) == 2:
                    start_time, end_time = times
                    if isinstance(start_time, time) and isinstance(end_time, time):
                        schedule_for_storage[day] = (
                            start_time.strftime("%H:%M"),
                            end_time.strftime("%H:%M")
                        )
                    else:
                        schedule_for_storage[day] = times

            # Convert color tuple to string
            color_str = str(time_block.color) if time_block.color else ""

            # Insert into database
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO time_blocks (
                    name, 
                    schedule, 
                    list_categories, 
                    task_tags, 
                    tasks, 
                    block_type, 
                    color
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                time_block.name,
                json.dumps(schedule_for_storage),
                json.dumps(time_block.list_categories),
                json.dumps(time_block.task_tags),
                json.dumps(time_block.tasks_dict),
                time_block.block_type,
                color_str
            ))

            # Commit the transaction
            self.conn.commit()

            # Update the time block's ID with the one assigned by the database
            time_block.id = cursor.lastrowid

            # Add to in-memory list
            self.time_blocks.append(time_block)

            cursor.close()
            return time_block.id

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            raise
        except Exception as e:
            print(f"Error adding time block: {e}")
            self.conn.rollback()
            raise

    def remove_time_block(self, block_id: int):
        """
        Remove a TimeBlock from memory and the database.

        Args:
            block_id (int): The ID of the time block to remove

        Returns:
            bool: True if successful, False if block not found

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            # First check if the block exists in memory
            block_to_remove = None
            for block in self.time_blocks:
                if block.id == block_id:
                    block_to_remove = block
                    break

            if not block_to_remove:
                print(f"Time block with ID {block_id} not found in memory")
                return False

            # Remove from database
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM time_blocks WHERE id = ?", (block_id,))

            # Check if any rows were affected
            if cursor.rowcount == 0:
                print(f"Time block with ID {block_id} not found in database")
                return False

            # Commit the transaction
            self.conn.commit()

            # Remove from memory
            self.time_blocks.remove(block_to_remove)

            cursor.close()
            return True

        except sqlite3.Error as e:
            print(f"Database error while removing time block: {e}")
            self.conn.rollback()
            raise
        except ValueError as e:
            print(f"Error removing time block from memory: {e}")
            self.conn.rollback()
            raise
        except Exception as e:
            print(f"Unexpected error removing time block: {e}")
            self.conn.rollback()
            raise

    def update_time_block(self, time_block: TimeBlock):
        """
        Update an existing TimeBlock in both memory and database.

        Args:
            time_block (TimeBlock): The TimeBlock object with updated values

        Returns:
            bool: True if successful, False if block not found

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            # First check if the block exists in memory
            existing_block = None
            for idx, block in enumerate(self.time_blocks):
                if block.id == time_block.id:
                    existing_block = idx
                    break

            if existing_block is None:
                print(f"Time block with ID {time_block.id} not found")
                return False

            # Convert time objects in schedule to string format for storage
            schedule_for_storage = {}
            for day, times in time_block.schedule.items():
                if isinstance(times, tuple) and len(times) == 2:
                    start_time, end_time = times
                    if isinstance(start_time, time) and isinstance(end_time, time):
                        schedule_for_storage[day] = (
                            start_time.strftime("%H:%M"),
                            end_time.strftime("%H:%M")
                        )
                    else:
                        schedule_for_storage[day] = times

            # Convert color tuple to string
            color_str = str(time_block.color) if time_block.color else ""

            # Update database
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE time_blocks 
                SET name = ?,
                    schedule = ?,
                    list_categories = ?,
                    task_tags = ?,
                    tasks = ?,
                    block_type = ?,
                    color = ?
                WHERE id = ?
            """, (
                time_block.name,
                json.dumps(schedule_for_storage),
                json.dumps(time_block.list_categories),
                json.dumps(time_block.task_tags),
                json.dumps(time_block.tasks_dict),
                time_block.block_type,
                color_str,
                time_block.id
            ))

            # Check if any rows were affected
            if cursor.rowcount == 0:
                print(f"Time block with ID {time_block.id} not found in database")
                return False

            # Commit the transaction
            self.conn.commit()

            # Update in-memory list
            self.time_blocks[existing_block] = time_block

            cursor.close()
            return True

        except sqlite3.Error as e:
            print(f"Database error while updating time block: {e}")
            self.conn.rollback()
            raise
        except Exception as e:
            print(f"Error updating time block: {e}")
            self.conn.rollback()
            raise

    def task_weight_formula(self, task, max_added_time, max_time_estimate):
        priority_weight = self.alpha * task.priority

        if task.due_datetime:
            days_left = max(1, (task.due_datetime - datetime.now()).total_seconds() / (24 * 3600))
            urgency_weight = self.beta * (1 / days_left)
        else:
            urgency_weight = self.beta * 0.5

        flexibility_map = {"Strict": 0, "Flexible": 1, "Very Flexible": 2}
        flexibility_weight = self.gamma * flexibility_map.get(task.flexibility, 1)

        if task.added_date_time:
            added_time_weight = self.delta * (
                    (datetime.now() - task.added_date_time).total_seconds() / max_added_time
            )
        else:
            added_time_weight = self.delta * 0.5

        effort_map = {"Low": 1, "Medium": 2, "High": 3}
        effort_weight = self.epsilon * effort_map.get(task.effort_level, 2)

        if task.time_estimate and max_time_estimate > 0:
            time_estimate_weight = self.zeta * (task.time_estimate / max_time_estimate)
        else:
            time_estimate_weight = 0

        if task.time_logged and task.time_estimate:
            time_logged_weight = self.eta * (task.time_logged / task.time_estimate)
        else:
            time_logged_weight = 0

        return (
                priority_weight + urgency_weight + flexibility_weight + added_time_weight +
                effort_weight + time_estimate_weight + time_logged_weight + workday_preference_weight
        )

    def update_task_global_weights(self):

        tasks = self.task_manager_instance.get_active_tasks()

        max_added_time = max(
            (datetime.now() - task.added_date_time).total_seconds()
            for task in tasks if task.added_date_time
        ) if any(task.added_date_time for task in tasks) else 1

        max_time_estimate = max(task.time_estimate for task in tasks if task.time_estimate) or 1

        total_weight = sum(
            self.task_weight_formula(task, max_added_time, max_time_estimate) for task in tasks
        )

        if total_weight == 0:
            return

        for task in tasks:
            global_weight = (
                    self.task_weight_formula(task, max_added_time, max_time_estimate) / total_weight
            )
            task.global_weight = global_weight
            self.task_manager_instance.update_task(task)

        self.conn.commit()

    def get_day_schedule(self, date):
        schedule = self.load_schedule(date)
        if schedule:
            return schedule
        else:
            return DaySchedule(self, date, self.time_blocks, self.task_manager_instance, self.schedule_settings)


class DaySchedule:
    def __init__(self, schedule_manager_instance, date, time_blocks, task_manager_instance, schedule_settings):
        """
        :param date: A datetime.date object for which the schedule is generated
        :param time_blocks: A list of TimeBlock objects (user_defined + system_defined)
        :param task_manager_instance: The TaskManager used to fetch tasks from the DB
        :param schedule_settings: An instance of ScheduleSettings for configuring sleep, peak hours, etc.
        """
        self.date = date
        self.time_blocks = time_blocks
        self.task_manager_instance = task_manager_instance
        self.schedule_manager_instance = schedule_manager_instance
        self.schedule_settings = schedule_settings
        self.time_blocks = self.generate_schedule()

    def generate_schedule(self):
        day_start = datetime.combine(self.date, self.schedule_settings.day_start)
        sleep_duration = timedelta(hours=self.schedule_settings.ideal_sleep_duration)
        target_day_str = self.date.strftime('%A').lower()

        # Filter user-defined blocks that apply to this day
        user_blocks = [
            block for block in self.time_blocks
            if block.schedule and target_day_str in block.schedule and block.block_type == 'user_defined'
        ]
        user_blocks.sort(key=lambda b: b.schedule[target_day_str][0])  # Sort by start time

        final_blocks = []
        current_time = day_start

        # (1) Insert user-defined blocks first
        for block in user_blocks:
            block_start_dt = datetime.combine(self.date, block.schedule[target_day_str][0])
            block_end_dt = datetime.combine(self.date, block.schedule[target_day_str][1])

            block.start_time = block_start_dt.time()
            block.end_time = block_end_dt.time()
            final_blocks.append(block)

        # (2) Calculate sleep block timing
        sleep_end = day_start
        ideal_sleep_start = sleep_end - sleep_duration

        # Find the last user-defined block that overlaps with our ideal sleep time
        overlapping_block = None
        for block in reversed(final_blocks):
            block_end = datetime.combine(self.date, block.end_time)
            if block_end > ideal_sleep_start:
                overlapping_block = block
                break

        # Adjust sleep start time if there's an overlap
        if overlapping_block:
            actual_sleep_start = datetime.combine(self.date, overlapping_block.end_time)
            adjusted_sleep_duration = (sleep_end - actual_sleep_start).total_seconds() / 3600  # in hours
        else:
            actual_sleep_start = ideal_sleep_start
            adjusted_sleep_duration = self.schedule_settings.ideal_sleep_duration

        # (3) Now fill gaps between user-defined blocks up until sleep start
        filled_blocks = []
        current_time = day_start

        for block in sorted(final_blocks, key=lambda b: b.start_time):
            block_start_dt = datetime.combine(self.date, block.start_time)

            # If there's a gap before this block, add a system-defined block
            if current_time < block_start_dt:
                gap_block = TimeBlock(
                    block_id=None,
                    name="Unscheduled",
                    schedule={target_day_str: (current_time.time(), block_start_dt.time())},
                    block_type="system_defined",
                    color=(200, 200, 200)
                )
                gap_block.start_time = current_time.time()
                gap_block.end_time = block_start_dt.time()
                filled_blocks.append(gap_block)

            filled_blocks.append(block)
            current_time = datetime.combine(self.date, block.end_time)

        # Fill gap between last user block and sleep start if exists
        if current_time < actual_sleep_start:
            gap_block = TimeBlock(
                block_id=None,
                name="Unscheduled",
                schedule={target_day_str: (current_time.time(), actual_sleep_start.time())},
                block_type="system_defined",
                color=(200, 200, 200)
            )
            gap_block.start_time = current_time.time()
            gap_block.end_time = actual_sleep_start.time()
            filled_blocks.append(gap_block)

        # (4) Finally add the sleep block
        sleep_block = TimeBlock(
            block_id=None,
            name=f"Sleep ({adjusted_sleep_duration:.1f}h)",
            schedule={target_day_str: (actual_sleep_start.time(), sleep_end.time())},
            block_type="unavailable",
            color=(173, 216, 230)
        )
        sleep_block.start_time = actual_sleep_start.time()
        sleep_block.end_time = sleep_end.time()
        filled_blocks.append(sleep_block)

        return filled_blocks

    def _populate_tasks(self):
        tasks = self.task_manager_instance.get_active_tasks()

        total_hours_available = self.schedule_settings.hours_of_day_available
        total_hours_scheduled = 0.0

        scheduled_tasks = []

        # remove scheduled tasks
        tasks = [task for task in tasks if task.schedule_weight is None]

        # populate time blocks
        for task in tasks:
            user_defined = False
            if total_hours_scheduled >= total_hours_available:
                break
            elif (total_hours_scheduled - total_hours_available) < task.time_estimate:
                continue
            for time_block in self.time_blocks:
                if time_block.block_type == "unavailable" or time_block.block_type == "system_defined":
                    continue
                if time_block.block_type == "user_defined":
                    if task.id in time_block.tasks["exclude"]:
                        continue
                    elif task.id in time_block.tasks["include"]:
                        if not time_block.add_task_if_time_available(task):
                            continue
                        scheduled_tasks.append(task)
                        total_hours_scheduled += task.time_estimate
                        user_defined = True
                        break
                    if any(tag in time_block.task_tags["exclude"] for tag in task.tags):
                        continue
                    elif any(tag in time_block.task_tags["include"] for tag in task.tags):
                        if not time_block.add_task_if_time_available(task):
                            continue
                        scheduled_tasks.append(task)
                        total_hours_scheduled += task.time_estimate
                        user_defined = True
                        break
                    if self.task_manager_instance.get_task_list_category_name(task.list_name) in \
                            time_block.list_categories["exclude"]:
                        continue
                    elif self.task_manager_instance.get_task_list_category_name(task.list_name) in \
                            time_block.list_categories["include"]:
                        if not time_block.add_task_if_time_available(task):
                            continue
                        scheduled_tasks.append(task)
                        total_hours_scheduled += task.time_estimate
                        user_defined = True
                        break
                if not user_defined:
                    for time_block in self.time_blocks:
                        if time_block.block_type == "unavailable":
                            continue
                        elif time_block.block_type == "user_defined":
                            if not time_block.list_categories["include"]:
                                if task.id in time_block.tasks["exclude"]:
                                    continue
                                else:
                                    if not time_block.task_tags["include"]:
                                        if any(tag in time_block.task_tags["exclude"] for tag in task.tags):
                                            continue
                                        if not time_block.add_task_if_time_available(task):
                                            continue
                                        scheduled_tasks.append(task)
                                        total_hours_scheduled += task.time_estimate
                                        user_defined = True
                                        break
                        if time_block.block_type == "system_defined":
                            if not time_block.add_task_if_time_available(task):
                                continue
                            scheduled_tasks.append(task)
                            total_hours_scheduled += task.time_estimate
                            user_defined = True
                            break
