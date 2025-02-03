import os
import sqlite3
import json
import uuid
from datetime import datetime, date, time, timedelta
import random

from pyarrow import duration

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

    def add_chunk(self, chunk, rating):
        task = chunk.task
        task_id = task.id if hasattr(task, 'id') else uuid.uuid4().int
        if task_id in self.task_chunks and chunk.auto:
            self.task_chunks[task_id]["chunk"].duration += chunk.duration
        else:
            self.task_chunks[task_id] = {"chunk": chunk, "rating": rating}

    def remove_chunk(self, task, remove_amount):
        task_id = task.id if hasattr(task, 'id') else None
        if task_id and task_id in self.task_chunks:
            existing_chunk = self.task_chunks[task_id]["chunk"]
            if not existing_chunk.auto:
                del self.task_chunks[task_id]
            else:
                existing_chunk.duration -= remove_amount
                if existing_chunk.duration <= 0:
                    del self.task_chunks[task_id]

    def get_available_time(self):
        used_time = sum(chunk["chunk"].duration for chunk in self.task_chunks.values())
        if self.duration is None:
            return 0
        return max(0, (self.duration * (1 - self.buffer_ratio)) - used_time)

    def get_capacity(self):
        return max(0, (self.duration * (1 - self.buffer_ratio)))


