import os
import sqlite3
import json
import uuid
from datetime import datetime, date, time, timedelta
import random
from ortools.sat.python import cp_model
import math

from core.task_manager import *


def time_to_string(t: time) -> str:
    return t.strftime("%H:%M")


def convert_times_in_schedule(schedule_dict: dict) -> dict:
    new_schedule = {}
    for day, times in schedule_dict.items():
        # Each day has a list/tuple of [start_time, end_time]
        # Convert each to string if necessary.
        converted = []
        for t in times:
            if isinstance(t, time):
                converted.append(time_to_string(t))
            else:
                converted.append(t)
        new_schedule[day] = converted
    return new_schedule


def parse_time_schedule(schedule_data: dict) -> dict:
    """
    Convert each day's [start_time_str, end_time_str] into [start_time_obj, end_time_obj].
    """
    parsed_schedule = {}
    for day, time_pair in schedule_data.items():
        if not isinstance(time_pair, (list, tuple)) or len(time_pair) != 2:
            continue
        start_str, end_str = time_pair

        # Parse only if they're strings, otherwise keep them if they are already time objects.
        if isinstance(start_str, str):
            start_time = datetime.strptime(start_str, "%H:%M").time()
        else:
            start_time = start_str

        if isinstance(end_str, str):
            end_time = datetime.strptime(end_str, "%H:%M").time()
        else:
            end_time = end_str

        parsed_schedule[day] = [start_time, end_time]

    return parsed_schedule


class ScheduleSettings:
    def __init__(self, db_path='data/adm.db'):
        self.db_path = db_path
        self.create_table()
        self.load_settings()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
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
                    task_status_popup_frequency INTEGER,
                    alpha REAL,
                    beta REAL,
                    gamma REAL,
                    delta REAL,
                    epsilon REAL,
                    zeta REAL,
                    eta REAL,
                    theta REAL,
                    K INTEGER,
                    T_q INTEGER,
                    C INTEGER
                )
            ''')

    def load_settings(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schedule_settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                self.day_start = self.parse_time(row["day_start"])
                self.ideal_sleep_duration = row["ideal_sleep_duration"]
                self.overtime_flexibility = row["overtime_flexibility"]
                self.hours_of_day_available = row["hours_of_day_available"]
                self.peak_productivity_hours = (
                    self.parse_time(row["peak_productivity_start"]), self.parse_time(row["peak_productivity_end"]))
                self.off_peak_hours = (self.parse_time(row["off_peak_start"]), self.parse_time(row["off_peak_end"]))
                self.task_notifications = bool(row["task_notifications"])
                self.task_status_popup_frequency = row["task_status_popup_frequency"]

                # Load weighting coefficients
                self.alpha = row["alpha"]
                self.beta = row["beta"]
                self.gamma = row["gamma"]
                self.delta = row["delta"]
                self.epsilon = row["epsilon"]
                self.zeta = row["zeta"]
                self.eta = row["eta"]
                self.theta = row["theta"]
                self.K = row["K"]
                self.T_q = row["T_q"]
                self.C = row["C"]

            else:
                self.set_default_settings()

    def set_default_settings(self):
        self.day_start = time(4, 0)
        self.ideal_sleep_duration = 8.0
        self.overtime_flexibility = "auto"
        self.hours_of_day_available = 24.0 - self.ideal_sleep_duration
        self.peak_productivity_hours = (time(17, 0), time(19, 0))
        self.off_peak_hours = (time(22, 0), time(6, 0))
        self.task_notifications = True
        self.task_status_popup_frequency = 20

        # Default weighting coefficients
        self.alpha = 0.4
        self.beta = 0.3
        self.gamma = 0.1
        self.delta = 0.2
        self.epsilon = 0.2
        self.zeta = 0.3
        self.eta = 0.2
        self.theta = 0.1
        self.K = 100
        self.T_q = 3600
        self.C = 1000

        self.save_settings()

    def save_settings(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedule_settings")
            cursor.execute('''
                INSERT INTO schedule_settings (
                    day_start, ideal_sleep_duration, overtime_flexibility,
                    hours_of_day_available, peak_productivity_start, peak_productivity_end,
                    off_peak_start, off_peak_end, task_notifications, task_status_popup_frequency,
                    alpha, beta, gamma, delta, epsilon, zeta, eta, theta, K, T_q, C
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                self.task_status_popup_frequency,
                self.alpha, self.beta, self.gamma, self.delta, self.epsilon,
                self.zeta, self.eta, self.theta, self.K, self.T_q, self.C
            ))
            conn.commit()

    @staticmethod
    def parse_time(time_str):
        if time_str:
            hours, minutes = map(int, time_str.split(':'))
            return time(hours, minutes)
        return None

    # === Setters for configuring values ===
    def set_alpha(self, value):
        self.alpha = value
        self.save_settings()

    def set_beta(self, value):
        self.beta = value
        self.save_settings()

    def set_gamma(self, value):
        self.gamma = value
        self.save_settings()

    def set_delta(self, value):
        self.delta = value
        self.save_settings()

    def set_epsilon(self, value):
        self.epsilon = value
        self.save_settings()

    def set_zeta(self, value):
        self.zeta = value
        self.save_settings()

    def set_eta(self, value):
        self.eta = value
        self.save_settings()

    def set_theta(self, value):
        self.theta = value
        self.save_settings()

    def set_K(self, value):
        self.K = value
        self.save_settings()

    def set_T_q(self, value):
        self.T_q = value
        self.save_settings()

    def set_C(self, value):
        self.C = value
        self.save_settings()

    # Example usage of existing settings
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


