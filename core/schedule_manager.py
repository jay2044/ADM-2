import os
import sqlite3
import json
import uuid
from datetime import datetime, date, time, timedelta
import random
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
                    task_status_popup_frequency INTEGER
                )
            ''')

    def load_settings(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schedule_settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                self.day_start = self.parse_time(row[1])
                self.ideal_sleep_duration = row[2]
                self.overtime_flexibility = row[3]
                self.hours_of_day_available = row[4]
                self.peak_productivity_hours = (self.parse_time(row[5]), self.parse_time(row[6]))
                self.off_peak_hours = (self.parse_time(row[7]), self.parse_time(row[8]))
                self.task_notifications = bool(row[9])
                self.task_status_popup_frequency = row[10]
            else:
                self.day_start = time(4, 0)
                self.ideal_sleep_duration = 8.0
                self.overtime_flexibility = "auto"
                self.hours_of_day_available = 24.0 - self.ideal_sleep_duration
                self.peak_productivity_hours = (time(17, 0), time(19, 0))
                self.off_peak_hours = (time(22, 0), time(6, 0))
                self.task_notifications = True
                self.task_status_popup_frequency = 20
                self.save_settings()

    def save_settings(self):
        with sqlite3.connect(self.db_path) as conn:
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


# --- Modified TimeBlock class (add get_available_count method) ---
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
        return max(0, (self.duration * (1 - self.buffer_ratio)) - used_time)

    def get_capacity(self):
        return max(0, self.duration * (1 - self.buffer_ratio))

    def get_available_count(self):
        # For count-based tasks, assume capacity is analogous to time capacity.
        used_count = sum(info["chunk"].size for info in self.task_chunks.values())
        capacity = self.get_capacity()
        return max(0, capacity - used_count)

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

        # Weighting coefficients
        self.alpha = 0.4
        self.beta = 0.3
        self.gamma = 0.1
        self.delta = 0.2
        self.epsilon = 0.2
        self.zeta = 0.3
        self.eta = 0.2
        self.theta = 0.1
        # K: Fixed boost weight for quick tasks.
        # T_q: Decay time constant (in seconds).
        # C: Very high constant ensuring placed tasks always appear at the top.
        self.K = 100
        self.T_q = 3600
        self.C = 1000

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

    def estimate_daily_buffer_ratios(self):
        """
        Estimate each day's buffer ratio before tasks are assigned to timeblocks.
        Uses a proportional approach based on each day's EAT relative to total EAT,
        and the overall total workload.
        """
        # 1. Calculate total workload from all active tasks
        total_workload = sum(task.time_estimate for task in self.active_tasks)

        # 2. Sum the EAT (Effective Available Time) across all days
        total_eat = 0.0
        for day_schedule in self.day_schedules:
            day_eat = day_schedule.get_eat()  # Assume get_eat() is defined
            total_eat += day_eat

        # 3. Distribute workload to each day proportionally,
        #    then derive a pre-assignment "estimated" daily buffer
        if total_eat <= 0:
            # Edge case: No available time at all
            for day_schedule in self.day_schedules:
                day_schedule.assign_buffer_ratio(0.0)
            return

        # 4. Assign an approximate share of the total workload to each day
        for day_schedule in self.day_schedules:
            day_eat = day_schedule.get_eat()
            # Proportional workload share for this day
            day_workload_est = (day_eat / total_eat) * total_workload

            # 5. Calculate the daily buffer ratio as a fraction of free time
            if day_eat > 0:
                day_schedule.assign_buffer_ratio(1 - day_workload_est)
            else:
                day_schedule.assign_buffer_ratio(0.0)
            # day_schedule.assign_buffer_ratio(0.0)

    def chunk_tasks(self):
        chunks = []
        recurrence_end_date = datetime.now() + timedelta(days=48)

        for task in self.active_tasks:
            for chunk_data in task.chunks:
                base_chunk_id = chunk_data.get("id")

                chunk_obj = TaskChunk(
                    id=base_chunk_id,
                    task=task,
                    chunk_type=chunk_data.get("type"),
                    unit=chunk_data.get("unit"),
                    size=chunk_data.get("size"),
                    timeblock_ratings=chunk_data.get("timeblock_ratings", []),
                    timeblock=chunk_data.get("time_block"),
                    date=chunk_data.get("date"),
                    is_recurring=chunk_data.get("is_recurring", False),
                    status=chunk_data.get("status", "active")
                )
                chunks.append(chunk_obj)

                if task.recurring and chunk_data.get("is_recurring", False):
                    recurrence_count = 1
                    if isinstance(task.recur_every, int):
                        try:
                            base_date = datetime.strptime(chunk_obj.date,
                                                          "%Y-%m-%d") if chunk_obj.date else datetime.now()
                        except ValueError:
                            base_date = datetime.now()
                        next_date = base_date
                        while next_date < recurrence_end_date:
                            next_date += timedelta(days=task.recur_every)
                            recurring_chunk = TaskChunk(
                                id=f"{base_chunk_id}_{recurrence_count}",
                                task=task,
                                chunk_type=chunk_data.get("type"),
                                unit=chunk_data.get("unit"),
                                size=chunk_data.get("size"),
                                timeblock_ratings=chunk_data.get("timeblock_ratings", []),
                                timeblock=chunk_data.get("time_block"),
                                date=next_date.strftime("%Y-%m-%d"),
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
                                    date=current_date.strftime("%Y-%m-%d"),
                                    is_recurring=True,
                                    status="locked"
                                )
                                chunks.append(recurring_chunk)
                                recurrence_count += 1
                            current_date += timedelta(days=1)
        return chunks

    # returns a bool for success
    def assign_chunk(self, chunk, exclude_block=None, test=False):
        task = chunk.task

        if not chunk.timeblock_ratings or not isinstance(chunk.timeblock_ratings, list):
            chunk.flagged = True
            return False

        sorted_candidates = sorted(chunk.timeblock_ratings, key=lambda x: x[1], reverse=True)

        # For both time‐ and count‑based chunks, use the "size" attribute.
        required_capacity = chunk.size

        if chunk.chunk_type == "auto":
            FLEXIBILITY_MAP = {"Strict": 1, "Flexible": 2, "Very Flexible": 3}
            flexibility_ratio = FLEXIBILITY_MAP.get(task.flexibility, 1) / max(FLEXIBILITY_MAP.values())
            if required_capacity <= 0:
                return True
            num_top_candidates = max(1, int(len(sorted_candidates) * flexibility_ratio))
            top_candidates = [cand for cand in sorted_candidates[:num_top_candidates]
                              if exclude_block is None or cand[0].id != exclude_block.id]
            for candidate in top_candidates:
                block, rating = candidate
                filtered_chunks = [ci["chunk"] for ci in block.task_chunks.values() if ci["rating"] < rating]
                filtered_chunks = [c for c in filtered_chunks if c.chunk_type != "placed"]
                # Use block.get_available_time() for time‐based units and get_available_count() for count.
                available = (block.get_available_time() if chunk.unit == "time"
                             else block.get_available_count())
                if available >= required_capacity:
                    if not test:
                        block.add_chunk(chunk, rating)
                    return True
                else:
                    if not filtered_chunks:
                        continue
                    resizable_capacity = 0.0
                    reschedule_chunk_queue = []
                    for filtered_chunk in filtered_chunks:
                        cap = filtered_chunk.size
                        if cap <= 0:
                            continue
                        if filtered_chunk.chunk_type == "placed":
                            if self.assign_chunk(filtered_chunk, block, True):
                                resizable_capacity += cap
                                reschedule_chunk_queue.append(filtered_chunk)
                        elif filtered_chunk.chunk_type == "auto":
                            flexibility_ratio_auto = FLEXIBILITY_MAP.get(filtered_chunk.task.flexibility, 1) / max(
                                FLEXIBILITY_MAP.values())
                            if flexibility_ratio_auto >= flexibility_ratio:
                                av = filtered_chunk.size - (required_capacity - resizable_capacity)
                                if av > 0:
                                    sp = filtered_chunk.split([av, cap - av])
                                    if sp and len(sp) >= 2:
                                        if self.assign_chunk(sp[1], block, True):
                                            resizable_capacity += sp[1].size
                                            reschedule_chunk_queue.append(sp[1])
                            elif cap <= required_capacity:
                                if self.assign_chunk(filtered_chunk, block, True):
                                    resizable_capacity += cap
                                    reschedule_chunk_queue.append(filtered_chunk)
                        if resizable_capacity >= required_capacity:
                            break
                    if resizable_capacity >= 0.9 * required_capacity:
                        available_for_this_block = available + resizable_capacity
                        total = chunk.size
                        if available_for_this_block < total:
                            sp = chunk.split([available_for_this_block, total - available_for_this_block])
                            if sp and len(sp) >= 2:
                                if not test:
                                    block.add_chunk(sp[0], rating)
                                if self.assign_chunk(sp[1], exclude_block=block, test=test):
                                    return True
                    if resizable_capacity >= required_capacity:
                        for reschedule_chunk in reschedule_chunk_queue:
                            block.remove_chunk(reschedule_chunk)
                            self.assign_chunk(reschedule_chunk, block)
                        if not test:
                            block.add_chunk(chunk, rating)
                        return True

        elif chunk.chunk_type == "manual":
            for candidate in sorted_candidates:
                block, rating = candidate
                if exclude_block and block.id == exclude_block.id:
                    continue
                available = (block.get_available_time() if chunk.unit == "time"
                             else block.get_available_count())
                total = chunk.size
                if available >= total:
                    if not test:
                        block.add_chunk(chunk, rating)
                    return True
                else:
                    filtered_chunks = [ci["chunk"] for ci in block.task_chunks.values() if ci["rating"] < rating]
                    filtered_chunks = [c for c in filtered_chunks if c.chunk_type != "placed"]
                    if not filtered_chunks:
                        continue
                    resizable_capacity = 0.0
                    reschedule_chunk_queue = []
                    for filtered_chunk in filtered_chunks:
                        if filtered_chunk.chunk_type in ("placed", "auto"):
                            if self.assign_chunk(filtered_chunk, block, True):
                                resizable_capacity += filtered_chunk.size
                                reschedule_chunk_queue.append(filtered_chunk)
                        if resizable_capacity >= total:
                            break
                    if resizable_capacity >= total:
                        for reschedule_chunk in reschedule_chunk_queue:
                            block.remove_chunk(reschedule_chunk)
                            self.assign_chunk(reschedule_chunk, block)
                        if not test:
                            block.add_chunk(chunk, rating)
                        return True

        chunk.flagged = True
        return False

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
            self.assign_chunk(chunk)

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

        # 5) Insert user blocks (or unscheduled gaps) up to day_end
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
                    name="Unscheduled",
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
                name="Unscheduled",
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
        from datetime import datetime, time, timedelta

        def compute_time_bonus(t, interval, max_bonus, threshold=60):
            def to_minutes(t_obj):
                return t_obj.hour * 60 + t_obj.minute

            t_val = to_minutes(t)
            start_val = to_minutes(interval[0])
            end_val = to_minutes(interval[1])
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
        for block in self.time_blocks:
            if block.block_type == "unavailable":
                continue
            if not self.qualifies(task, block):
                continue
            # For time-based chunks, ensure the block has enough available time.
            if chunk.unit == "time" and not chunk.chunk_type == "auto" and block.get_available_time() < chunk.size:
                continue

            rating = 0
            if task.due_datetime:
                days_until_due = (task.due_datetime.date() - self.date).days
                rating += 100 / (days_until_due + 1)
            days_from_today = (self.date - today).days
            if task.priority >= 8:
                rating += max(0, 100 - days_from_today * 10)
            if task.preferred_work_days:
                if self.date.strftime("%A") in task.preferred_work_days:
                    rating += 50
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
                        rating += bonus
                        break
            if task.effort_level:
                if task.effort_level == "High":
                    peak_start, peak_end = self.schedule_settings.peak_productivity_hours
                    bonus = compute_time_bonus(block.start_time, (peak_start, peak_end), 50)
                    rating += bonus
                elif task.effort_level == "Low":
                    off_start, off_end = self.schedule_settings.off_peak_hours
                    bonus = compute_time_bonus(block.start_time, (off_start, off_end), 30)
                    rating += bonus
            suitable.append((block, rating))
        suitable.sort(key=lambda x: x[1], reverse=True)
        return suitable