class TaskChunk:
    def __init__(self, task, duration, timeblock_ratings=None, auto=False, manual=False, assigned=False,
                 flagged=False):
        """
        :param task: The task object this chunk belongs to.
        :param duration: Duration of the chunk.
        :param timeblock_ratings: Ratings associated with different timeblocks.
        :param status: Current status of the chunk.
        :param auto: Boolean indicating if auto-scheduling was used.
        :param manual: Boolean indicating if manually scheduled.
        :param assigned: Boolean indicating if the chunk has been assigned.
        :param flagged: Boolean indicating if the chunk is flagged.
        """
        self.task = task
        self.duration = duration
        self.timeblock_ratings = timeblock_ratings
        self.auto = auto
        self.manual = manual
        self.assigned = assigned
        self.flagged = flagged

    def split(self, ratios):
        total_ratio = sum(ratios)
        return [TaskChunk(self.task, (self.duration * r) / total_ratio, self.timeblock_ratings, self.auto, self.manual,
                          self.assigned,
                          self.flagged) for r in ratios]


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

        self.active_tasks = self.task_manager_instance.get_active_tasks()
        self.update_task_global_weights()

        self.day_schedules = self.load_day_schedules()

        self.estimate_daily_buffer_ratios()

        self.chunks = self.chunk_tasks()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS time_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT DEFAULT '',
                    schedule TEXT DEFAULT '{}',
                    list_categories TEXT DEFAULT '{"include": [], "exclude": []}',
                    task_tags TEXT DEFAULT '{"include": [], "exclude": []}',
                    color TEXT DEFAULT ''
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
                schedule = json.loads(row['schedule']) if row['schedule'] else {}
                list_categories = json.loads(row['list_categories']) if row['list_categories'] else {"include": [],
                                                                                                     "exclude": []}
                task_tags = json.loads(row['task_tags']) if row['task_tags'] else {"include": [], "exclude": []}

                # Convert color string to a tuple, if provided (e.g., "(255,200,200)")
                color_str = row['color']
                if color_str:
                    try:
                        color = tuple(map(int, color_str.strip('()').split(',')))
                    except Exception:
                        color = None
                else:
                    color = None

                block = {
                    "id": row["id"],
                    "name": row["name"],
                    "schedule": schedule,  # e.g., {"wed": ["09:00", "10:00"]}
                    "list_categories": list_categories,
                    "task_tags": task_tags,
                    "color": color
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

    def add_time_block(self, time_block):
        """
        Insert a new time block into the database and add it to the in-memory structure.
        The time_block object is expected to have attributes:
          - name, schedule (a dict), list_categories, task_tags, and color.
        """
        try:
            schedule_json = json.dumps(time_block.schedule) if hasattr(time_block, 'schedule') else json.dumps({})
            list_cats_json = json.dumps(time_block.list_categories) if hasattr(time_block,
                                                                               'list_categories') else json.dumps(
                {"include": [], "exclude": []})
            task_tags_json = json.dumps(time_block.task_tags) if hasattr(time_block, 'task_tags') else json.dumps(
                {"include": [], "exclude": []})
            color_str = str(time_block.color) if hasattr(time_block, 'color') and time_block.color else ""

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO time_blocks (
                    name,
                    schedule,
                    list_categories,
                    task_tags,
                    color
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                time_block.name,
                schedule_json,
                list_cats_json,
                task_tags_json,
                color_str
            ))
            self.conn.commit()

            # Update the time block's ID and add it to the in-memory list
            time_block.id = cursor.lastrowid
            self.time_blocks.append({
                "id": time_block.id,
                "name": time_block.name,
                "schedule": time_block.schedule,
                "list_categories": time_block.list_categories,
                "task_tags": time_block.task_tags,
                "color": time_block.color
            })

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
        Remove a time block from both the database and the in-memory structure.
        """
        try:
            # Find the block in memory
            block_to_remove = None
            for block in self.time_blocks:
                if block["id"] == block_id:
                    block_to_remove = block
                    break

            if not block_to_remove:
                print(f"Time block with ID {block_id} not found in memory")
                return False

            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM time_blocks WHERE id = ?", (block_id,))
            if cursor.rowcount == 0:
                print(f"Time block with ID {block_id} not found in database")
                return False
            self.conn.commit()

            # Remove from in-memory structure
            self.time_blocks.remove(block_to_remove)
            cursor.close()
            return True

        except sqlite3.Error as e:
            print(f"Database error while removing time block: {e}")
            self.conn.rollback()
            raise
        except Exception as e:
            print(f"Unexpected error removing time block: {e}")
            self.conn.rollback()
            raise

    def update_time_block(self, updated_block):
        """
        Update an existing time block in both the database and the in-memory structure.
        The updated_block is a dictionary that must include the "id" key.
        """
        try:
            block_id = updated_block["id"]
            # Locate the block in the in-memory structure
            existing_index = None
            for i, block in enumerate(self.time_blocks):
                if block["id"] == block_id:
                    existing_index = i
                    break

            if existing_index is None:
                print(f"Time block with ID {block_id} not found in memory.")
                return False

            schedule_json = json.dumps(updated_block.get("schedule", {}))
            list_cats_json = json.dumps(updated_block.get("list_categories", {"include": [], "exclude": []}))
            task_tags_json = json.dumps(updated_block.get("task_tags", {"include": [], "exclude": []}))
            color_str = str(updated_block.get("color")) if updated_block.get("color") else ""

            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE time_blocks
                SET
                    name = ?,
                    schedule = ?,
                    list_categories = ?,
                    task_tags = ?,
                    color = ?
                WHERE id = ?
            """, (
                updated_block.get("name", ""),
                schedule_json,
                list_cats_json,
                task_tags_json,
                color_str,
                block_id
            ))
            if cursor.rowcount == 0:
                print(f"Time block with ID {block_id} not found in database.")
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
        """
        Given a date (a datetime.date object), check the in-memory time_blocks
        (each a dictionary with keys: name, schedule, list_categories, task_tags, color, etc.)
        and for each user-defined block that has an entry for the day of the week,
        initialize and return a list of TimeBlock objects for that day.

        The schedule field is expected to be a dict with day keys (e.g., "wed") and
        values as a list/tuple of two strings representing start and end times in "%H:%M" format.
        """
        # Get the day abbreviation in lower-case (e.g., "wed")
        day_abbr = given_date.strftime("%a").lower()
        result = []

        # Iterate over the loaded timeblocks
        for block in self.time_blocks:
            schedule = block.get("schedule", {})
            if day_abbr in schedule:
                time_range = schedule[day_abbr]
                # Expect time_range to be a list/tuple with two items: [start_str, end_str]
                if isinstance(time_range, (list, tuple)) and len(time_range) == 2:
                    start_str, end_str = time_range
                    try:
                        start_time = datetime.strptime(start_str, "%H:%M").time()
                        end_time = datetime.strptime(end_str, "%H:%M").time()
                    except Exception as e:
                        print(f"Error parsing time in block {block.get('id')}: {e}")
                        continue

                    # Initialize a new TimeBlock object for the given date.
                    new_block = TimeBlock(
                        block_id=None,  # Unique id will be assigned automatically.
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
                    # Handle cases where the end time might be past midnight.
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    new_block.duration = (end_dt - start_dt).total_seconds() / 3600.0

                    result.append(new_block)
        return result

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

        max_added_time = max(
            (datetime.now() - task.added_date_time).total_seconds()
            for task in self.active_tasks if task.added_date_time
        ) if any(task.added_date_time for task in self.active_tasks) else 1

        max_time_estimate = max(task.time_estimate for task in self.active_tasks if task.time_estimate) or 1

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
        schedule = self.load_schedule(date)
        if schedule:
            return schedule
        else:
            return DaySchedule(self, date)

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
                day_schedule.assign_buffer_ratio(1.0 - (day_workload_est / day_eat))
            else:
                day_schedule.assign_buffer_ratio(0.0)

    def chunk_tasks(self):
        chunks = []
        for task in self.active_tasks:
            # Calculate the remaining duration for the task.
            remaining_duration = task.time_estimate - task.time_logged

            # Process manually scheduled tasks.
            if task.manually_scheduled:
                if hasattr(task, 'manually_scheduled_chunks') and task.manually_scheduled_chunks:
                    # Assume manually_scheduled_chunks is a list of dictionaries.
                    for chunk_info in task.manually_scheduled_chunks:
                        chunk_duration = chunk_info.get("duration", 0)
                        if chunk_duration > 0:
                            chunk = TaskChunk(
                                task=task,
                                duration=chunk_duration,
                                manual=True
                            )
                            chunks.append(chunk)
                            remaining_duration -= chunk_duration

                # If any remaining duration exists.
                if remaining_duration > 0:
                    if task.auto_chunk:
                        chunk = TaskChunk(
                            task=task,
                            duration=remaining_duration,
                            auto=True
                        )
                        chunks.append(chunk)
                    else:
                        chunk = TaskChunk(
                            task=task,
                            duration=remaining_duration,
                            assigned=True
                        )
                        chunks.append(chunk)
            # Process tasks that are assigned.
            elif hasattr(task, 'assigned_chunks') and task.assigned_chunks:
                for assigned_chunk in task.assigned_chunks:
                    chunk_duration = assigned_chunk.get("duration", 0)
                    if chunk_duration > 0:
                        chunk = TaskChunk(
                            task=task,
                            duration=chunk_duration,
                            assigned=True
                        )
                        chunks.append(chunk)
            # Process tasks that are not manually scheduled and use auto chunking.
            else:
                if task.auto_chunk:
                    chunk = TaskChunk(
                        task=task,
                        duration=remaining_duration,
                        auto=True
                    )
                    chunks.append(chunk)
        return chunks

    # returns a bool for success
    def assign_chunk(self, chunk, exclude_block=None, test=False):
        """
        Attempt to assign a TaskChunk (chunk) to one of the candidate timeblocks.

        For auto chunks, if capacity is insufficient, it will attempt to split the chunk
        and free capacity by reassigning lower-rated auto chunks.

        For assigned (non-auto) chunks, the same candidate loop is used, but the current
        chunk is not split; instead, lower-rated chunks are re-assigned to free space.

        Returns True if the assignment is successful; otherwise, flags the chunk and returns False.
        """
        task = chunk.task
        if not chunk.timeblock_ratings:
            chunk.flagged = True
            return False

        # Sort candidate timeblocks (each a tuple: (block, rating)) by descending rating.
        sorted_candidates = sorted(chunk.timeblock_ratings, key=lambda x: x[1], reverse=True)

        if chunk.auto:
            FLEXIBILITY_MAP = {
                "Strict": 1,
                "Flexible": 2,
                "Very Flexible": 3
            }
            flexibility_ratio = FLEXIBILITY_MAP[task.flexibility] / max(FLEXIBILITY_MAP.values())
            required_capacity = task.time_estimate - task.time_logged
            num_top_candidates = max(1, int(len(sorted_candidates) * flexibility_ratio))

            # Select only the top candidates and filter out the exclude_block.
            top_candidates = [cand for cand in sorted_candidates[:num_top_candidates]
                              if cand[0].id != (exclude_block.id if exclude_block else None)]

            for candidate in top_candidates:
                block, rating = candidate
                # Gather lower-rated chunks from this block that are not manually scheduled.
                filtered_chunks = sorted(
                    [ci["chunk"] for ci in block.task_chunks.values() if ci["rating"] < rating],
                    key=lambda c: c.duration
                )
                filtered_chunks = [c for c in filtered_chunks if not c.manual]

                if block.get_available_time() >= required_capacity:
                    if not test:
                        block.add_chunk(chunk, rating)
                    return True
                else:
                    if not filtered_chunks:
                        continue
                    resizable_capacity = 0.0
                    reschedule_chunk_queue = []
                    for filtered_chunk in filtered_chunks:
                        if filtered_chunk.assigned or filtered_chunk.auto:
                            if self.assign_chunk(filtered_chunk, block, True):
                                resizable_capacity += filtered_chunk.get_capacity()
                                reschedule_chunk_queue.append(filtered_chunk)
                        elif filtered_chunk.auto:
                            flexibility_ratio_auto = FLEXIBILITY_MAP[filtered_chunk.task.flexibility] / max(
                                FLEXIBILITY_MAP.values())
                            if flexibility_ratio_auto >= flexibility_ratio:
                                av = filtered_chunk.duration - (required_capacity - resizable_capacity)
                                if av > 0:
                                    sp = filtered_chunk.split([av, filtered_chunk.duration - av])
                                    if self.assign_chunk(sp[1], block, True):
                                        resizable_capacity += sp[1].get_capacity()
                                        reschedule_chunk_queue.append(sp[1])
                        # End inner loop.
                    # Check if the freed capacity is nearly enough to accommodate the entire chunk.
                    if resizable_capacity >= 0.9 * required_capacity:
                        available_for_this_block = block.get_available_time() + resizable_capacity
                        if available_for_this_block < chunk.duration:
                            sp = chunk.split([available_for_this_block, chunk.duration - available_for_this_block])
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
        elif chunk.assigned:
            # For assigned chunks, the current chunk is not split.
            for candidate in sorted_candidates:
                block, rating = candidate
                if exclude_block and block.id == exclude_block.id:
                    continue
                if block.get_available_time() >= chunk.duration:
                    if not test:
                        block.add_chunk(chunk, rating)
                    return True
                else:
                    # Try to free capacity by reassigning lower-rated chunks.
                    filtered_chunks = sorted(
                        [ci["chunk"] for ci in block.task_chunks.values() if ci["rating"] < rating],
                        key=lambda c: c.duration
                    )
                    filtered_chunks = [c for c in filtered_chunks if not c.manual]
                    if not filtered_chunks:
                        continue
                    resizable_capacity = 0.0
                    reschedule_chunk_queue = []
                    for filtered_chunk in filtered_chunks:
                        if filtered_chunk.assigned or filtered_chunk.auto:
                            if self.assign_chunk(filtered_chunk, block, True):
                                resizable_capacity += filtered_chunk.get_capacity()
                                reschedule_chunk_queue.append(filtered_chunk)
                    if resizable_capacity >= chunk.duration:
                        for reschedule_chunk in reschedule_chunk_queue:
                            block.remove_chunk(reschedule_chunk)
                            self.assign_chunk(reschedule_chunk, block)
                        if not test:
                            block.add_chunk(chunk, rating)
                        return True
        # If no candidate block can accept the chunk, flag it.
        chunk.flagged = True
        return False

    def generate_schedule(self):
        for chunk in self.chunks:
            # If the chunk is manually scheduled, assume it's pre-assigned.
            if chunk.manual:
                # Implement custom manual assignment logic if needed.
                # ---
                continue

            chunk.timeblock_ratings = []
            for day in self.day_schedules:
                if chunk.task.due_datetime and day.date > chunk.task.due_datetime.date():
                    break
                ratings = day.get_suitable_timeblocks_with_rating(chunk)
                chunk.timeblock_ratings.extend(ratings)

            chunk.timeblock_ratings.sort(key=lambda x: x[1], reverse=True)

            self.assign_chunk(chunk)


class DaySchedule:
    def __init__(self, schedule_manager_instance, date):
        self.date = date
        self.schedule_manager_instance = schedule_manager_instance
        self.task_manager_instance = self.schedule_manager_instance.task_manager_instance
        self.schedule_settings = self.schedule_manager_instance.schedule_settings

        self.sleep_time = self.schedule_settings.ideal_sleep_duration
        self.time_blocks = self.generate_schedule()

        self.buffer_ratio = 0.0
        self.reserved_time = 0.0

    def assign_buffer_ratio(self, buffer_ratio):
        self.buffer_ratio = buffer_ratio
        for block in self.time_blocks:
            block.buffer_ratio = buffer_ratio

    def generate_schedule(self):
        target_day_str = self.date.strftime('%A').lower()
        # day_start is the user's wake time (e.g., 8:00 AM)
        day_start = datetime.combine(self.date, self.schedule_settings.day_start)
        # Define day_end as midnight (start of next day)
        day_end = datetime.combine(self.date + timedelta(days=1), time(0, 0))

        # Set sleep block using self.sleep_time: sleep from (day_start - sleep_time) to day_start
        sleep_start = day_start - timedelta(hours=self.sleep_time)
        sleep_end = day_start
        sleep_block = TimeBlock(
            block_id=None,
            name=f"Sleep ({self.sleep_time:.1f}h)",
            schedule={target_day_str: (sleep_start.time(), sleep_end.time())},
            block_type="unavailable",
            color=(173, 216, 230)
        )
        sleep_block.start_time = sleep_start.time()
        sleep_block.end_time = sleep_end.time()
        sleep_block.duration = (sleep_end - sleep_start).total_seconds() / 3600

        # Filter user-defined blocks for the awake period (from day_start to day_end)
        user_blocks = self.schedule_manager_instance.get_user_defined_timeblocks_for_date(self.date)
        user_blocks.sort(key=lambda b: b.start_time)

        final_blocks = []
        # First, add the sleep block (from sleep_start to day_start)
        final_blocks.append(sleep_block)

        # Now fill the awake period with user-defined blocks and system-defined gap blocks
        current_dt = day_start
        for block in user_blocks:
            block_start_dt = datetime.combine(self.date, block.start_time)
            if current_dt < block_start_dt:
                gap_block = TimeBlock(
                    block_id=None,
                    name="Unscheduled",
                    schedule={target_day_str: (current_dt.time(), block_start_dt.time())},
                    block_type="system_defined",
                    color=(200, 200, 200)
                )
                gap_block.start_time = current_dt.time()
                gap_block.end_time = block_start_dt.time()
                gap_block.duration = (block_start_dt - current_dt).total_seconds() / 3600
                final_blocks.append(gap_block)
            final_blocks.append(block)
            current_dt = datetime.combine(self.date, block.end_time)

        # Fill any remaining gap until day_end with a system-defined block
        if current_dt < day_end:
            gap_block = TimeBlock(
                block_id=None,
                name="Unscheduled",
                schedule={target_day_str: (current_dt.time(), day_end.time())},
                block_type="system_defined",
                color=(200, 200, 200)
            )
            gap_block.start_time = current_dt.time()
            gap_block.end_time = day_end.time()
            gap_block.duration = (day_end - current_dt).total_seconds() / 3600
            final_blocks.append(gap_block)

        return final_blocks

    # Helper function: determine if a task qualifies for a given block.
    def qualifies(self, task, block):
        # Check list_categories restrictions.
        if block.list_categories:
            include_cats = block.list_categories.get("include", [])
            exclude_cats = block.list_categories.get("exclude", [])
            # Assume task.list_name represents its category.
            cat = self.task_manager_instance.get_task_list_category_name(task.list_name)
            if include_cats and cat not in include_cats:
                return False
            if exclude_cats and cat in exclude_cats:
                return False

        # Check task_tags restrictions.
        if block.task_tags:
            include_tags = block.task_tags.get("include", [])
            exclude_tags = block.task_tags.get("exclude", [])
            # Assume task.tags is a list of tag strings.
            if include_tags and not any(tag in include_tags for tag in task.tags):
                return False
            if exclude_tags and any(tag in exclude_tags for tag in task.tags):
                return False

        return True

    def get_eat(self, task=None):
        """
        Calculate Effective Available Time (EAT) as the sum of durations of all blocks
        where tasks can be scheduled (i.e., blocks not marked as "unavailable").
        If a task is provided, only consider blocks that the task qualifies for,
        taking into account restrictions on list categories, tags, and task IDs.
        """
        if task:
            candidate_total = 0.0
            for block in self.time_blocks:
                if block.block_type == "unavailable":
                    continue
                duration = block.get_available_time()
                if self.qualifies(task, block):
                    candidate_total += duration

            return candidate_total
        else:
            total_available = 0.0
            for block in self.time_blocks:
                if block.block_type != "unavailable":
                    total_available += block.get_available_time()
            return total_available

    def get_suitable_timeblocks_with_rating(self, chunk):
        """
        Given a TaskChunk (chunk), return a sorted list of tuples (timeblock, rating)
        for each timeblock in this DaySchedule that is suitable for scheduling the chunk.

        The rating is computed based on:
          - Date: closer due dates boost rating; high priority tasks get bonus for days close to today.
          - Preferred work days: if the day matches task.preferred_work_days.
          - Preferred time of day: bonus if the block’s start_time is in a preferred interval.
          - Productivity hours: bonus based on task.effort_level and whether the block is within peak/off-peak hours.
          - Capacity: if not auto_chunk, a block that cannot hold the chunk duration is penalized.
          - If auto_chunk is True, a maximum rating is assigned.
        """
        from datetime import datetime, time, timedelta

        def compute_time_bonus(t, interval, max_bonus, threshold=60):
            """
            Compute a bonus based on how close time 't' (a time object) is to the given interval.
            Returns a bonus between 0 and max_bonus.
            """

            def to_minutes(t_obj):
                return t_obj.hour * 60 + t_obj.minute

            t_val = to_minutes(t)
            start_val = to_minutes(interval[0])
            end_val = to_minutes(interval[1])
            # Adjust if the interval spans midnight.
            if start_val > end_val:
                if t_val < start_val:
                    t_val += 24 * 60
                end_val += 24 * 60

            if start_val <= t_val <= end_val:
                return max_bonus
            elif t_val < start_val:
                diff = start_val - t_val
                return max_bonus * (1 - diff / threshold) if diff <= threshold else 0
            else:  # t_val > end_val
                diff = t_val - end_val
                return max_bonus * (1 - diff / threshold) if diff <= threshold else 0

        suitable = []
        task = chunk.task
        today = datetime.now().date()

        for block in self.time_blocks:
            # Skip unavailable blocks.
            if block.block_type == "unavailable":
                continue
            if not self.qualifies(task, block):
                continue

            # Capacity check.
            if not task.auto_chunk:
                if block.get_available_time() < chunk.duration:
                    continue

            rating = 0

            # 1. Date factor: Boost if the task's due date is near this schedule's date.
            if task.due_datetime:
                days_until_due = (task.due_datetime.date() - self.date).days
                rating += 100 / (days_until_due + 1)  # the closer, the higher the boost

            # 2. Priority factor: For high priority tasks, days close to today get bonus.
            days_from_today = (self.date - today).days
            if task.priority >= 8:
                rating += max(0, 100 - days_from_today * 10)

            # 3. Preferred work days.
            if hasattr(task, "preferred_work_days") and task.preferred_work_days:
                if self.date.strftime("%A") in task.preferred_work_days:
                    rating += 50

            # 4. Preferred time of day.
            preferred_intervals = {
                "Morning": (time(6, 0), time(10, 0)),
                "Afternoon": (time(12, 0), time(16, 0)),
                "Evening": (time(16, 0), time(20, 0)),
                "Night": (time(20, 0), time(23, 0))
            }
            if hasattr(task, "time_of_day_preference") and task.time_of_day_preference:
                for pref in task.time_of_day_preference:
                    if pref in preferred_intervals:
                        bonus = compute_time_bonus(block.start_time, preferred_intervals[pref], 50)
                        rating += bonus
                        break

            # 5. Productivity hours based on task effort level.
            if hasattr(task, "effort_level"):
                if task.effort_level == "High":
                    peak_start, peak_end = self.schedule_settings.peak_productivity_hours
                    bonus = compute_time_bonus(block.start_time, (peak_start, peak_end), 50)
                    rating += bonus
                elif task.effort_level == "Low":
                    off_start, off_end = self.schedule_settings.off_peak_hours
                    bonus = compute_time_bonus(block.start_time, (off_start, off_end), 30)
                    rating += bonus

            suitable.append((block, rating))

        # Sort the candidate timeblocks by descending rating.
        suitable.sort(key=lambda x: x[1], reverse=True)
        return suitable