class TimeBlock:
    def __init__(self, block_id=None, name="", date=None,
                 list_categories=None, task_tags=None,
                 block_type="user_defined", color=None):
        self.id = block_id if block_id else uuid.uuid4().int
        self.name = name
        self.date = date
        self.list_categories = list_categories if list_categories else {"include": [], "exclude": []}
        self.task_tags = task_tags if task_tags else {"include": [], "exclude": []}
        self.block_type = block_type
        if color and isinstance(color, tuple) and len(color) == 3 and all(isinstance(c, int) for c in color):
            self.color = color
        elif block_type == "system_defined":
            self.color = (47, 47, 47)
        elif block_type == "unavailable":
            self.color = (231, 131, 97)
        else:
            self.color = tuple(random.randint(0, 255) for _ in range(3))
        self.task_chunks = {}
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.buffer_ratio = 0.0

    def get_available_time(self):
        used_time = sum(info["chunk"].size for info in self.task_chunks.values())
        if self.duration is None:
            return 0

        if self.date and self.start_time and self.end_time:
            now = datetime.now()
            block_start = datetime.combine(self.date, self.start_time)
            block_end = (block_start + timedelta(hours=self.duration))

            if block_start <= now <= block_end:
                hours_passed = (now - block_start).total_seconds() / 3600
            else:
                hours_passed = 0
        else:
            hours_passed = 0

        return max(0, ((self.duration - hours_passed - used_time) * (1 - self.buffer_ratio)))

    def add_chunk(self, chunk, rating):
        cid = chunk.id
        self.task_chunks[cid] = {"chunk": chunk, "rating": rating}

    def remove_chunk(self, chunk):
        id = chunk.id
        if id in [task_chunk["chunk"].id for task_chunk in self.task_chunks]:
            del self.task_chunks[id]


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

        # Load weighting coefficients from settings
        self.alpha = self.schedule_settings.alpha
        self.beta = self.schedule_settings.beta
        self.gamma = self.schedule_settings.gamma
        self.delta = self.schedule_settings.delta
        self.epsilon = self.schedule_settings.epsilon
        self.zeta = self.schedule_settings.zeta
        self.eta = self.schedule_settings.eta
        self.theta = self.schedule_settings.theta

        # Load fixed constants from settings
        self.K = self.schedule_settings.K
        self.T_q = self.schedule_settings.T_q
        self.C = self.schedule_settings.C

        self.time_blocks = []
        self.load_time_blocks()

        self.active_tasks = self.task_manager_instance.get_active_tasks()
        self.update_task_global_weights()

        self.day_schedules = self.load_day_schedules()

        self.estimate_daily_buffer_ratios()

        self.chunks = self.chunk_tasks()

        self.generate_schedule()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS time_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT DEFAULT '',
                    schedule TEXT DEFAULT '{}',
                    list_categories TEXT DEFAULT '{"include": [], "exclude": []}',
                    task_tags TEXT DEFAULT '{"include": [], "exclude": []}',
                    color TEXT DEFAULT '',
                    unavailable INTEGER DEFAULT 0
                )
            """)

    def load_time_blocks(self):
        """
        Load time blocks from the database and store them in-memory as dictionaries.
        The schedule field is a JSON string representing a dictionary of day(s) of week and time ranges.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM time_blocks")
            rows = cursor.fetchall()

            self.time_blocks = []  # clear the in-memory structure

            for row in rows:
                # Parse JSON fields
                schedule_json = row["schedule"]
                if schedule_json:
                    schedule_dict = json.loads(schedule_json)
                    # Convert any string times into actual time objects
                    # schedule_dict = parse_time_schedule(schedule_dict)
                else:
                    schedule_dict = {}
                list_categories = json.loads(row["list_categories"]) if row["list_categories"] else {
                    "include": [], "exclude": []
                }
                task_tags = json.loads(row["task_tags"]) if row["task_tags"] else {"include": [], "exclude": []}

                # Convert color string to a tuple
                color_str = row["color"]
                if color_str:
                    try:
                        color = tuple(map(int, color_str.strip("()").split(",")))
                    except Exception:
                        color = None
                else:
                    color = None

                block = {
                    "id": row["id"],
                    "name": row["name"],
                    "schedule": schedule_dict,  # e.g., {"wed": ["09:00", "10:00"]}
                    "list_categories": list_categories,
                    "task_tags": task_tags,
                    "color": color,
                    "unavailable": int(row["unavailable"]) if row["unavailable"] else 0
                }
                self.time_blocks.append(block)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
        except Exception as e:
            print(f"Error loading time blocks: {e}")
        finally:
            cursor.close()

    def add_time_block(self, time_block: dict):
        """
        Insert a new time block into the database and add it to the in-memory structure.
        'time_block' is a dictionary with keys:
          name, schedule, list_categories, task_tags, color, unavailable.
        """
        try:
            # Convert each field to JSON or string as needed
            if "schedule" in time_block:
                schedule_dict = time_block["schedule"]
                # Convert any datetime.time objects to strings
                schedule_dict = convert_times_in_schedule(schedule_dict)
                schedule_json = json.dumps(schedule_dict)
            else:
                schedule_json = "{}"
            list_cats_json = json.dumps(
                time_block["list_categories"]) if "list_categories" in time_block else json.dumps({
                "include": [], "exclude": []
            })
            task_tags_json = json.dumps(time_block["task_tags"]) if "task_tags" in time_block else json.dumps({
                "include": [], "exclude": []
            })

            color_str = ""
            if "color" in time_block and time_block["color"]:
                color_str = str(time_block["color"])  # e.g. "(255, 200, 200)"

            unavailable = time_block.get("unavailable", 0)

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO time_blocks (
                    name,
                    schedule,
                    list_categories,
                    task_tags,
                    color,
                    unavailable
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                time_block["name"],
                schedule_json,
                list_cats_json,
                task_tags_json,
                color_str,
                unavailable
            ))
            self.conn.commit()

            new_id = cursor.lastrowid
            time_block["id"] = new_id

            self.time_blocks.append(time_block)

            cursor.close()
            return new_id

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            raise
        except Exception as e:
            print(f"Error adding time block: {e}")
            self.conn.rollback()
            raise

    def remove_time_block(self, block_name: int):
        """
        Remove a time block from both the database and the in-memory structure.
        """
        try:
            block_to_remove = None
            for block in self.time_blocks:
                if block["name"] == block_name:
                    block_to_remove = block
                    break

            if not block_to_remove:
                print(f"Time block with ID {block_name} not found in memory")
                return False

            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM time_blocks WHERE name = ?", (block_name,))
            if cursor.rowcount == 0:
                print(f"Time block with ID {block_name} not found in database")
                return False
            self.conn.commit()

            self.time_blocks.remove(block_to_remove)
            cursor.close()
            return True

        except sqlite3.Error as e:
            print(f"Database error while removing time block: {e}")
            self.conn.rollback()
            raise
        except Exception as e:
            print(f"Unexpected error while removing time block: {e}")
            self.conn.rollback()
            raise

    def update_time_block(self, updated_block: dict):
        """
        Update an existing time block in both the database and the in-memory structure.
        The updated_block is a dictionary that must include the "id" key.
        """
        try:
            block_name = updated_block["name"]

            # Find the existing block in memory
            existing_index = None
            for i, block in enumerate(self.time_blocks):
                if block["name"] == block_name:
                    existing_index = i
                    break
            if existing_index is None:
                print(f"Time block with ID {block_name} not found in memory.")
                return False

            # Convert each field to JSON or string as needed
            if updated_block.get("schedule", {}):
                schedule_dict = updated_block["schedule"]
                # Convert any datetime.time objects to strings
                schedule_dict = convert_times_in_schedule(schedule_dict)
                schedule_json = json.dumps(schedule_dict)
            else:
                schedule_json = "{}"
            list_cats_json = json.dumps(updated_block.get("list_categories", {"include": [], "exclude": []}))
            task_tags_json = json.dumps(updated_block.get("task_tags", {"include": [], "exclude": []}))
            color_str = ""
            if "color" in updated_block and updated_block["color"]:
                color_str = str(updated_block["color"])
            unavailable = updated_block.get("unavailable", 0)

            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE time_blocks
                SET
                    name = ?,
                    schedule = ?,
                    list_categories = ?,
                    task_tags = ?,
                    color = ?,
                    unavailable = ?
            """, (
                updated_block.get("name", ""),
                schedule_json,
                list_cats_json,
                task_tags_json,
                color_str,
                unavailable
            ))
            if cursor.rowcount == 0:
                print(f"Time block with ID {block_name} not found in database.")
                return False

            self.conn.commit()
            cursor.close()

            # Update the in-memory record
            self.time_blocks[existing_index] = updated_block
            return True

        except sqlite3.Error as e:
            print(f"Database error while updating time block: {e}")
            self.conn.rollback()
            raise
        except Exception as e:
            print(f"Error updating time block: {e}")
            self.conn.rollback()
            raise

    def get_user_defined_timeblocks_for_date(self, given_date):
        day_full = given_date.strftime("%A").lower()
        result = []

        for block in self.time_blocks:
            schedule = block.get("schedule", {})
            if day_full in schedule:
                time_range = schedule[day_full]
                if isinstance(time_range, (list, tuple)) and len(time_range) == 2:
                    start_val, end_val = time_range

                    # If we already have a time object, great. Otherwise parse string -> time
                    if isinstance(start_val, time):
                        start_time = start_val
                    else:
                        start_time = datetime.strptime(start_val, "%H:%M").time()

                    if isinstance(end_val, time):
                        end_time = end_val
                    else:
                        end_time = datetime.strptime(end_val, "%H:%M").time()

                    # Now create your TimeBlock
                    new_block = TimeBlock(
                        block_id=None,
                        name=block.get("name", ""),
                        date=given_date,
                        list_categories=block.get("list_categories"),
                        task_tags=block.get("task_tags"),
                        block_type="user_defined",
                        color=block.get("color")
                    )
                    new_block.start_time = start_time
                    new_block.end_time = end_time

                    # Compute duration (in hours)
                    start_dt = datetime.combine(given_date, start_time)
                    end_dt = datetime.combine(given_date, end_time)
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    new_block.duration = (end_dt - start_dt).total_seconds() / 3600.0

                    result.append(new_block)
        return result

    def task_weight_formula(self, task, max_added_time, max_time_estimate):
        # W = αP + β(1/ max(1,D)) + γF + δ(A/M_A) + εE + ζ(T/M_T) + η(L/T) + Q + M
        priority_weight = self.alpha * task.priority

        if task.due_datetime:
            days_left = max(1, (task.due_datetime - datetime.now()).total_seconds() / (24 * 3600))
            urgency_weight = self.beta * (1 / days_left)
        else:
            urgency_weight = self.beta * 0.5

        flexibility_map = {"Strict": 0, "Flexible": 1, "Very Flexible": 2}
        flexibility_weight = self.gamma * flexibility_map.get(task.flexibility, 1)

        if task.added_date_time:
            added_time_weight = self.delta * ((datetime.now() - task.added_date_time).total_seconds() / max_added_time)
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

        # Quick task weight Q = K * exp(-t / T_q)
        if hasattr(task, 'quick') and task.quick:
            t = (datetime.now() - task.added_date_time).total_seconds() if task.added_date_time else 0
            quick_task_weight = self.K * math.exp(-t / self.T_q)
        else:
            quick_task_weight = 0

        # Manually scheduled weight M = C if task is manually scheduled
        manually_weight = self.C if hasattr(task, 'manually_scheduled') and task.manually_scheduled else 0

        return (priority_weight + urgency_weight + flexibility_weight + added_time_weight +
                effort_weight + time_estimate_weight + time_logged_weight +
                quick_task_weight + manually_weight)

    def update_task_global_weights(self):

        max_added_time = max(
            (datetime.now() - task.added_date_time).total_seconds()
            for task in self.active_tasks if task.added_date_time
        ) if any(task.added_date_time for task in self.active_tasks) else 1

        max_time_estimate = max(
            (task.time_estimate for task in self.active_tasks if task.time_estimate),
            default=1
        )

        total_weight = sum(
            self.task_weight_formula(task, max_added_time, max_time_estimate) for task in self.active_tasks
        )

        if total_weight == 0:
            return

        for task in self.active_tasks:
            global_weight = (
                    self.task_weight_formula(task, max_added_time, max_time_estimate) / total_weight
            )
            task.global_weight = global_weight
            self.task_manager_instance.update_task(task)

        self.conn.commit()

    def get_day_schedule(self, date):
        for schedule in self.day_schedules:
            if schedule.date == date:
                return schedule

    def load_day_schedules(self):
        """
        Generates DaySchedule objects starting from today.
        The schedule will span at least MIN_SCHEDULE_DAYS (21) days but not exceed MAX_SCHEDULE_DAYS (48).
        If there is a due date among active tasks, it is used only if it falls within the allowed range.
        """
        MIN_SCHEDULE_DAYS = 21
        MAX_SCHEDULE_DAYS = 48

        today = datetime.now().date()

        # Determine the latest due date among active tasks (if any)
        latest_due_date = None
        if self.active_tasks and any(task.due_datetime for task in self.active_tasks):
            latest_due_date = max(task.due_datetime.date() for task in self.active_tasks if task.due_datetime)

        min_end_date = today + timedelta(days=MIN_SCHEDULE_DAYS - 1)
        max_end_date = today + timedelta(days=MAX_SCHEDULE_DAYS - 1)

        if latest_due_date is None or latest_due_date < min_end_date:
            end_date = min_end_date
        elif latest_due_date > max_end_date:
            end_date = max_end_date
        else:
            end_date = latest_due_date

        num_days = (end_date - today).days + 1
        return [DaySchedule(self, today + timedelta(days=i)) for i in range(num_days)]

    def estimate_daily_buffer_ratios(self, max_buffer_ratio=0.8):
        """
        Estimate each day's buffer ratio before tasks are assigned to timeblocks.
        The buffer ratio is computed as the fraction of free time (i.e. EAT minus estimated workload)
        relative to the day's effective available time (EAT), but capped by max_buffer_ratio.
        """
        # 1. Calculate total workload from all active tasks (in hours)
        total_workload = sum(task.time_estimate for task in self.active_tasks)

        # 2. Sum the EAT (Effective Available Time) across all days (in hours)
        total_eat = sum(day_schedule.get_eat() for day_schedule in self.day_schedules)

        # 3. Handle edge case: if no time is available
        if total_eat <= 0:
            for day_schedule in self.day_schedules:
                day_schedule.assign_buffer_ratio(0.0)
            return

        # 4. For each day, estimate the workload share and compute free time and buffer ratio.
        for day_schedule in self.day_schedules:
            day_eat = day_schedule.get_eat()
            # Estimate workload for this day, proportionally to its available time.
            day_workload_est = (day_eat / total_eat) * total_workload

            # Compute free time: available time minus estimated workload.
            free_time = max(day_eat - day_workload_est, 0)

            # Raw buffer ratio as free time divided by total available time.
            raw_buffer_ratio = free_time / day_eat if day_eat > 0 else 0.0

            # Cap the buffer ratio to avoid excessively high values.
            buffer_ratio = min(raw_buffer_ratio, max_buffer_ratio)

            # day_schedule.assign_buffer_ratio(buffer_ratio)
            day_schedule.assign_buffer_ratio(buffer_ratio)

    def chunk_tasks(self):
        chunks = []
        recurrence_end_date = datetime.now() + timedelta(days=int(len(self.day_schedules)) - 1)

        for task in self.active_tasks:
            for chunk_data in task.chunks:
                base_chunk_id = chunk_data.get("id")

                # Ensure date is a datetime.date object
                date_value = chunk_data.get("date")
                if isinstance(date_value, str):
                    try:
                        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
                    except ValueError:
                        date_value = None

                chunk_obj = TaskChunk(
                    id=base_chunk_id,
                    task=task,
                    chunk_type=chunk_data.get("type"),
                    unit=chunk_data.get("unit"),
                    size=chunk_data.get("size"),
                    timeblock_ratings=chunk_data.get("timeblock_ratings", []),
                    timeblock=chunk_data.get("time_block"),
                    date=date_value,
                    is_recurring=task.recurring,
                    status=chunk_data.get("status", "active")
                )
                chunks.append(chunk_obj)

                if task.recurring:
                    recurrence_count = 1
                    if isinstance(task.recur_every, int):
                        try:
                            base_date = chunk_obj.date if chunk_obj.date else datetime.now().date()
                        except ValueError:
                            base_date = datetime.now().date()

                        next_date = base_date
                        while next_date < recurrence_end_date.date():
                            next_date += timedelta(days=task.recur_every)
                            recurring_chunk = TaskChunk(
                                id=f"{base_chunk_id}_{recurrence_count}",
                                task=task,
                                chunk_type=chunk_data.get("type"),
                                unit=chunk_data.get("unit"),
                                size=chunk_data.get("size"),
                                timeblock_ratings=chunk_data.get("timeblock_ratings", []),
                                timeblock=chunk_data.get("time_block"),
                                date=next_date,
                                is_recurring=True,
                                status="locked"
                            )
                            chunks.append(recurring_chunk)
                            recurrence_count += 1

                    elif isinstance(task.recur_every, list):
                        current_date = datetime.now().date()
                        while current_date <= recurrence_end_date.date():
                            if current_date.strftime("%A") in task.recur_every:
                                recurring_chunk = TaskChunk(
                                    id=f"{base_chunk_id}_{recurrence_count}",
                                    task=task,
                                    chunk_type=chunk_data.get("type"),
                                    unit=chunk_data.get("unit"),
                                    size=chunk_data.get("size"),
                                    timeblock_ratings=chunk_data.get("timeblock_ratings", []),
                                    timeblock=chunk_data.get("time_block"),
                                    date=current_date,
                                    is_recurring=True,
                                    status="locked"
                                )
                                chunks.append(recurring_chunk)
                                recurrence_count += 1
                            current_date += timedelta(days=1)

        return chunks

    def solve_schedule_with_cp(self):
        """
        This method uses OR-Tools CP-SAT to assign task chunks to available time blocks.
        It creates decision variables for each (chunk, block) pair, enforces full allocation,
        capacity, and minimum/maximum allocation constraints, and maximizes an objective based
        on task ratings. After solving, it updates each time block’s assigned chunks; if any
        chunk has an unscheduled remainder, that chunk is flagged.
        """
        scale = 10  # Scale factor: converts fractional hours to integers

        # --- Step 1. Prepare Data: Flatten available time blocks from all day schedules ---
        all_blocks = []
        block_capacity = {}  # key: block.id, value: capacity in scaled units
        for day in self.day_schedules:
            for block in day.time_blocks:
                if block.block_type == "unavailable":
                    continue
                all_blocks.append(block)
                # Compute available capacity in hours and then scale it.
                cap = block.get_available_time()
                block_capacity[block.id] = int(cap * scale + 0.5)

        # --- Step 2. Prepare Chunks ---
        all_chunks = self.chunks
        all_chunks.sort(key=lambda chunk: getattr(chunk.task, 'global_weight', float('-inf')), reverse=True)

        # --- Step 4. Build Allowed Assignments ---
        # For every (chunk, block) pair, record the rating and the full chunk weight (scaled).
        allowed_assignments = {}  # Key: (chunk.id, block.id)

        for chunk in all_chunks:
            # Convert chunk's total size to scaled units.
            full_weight = int(chunk.size * scale + 0.5)

            for (block_obj, rating) in chunk.timeblock_ratings:
                # If the block is flagged "unavailable," you can skip it here, or
                # handle it earlier so that chunk.timeblock_ratings never includes it.

                allowed_assignments[(chunk.id, block_obj.id)] = {
                    "rating": rating,
                    "full_weight": full_weight
                }

        # --- Step 5. Create the CP-SAT Model ---
        model = cp_model.CpModel()

        # Decision variables: assign[(c,b)] is binary; alloc[(c,b)] is the scaled allocated units.
        assign = {}
        alloc = {}
        for (c_id, b_id), data in allowed_assignments.items():
            assign[(c_id, b_id)] = model.NewBoolVar(f"assign_{c_id}_{b_id}")
            full_weight = data["full_weight"]
            alloc[(c_id, b_id)] = model.NewIntVar(0, full_weight, f"alloc_{c_id}_{b_id}")

        # Unscheduled variables and chunk parameters.
        unsched_manual = {}
        unsched_auto = {}
        chunk_weight = {}  # Full chunk weight in scaled units.
        chunk_min = {}  # Minimum allocation per block (scaled)
        chunk_max = {}  # Maximum allocation per block (scaled)

        for chunk in all_chunks:
            # Scale the total chunk size.
            w = int(chunk.size * scale + 0.5)
            chunk_weight[chunk.id] = w
            if chunk.chunk_type == "auto":
                # Scale the minimum size. Use default 0.5 if not provided.
                m = int(chunk.task.min_chunk_size * scale + 0.5)
                chunk_min[chunk.id] = m
                # Scale the maximum size. If not provided, default to full size.
                M = int(chunk.task.max_chunk_size * scale + 0.5)
                chunk_max[chunk.id] = M

        # Create unscheduled variables based on chunk type.
        for chunk in all_chunks:
            if chunk.chunk_type == "manual":
                # For manual chunks, unscheduled is a binary flag (1 means not scheduled anywhere).
                unsched_manual[chunk.id] = model.NewBoolVar(f"unsched_{chunk.id}")
            else:
                # For auto chunks, unscheduled is an integer variable (units left unscheduled).
                unsched_auto[chunk.id] = model.NewIntVar(0, chunk_weight[chunk.id], f"unsched_{chunk.id}")

        # --- Constraints ---

        # (1) Full Allocation Constraints:
        # For each chunk, the sum of allocations over all blocks plus any unscheduled amount must equal the full chunk weight.
        # For manual chunks, the chunk must be fully assigned in one block or marked unscheduled.
        for chunk in [c for c in all_chunks if c.chunk_type == "manual"]:
            possible_assignments = []
            for (cid, b_id) in assign:
                if cid == chunk.id:
                    possible_assignments.append(assign[(cid, b_id)])
                    # If assigned to a block, then allocation must equal the full chunk weight.
                    model.Add(alloc[(cid, b_id)] == chunk_weight[chunk.id]).OnlyEnforceIf(assign[(cid, b_id)])
                    # Otherwise, no allocation is made.
                    model.Add(alloc[(cid, b_id)] == 0).OnlyEnforceIf(assign[(cid, b_id)].Not())
            # Ensure that the chunk is assigned exactly once or left unscheduled.
            model.Add(sum(possible_assignments) + unsched_manual[chunk.id] == 1)

        # For auto (splittable) chunks, the sum of allocations across all blocks plus unscheduled units equals the full weight.
        # Also, for each assignment, if it is made, the allocation must be between the min and max allowed.
        for chunk in [c for c in all_chunks if c.chunk_type == "auto"]:
            possible_allocs = []
            for (cid, b_id) in alloc:
                if cid == chunk.id:
                    # Enforce a minimum allocation if this assignment is made.
                    m = chunk_min[chunk.id]
                    model.Add(alloc[(cid, b_id)] >= m).OnlyEnforceIf(assign[(cid, b_id)])
                    # Enforce a maximum allocation if this assignment is made.
                    M = chunk_max[chunk.id]
                    model.Add(alloc[(cid, b_id)] <= M).OnlyEnforceIf(assign[(cid, b_id)])
                    # If not assigned, then allocation must be zero.
                    model.Add(alloc[(cid, b_id)] == 0).OnlyEnforceIf(assign[(cid, b_id)].Not())
                    possible_allocs.append(alloc[(cid, b_id)])
            model.Add(sum(possible_allocs) + unsched_auto[chunk.id] == chunk_weight[chunk.id])
            # Note: The flexibility of splitting is inherent in allowing multiple assignments
            # that each must satisfy the min and max limits.

        # (2) Capacity Constraints:
        # The total allocated units in each time block must not exceed its available capacity.
        for block in all_blocks:
            block_allocs = []
            for (c_id, b_id) in alloc:
                if b_id == block.id:
                    block_allocs.append(alloc[(c_id, b_id)])
            model.Add(sum(block_allocs) <= block_capacity[block.id])

        # --- Objective Function ---
        # Our goal is to maximize the total rating (which factors in global importance) from all allocations
        # while penalizing any unscheduled portions.
        penalty_manual = 100  # Penalty for each unscheduled manual chunk (a high value discourages unscheduling)
        penalty_auto = 100  # Penalty per unit (scaled) unscheduled for auto chunks

        objective_terms = []

        # For each allowed (chunk, block) pair, add its contribution (rating * allocation).
        for (c_id, b_id), var in alloc.items():
            rating = allowed_assignments[(c_id, b_id)]["rating"]
            objective_terms.append(rating * var)

        # Subtract penalty terms for unscheduled work.
        for chunk in [c for c in all_chunks if c.chunk_type == "manual"]:
            objective_terms.append(-penalty_manual * unsched_manual[chunk.id])
        for chunk in [c for c in all_chunks if c.chunk_type == "auto"]:
            objective_terms.append(-penalty_auto * unsched_auto[chunk.id])

        # Set the objective to maximize the total benefit.
        model.Maximize(sum(objective_terms))

        # --- Step 9. Solve the Model ---
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("Solution found:")
            # Iterate over each chunk to record its allocation.
            for chunk in all_chunks:
                # Gather allocations: for each (chunk, block) pair that was chosen,
                # we record the block object and the allocated hours.
                block_allocations = []
                total_assigned_scaled = 0
                for (c_id, b_id) in assign:
                    if c_id == chunk.id:
                        if solver.Value(assign[(c_id, b_id)]) == 1:
                            alloc_units = solver.Value(alloc[(c_id, b_id)])
                            if alloc_units > 0:
                                allocated_hours = alloc_units / scale
                                total_assigned_scaled += alloc_units
                                block_obj = next((b for b in all_blocks if b.id == b_id), None)
                                block_allocations.append((block_obj, allocated_hours))

                # Retrieve the unscheduled value using the appropriate unsched list.
                if chunk.chunk_type == "manual":
                    unsched_amt = solver.Value(unsched_manual[chunk.id])
                    # For manual chunks, a value of 1 means the chunk was not scheduled.
                    if unsched_amt == 1:
                        print(f"Manual Chunk {chunk.id} is UNSCHEDULED.")
                        chunk.flagged = True
                    else:
                        # Manual chunks should be assigned fully to one block.
                        if len(block_allocations) == 1:
                            block_obj, alloc_hours = block_allocations[0]
                            rating = allowed_assignments.get((chunk.id, block_obj.id), {}).get("rating", 100)
                            block_obj.add_chunk(chunk, rating)
                            print(
                                f"Manual Chunk {chunk.id} assigned fully to Block {block_obj.id} "
                                f"(Name='{block_obj.name}', Date={block_obj.date}) "
                                f"(allocated {alloc_hours:.2f} hours)"
                            )
                else:  # Auto chunks
                    unsched_amt = solver.Value(unsched_auto[chunk.id])
                    unsched_hours = unsched_amt / scale
                    if unsched_amt > 0:
                        chunk.flagged = True
                        print(f"Auto Chunk {chunk.id} UNSCHEDULED for {unsched_hours:.2f} hours")

                    # If allocated to multiple blocks, split the chunk.
                    if len(block_allocations) > 1:
                        hours_list = [alloc_hours for (_, alloc_hours) in block_allocations]
                        subchunks = chunk.split(hours_list)
                        for i, (block_obj, alloc_hours) in enumerate(block_allocations):
                            subchunk = subchunks[i]
                            rating = allowed_assignments.get((chunk.id, block_obj.id), {}).get("rating", 100)
                            block_obj.add_chunk(subchunk, rating)
                            print(
                                f"Auto Chunk {chunk.task.name} split → {subchunk.task.name}, assigned {alloc_hours:.2f} hours "
                                f"to Block Name='{block_obj.name}', Date={block_obj.date})"
                            )
                    elif len(block_allocations) == 1:
                        block_obj, alloc_hours = block_allocations[0]
                        rating = allowed_assignments.get((chunk.id, block_obj.id), {}).get("rating", 100)
                        block_obj.add_chunk(chunk, rating)
                        print(
                            f"Auto Chunk {chunk.task.name} assigned {alloc_hours:.2f} hours "
                            f"to Block Name='{block_obj.name}', Date={block_obj.date})"
                        )
            print("Objective value:", solver.ObjectiveValue())
        else:
            print("No solution found.")
            for chunk in all_chunks:
                chunk.flagged = True

    def generate_schedule(self):
        for chunk in self.chunks:
            # Handle placed chunks: they come with a specific date and timeblock.
            if chunk.chunk_type == "placed":
                # Determine the target date.
                target_date = chunk.date
                if isinstance(target_date, str):
                    try:
                        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
                    except ValueError:
                        chunk.flagged = True
                        continue

                # Find the DaySchedule matching the target date.
                matching_day = next((day for day in self.day_schedules if day.date == target_date), None)
                if matching_day is None:
                    chunk.flagged = True
                    continue

                # Find the specific timeblock within the DaySchedule.
                # Assume chunk.timeblock holds the id of the target timeblock.
                target_block = next(
                    (block for block in matching_day.time_blocks if str(block.id) == str(chunk.timeblock)),
                    None
                )
                if target_block is None:
                    chunk.flagged = True
                    continue

                if chunk.unit == "time":
                    if target_block.get_available_time() < chunk.size:
                        chunk.flagged = True
                        continue

                # Assign the placed chunk to the target timeblock.
                target_block.add_chunk(chunk, 10000)  # Using a fixed high rating for placed assignments.
                continue  # Skip to the next chunk.

            if chunk.is_recurring:
                chunk.timeblock_ratings = []
                for day in self.day_schedules:
                    if chunk.task.due_datetime and day.date > chunk.task.due_datetime.date():
                        break
                    if day.date == chunk.date:
                        ratings = day.get_suitable_timeblocks_with_rating(chunk)
                        chunk.timeblock_ratings.extend(ratings)
                        break

            else:
                # For non-placed chunks, clear any existing timeblock ratings.
                chunk.timeblock_ratings = []
                for day in self.day_schedules:
                    # Skip days beyond the task's due date (if set).
                    if chunk.task.due_datetime and day.date > chunk.task.due_datetime.date():
                        break
                    ratings = day.get_suitable_timeblocks_with_rating(chunk)
                    chunk.timeblock_ratings.extend(ratings)

            # Sort candidates by rating (highest first) and attempt assignment.
            chunk.timeblock_ratings.sort(key=lambda x: x[1], reverse=True)

        self.solve_schedule_with_cp()

    def refresh_schedule(self):
        """
        Refreshes the schedule by reloading tasks, recalculating
        weights, re-building day schedules, re-chunking, and
        assigning chunks again.
        """
        # 1. Reload active tasks from TaskManager
        self.active_tasks = self.task_manager_instance.get_active_tasks()

        # 2. Update each task's global weight
        self.update_task_global_weights()

        # 3. Re-build the day schedules
        self.day_schedules = self.load_day_schedules()

        # 4. Estimate daily buffer ratios
        self.estimate_daily_buffer_ratios()

        # 5. Re-chunk tasks
        self.chunks = self.chunk_tasks()

        # 6. Re-assign all chunks
        self.generate_schedule()


class DaySchedule:
    def __init__(self, schedule_manager_instance, date):
        self.date = date
        self.schedule_manager_instance = schedule_manager_instance
        self.task_manager_instance = schedule_manager_instance.task_manager_instance
        self.schedule_settings = schedule_manager_instance.schedule_settings
        self.sleep_time = self.schedule_settings.ideal_sleep_duration
        self.time_blocks = self.generate_schedule()
        self.buffer_ratio = 0.0
        self.reserved_time = 0.0

    def assign_buffer_ratio(self, buffer_ratio):
        self.buffer_ratio = buffer_ratio
        for block in self.time_blocks:
            block.buffer_ratio = buffer_ratio

    def generate_schedule(self):
        target_day = self.date.strftime('%A').lower()

        # 1) The day starts at self.schedule_settings.day_start
        day_start = datetime.combine(self.date, self.schedule_settings.day_start)

        # 2) The awake period ends at (day_start + 24 - sleep_time) => sleep start
        day_end = day_start + timedelta(hours=(24 - self.sleep_time))

        # 3) Create the Sleep block from day_end -> day_end + self.sleep_time
        sleep_block = TimeBlock(
            block_id=None,
            name=f"Sleep ({self.sleep_time:.1f}h)",
            date=self.date,
            block_type="unavailable",
            color=(173, 216, 230),
        )
        sleep_block.start_time = day_end.time()
        sleep_block.end_time = (day_end + timedelta(hours=self.sleep_time)).time()
        sleep_block.duration = (timedelta(hours=self.sleep_time).total_seconds()) / 3600.0

        # 4) Gather user‑defined blocks for this date
        user_blocks = self.schedule_manager_instance.get_user_defined_timeblocks_for_date(self.date)
        user_blocks.sort(key=lambda b: b.start_time)

        final_blocks = []
        current_dt = day_start

        # 5) Insert user blocks (or Open Block gaps) up to day_end
        for block in user_blocks:
            block_start_dt = datetime.combine(self.date, block.start_time)
            block_end_dt = datetime.combine(self.date, block.end_time)

            # If the block starts after the awake period, skip
            if block_start_dt >= day_end:
                break

            # If user block extends beyond day_end, clamp it
            if block_end_dt > day_end:
                block.end_time = day_end.time()
                block_end_dt = day_end

            # Fill any gap before this block
            if current_dt < block_start_dt:
                gap_block = TimeBlock(
                    block_id=None,
                    name="Open Block",
                    date=self.date,
                    block_type="system_defined",
                    color=(200, 200, 200),
                )
                gap_block.start_time = current_dt.time()
                gap_block.end_time = block_start_dt.time()
                gap_block.duration = (block_start_dt - current_dt).total_seconds() / 3600
                final_blocks.append(gap_block)

            final_blocks.append(block)
            current_dt = block_end_dt

        # 6) Fill leftover time (if any) before sleep starts
        if current_dt < day_end:
            gap_block = TimeBlock(
                block_id=None,
                name="Open Block",
                date=self.date,
                block_type="system_defined",
                color=(200, 200, 200),
            )
            gap_block.start_time = current_dt.time()
            gap_block.end_time = day_end.time()
            gap_block.duration = (day_end - current_dt).total_seconds() / 3600
            final_blocks.append(gap_block)

        # 7) Finally, add the sleep block to the schedule
        final_blocks.append(sleep_block)

        return final_blocks

    def qualifies(self, task, block):
        inc = block.list_categories.get("include", [])
        exc = block.list_categories.get("exclude", [])
        cat = self.task_manager_instance.get_task_list_category_name(task.list_name)
        if inc and cat not in inc:
            return False
        if exc and cat in exc:
            return False
        inc_tags = block.task_tags.get("include", [])
        exc_tags = block.task_tags.get("exclude", [])
        if inc_tags and not any(tag in inc_tags for tag in task.tags):
            return False
        if exc_tags and any(tag in exc_tags for tag in task.tags):
            return False
        return True

    def get_eat(self, task=None):
        total = 0.0
        if task:
            for block in self.time_blocks:
                if block.block_type == "unavailable":
                    continue
                if self.qualifies(task, block):
                    total += block.get_available_time()
        else:
            for block in self.time_blocks:
                if block.block_type != "unavailable":
                    total += block.get_available_time()
        return total

    def get_suitable_timeblocks_with_rating(self, chunk):
        """
        Suggests time blocks for the given chunk, sorted by rating in descending order.
        Incorporates weighting coefficients (alpha, beta, gamma, delta, epsilon, etc.)
        only if they're relevant to the rating.
        """

        if chunk.is_recurring:
            if self.date != chunk.date:
                return []

        def compute_time_bonus(t, interval, max_bonus, threshold=60):
            """Existing logic for peak/off-peak hour bonuses."""

            def to_minutes(t_obj):
                return t_obj.hour * 60 + t_obj.minute

            t_val = to_minutes(t)
            start_val = to_minutes(interval[0])
            end_val = to_minutes(interval[1])

            # Handle intervals crossing midnight
            if start_val > end_val:
                if t_val < start_val:
                    t_val += 24 * 60
                end_val += 24 * 60

            if start_val <= t_val <= end_val:
                return max_bonus
            elif t_val < start_val:
                diff = start_val - t_val
                return max_bonus * (1 - diff / threshold) if diff <= threshold else 0
            else:
                diff = t_val - end_val
                return max_bonus * (1 - diff / threshold) if diff <= threshold else 0

        suitable = []
        task = chunk.task
        today = datetime.now().date()

        # For easy access to coefficients from your manager/settings:
        alpha = self.schedule_manager_instance.alpha
        beta = self.schedule_manager_instance.beta
        gamma = self.schedule_manager_instance.gamma
        delta = self.schedule_manager_instance.delta
        epsilon = self.schedule_manager_instance.epsilon
        zeta = self.schedule_manager_instance.zeta
        eta_ = self.schedule_manager_instance.eta
        theta_ = self.schedule_manager_instance.theta

        for block in self.time_blocks:
            if block.block_type == "unavailable":
                continue
            if not self.qualifies(task, block):
                continue

            # For time-based chunks that are manual (not auto-splittable), skip if not enough capacity
            if chunk.unit == "time" and chunk.chunk_type != "auto":
                if block.get_available_time() < chunk.size:
                    continue

            # ---------------------------------------------------------------------------------------
            # Compute sub-ratings for each factor you have and multiply by the weighting coefficients
            # ---------------------------------------------------------------------------------------

            # 1) Due Date Influence
            due_date_score = 0
            if task.due_datetime:
                days_until_due = (task.due_datetime.date() - self.date).days
                # Example scoring: tasks with fewer days_until_due get a higher (or lower) rating
                # For demonstration, let's invert the days_until_due and clamp it:
                # e.g. (100 / (days_until_due+1)) => bigger when days_until_due is small
                due_date_score = 100 / (days_until_due + 1)
            # Weighted portion of rating
            rating_due_date = alpha * due_date_score

            # 2) Added Date Influence
            added_date_score = 0
            if hasattr(task, "added_date_time") and task.added_date_time:
                days_from_added_to_block = (self.date - task.added_date_time.date()).days
                # Example: big bonus if scheduled soon, decays over time
                added_date_score = max(0, 30 - days_from_added_to_block)
            rating_added_date = beta * added_date_score

            # 3) Priority
            priority_score = 0
            if hasattr(task, "priority"):
                # If priority is high, you can scale that more
                priority_score = max(0, (task.priority - 2) * 10)
            rating_priority = gamma * priority_score

            # 4) Flexibility
            flexibility_score = 0
            if hasattr(task, "flexibility"):
                if task.flexibility == "high":
                    flexibility_score = -10  # penalize scheduling soon
                elif task.flexibility == "low":
                    flexibility_score = 10  # encourage scheduling asap
            rating_flexibility = delta * flexibility_score

            # 5) Days from "today"
            # Possibly incorporate how far in the future it is
            days_from_today = (self.date - today).days
            days_from_today_score = 0
            if getattr(task, "priority", 0) >= 8:
                days_from_today_score = max(0, 100 - days_from_today * 10)
            rating_days_from_today = epsilon * days_from_today_score

            # 6) Preferred Work Days
            preferred_days_score = 0
            if task.preferred_work_days:
                if self.date.strftime("%A")[:3] in task.preferred_work_days:
                    preferred_days_score = 50
            rating_preferred_days = zeta * preferred_days_score

            # 7) Time-of-day preferences
            time_of_day_score = 0
            pref_intervals = {
                "Morning": (time(6, 0), time(10, 0)),
                "Afternoon": (time(12, 0), time(16, 0)),
                "Evening": (time(16, 0), time(20, 0)),
                "Night": (time(20, 0), time(23, 0))
            }
            if task.time_of_day_preference:
                for pref in task.time_of_day_preference:
                    if pref in pref_intervals:
                        bonus = compute_time_bonus(block.start_time, pref_intervals[pref], 50)
                        time_of_day_score += bonus
                        # break if you only want to apply the first match:
                        break
            rating_time_of_day = eta_ * time_of_day_score

            # 8) Effort level vs. peak/off-peak
            effort_score = 0
            if task.effort_level:
                if task.effort_level == "High":
                    peak_start, peak_end = self.schedule_settings.peak_productivity_hours
                    effort_score = compute_time_bonus(block.start_time, (peak_start, peak_end), 50)
                elif task.effort_level == "Low":
                    off_start, off_end = self.schedule_settings.off_peak_hours
                    effort_score = compute_time_bonus(block.start_time, (off_start, off_end), 30)
            rating_effort = theta_ * effort_score

            # Combine sub-ratings
            rating = (
                    rating_due_date +
                    rating_added_date +
                    rating_priority +
                    rating_flexibility +
                    rating_days_from_today +
                    rating_preferred_days +
                    rating_time_of_day +
                    rating_effort
            )

            # Optionally, you can add a baseline
            rating += 10  # Example baseline offset

            # Store the block & rating
            suitable.append((block, rating))

        # Sort highest rating first
        suitable.sort(key=lambda x: x[1], reverse=True)
        return suitable
