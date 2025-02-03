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
        self.task_chunks = {}  # Mapping: task.id -> { "task": task, "duration": ..., "score": ..., "auto_chunk": bool }
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.buffer_ratio = 0.0

    def add_chunk(self, task, duration, score, auto_chunk=True):
        task_id = task.id if hasattr(task, 'id') else uuid.uuid4().int
        if task_id in self.task_chunks:
            self.task_chunks[task_id]["duration"] += duration
            # Optionally update score if desired.
        else:
            self.task_chunks[task_id] = {"task": task, "duration": duration, "score": score, "auto_chunk": auto_chunk}
        return 0  # In this design, assume the entire duration is scheduled if free_time permits.

    def remove_chunk(self, task, remove_amount):
        """
        Remove remove_amount of chunk time from the scheduled chunk for task.
        If the chunk is auto-scheduled, remove only the needed amount (or the entire chunk if remove_amount >= chunk size).
        If the chunk is manually scheduled, remove the entire chunk regardless.
        """
        task_id = task.id if hasattr(task, 'id') else None
        if task_id and task_id in self.task_chunks:
            chunk = self.task_chunks[task_id]
            if not chunk.get("auto_chunk"):
                # For manually scheduled chunks, remove the entire chunk.
                del self.task_chunks[task_id]
            else:
                # For auto-scheduled chunks, remove only what is needed.
                chunk["duration"] -= remove_amount
                if chunk["duration"] <= 0:
                    del self.task_chunks[task_id]

    def get_available_time(self):
        used_time = sum(chunk["duration"] for chunk in self.task_chunks.values())
        # Assume that self.duration is the full duration of the block.
        # The effective capacity is reduced by the buffer_ratio.
        if self.duration is None:
            return 0
        return max(0, (self.duration * (1 - self.buffer_ratio)) - used_time)


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

        self.avg_buffer_ration = self.get_avg_buffer_ratio()

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
        """Generates a schedule from today up to the farthest due date, ensuring a minimum of 21 days."""
        today = datetime.now().date()
        latest_due_date = max((task.due_datetime.date() for task in self.active_tasks), default=None)

        end_date = max(today + timedelta(days=20), latest_due_date) if latest_due_date else today + timedelta(days=20)

        return [DaySchedule(self, date) for date in
                (today + timedelta(days=i) for i in range((end_date - today).days + 1))]

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

    def generate_schedule(self):
        """
        For each task:
          - If the task is manually scheduled (manually_scheduled == True), assign its
            manually scheduled chunks (from manually_scheduled_chunks) first.
          - For the remaining time:
              - Evaluate candidate days (only days before the task’s due date, if defined)
                and compute a suitability rating for each.
              - Then, if the task is auto-chunked, split the remaining time intelligently:
                  * A task’s flexibility dictates into how many chunks it should be split.
                  * High-rated candidate days will receive larger chunks while lower-rated days get smaller chunks.
                  * If there is excess remaining time, try assigning additional chunks across candidate days.
              - Else if the task is manually chunked (predefined chunks in assigned_chunks), assign each chunk to the first candidate day with enough free time.
              - Otherwise, assign the entire remaining time to the best candidate day.
          - Finally, flag the task if it couldn’t be fully scheduled.
        """
        # Clear the task-day rating matrix.
        self.task_day_rating_matrix = {}

        # Sort tasks by global weight (highest first)
        tasks = sorted(self.active_tasks, key=lambda t: t.global_weight, reverse=True)

        for task in tasks:
            self.task_day_rating_matrix[task.id] = {}
            candidate_days = []
            remaining_time = task.time_estimate - task.time_logged

            # --- 1. Manually Scheduled Chunks (User-interacted chunks) ---
            if task.manually_scheduled and hasattr(task,
                                                   'manually_scheduled_chunks') and task.manually_scheduled_chunks:
                for chunk in task.manually_scheduled_chunks:
                    # Each chunk is expected as a dict with keys: 'date', 'timeblock', and 'duration'
                    chunk_date = chunk.get('date')
                    chunk_duration = chunk.get('duration', 0)
                    for day in self.day_schedules:
                        if day.date == chunk_date:
                            day.add_task_chunk(task, chunk_duration)
                            remaining_time -= chunk_duration
                            break  # Process next manually scheduled chunk

            # --- 2. Evaluate Candidate Days ---
            for day in self.day_schedules:
                # Skip days after the task’s due date, if defined.
                if task.due_datetime and day.date > task.due_datetime.date():
                    continue
                rating = self.compute_suitability_rating(task, day)
                self.task_day_rating_matrix[task.id][day.date] = rating
                candidate_days.append((day, rating))
            candidate_days.sort(key=lambda x: x[1], reverse=True)

            if remaining_time <= 0:
                continue  # Task fully scheduled via manual chunks.

            # --- 3. Auto-Chunking Based on Flexibility and Candidate Day Ratings ---
            if task.auto_chunk:
                # Decide desired number of chunks based on task flexibility.
                if task.flexibility == "Strict":
                    desired_chunks = 1 if remaining_time <= 3 else 2
                elif task.flexibility == "Flexible":
                    # For flexible tasks, try splitting into roughly one chunk per 2 hours of work.
                    desired_chunks = min(len(candidate_days), max(1, int(remaining_time // 2)))
                elif task.flexibility == "Very Flexible":
                    # Very flexible tasks can be split more finely.
                    desired_chunks = min(len(candidate_days), max(1, int(remaining_time)))
                else:
                    desired_chunks = 1

                # Select the top candidate days for initial assignment.
                selected_candidates = candidate_days[:desired_chunks]
                total_rating = sum(rating for _, rating in selected_candidates)

                # Distribute remaining_time among selected candidate days proportionally to their rating.
                for day, rating in selected_candidates:
                    if total_rating > 0:
                        proposed_chunk = remaining_time * (rating / total_rating)
                    else:
                        proposed_chunk = remaining_time
                    free_time = day.get_eat(task)
                    chunk = min(proposed_chunk, free_time)
                    day.add_task_chunk(task, chunk)
                    remaining_time -= chunk
                    total_rating -= rating
                    if remaining_time <= 0:
                        break

                # If there is still remaining time, iterate over all candidate days to assign additional chunks.
                if remaining_time > 0:
                    for day, rating in candidate_days:
                        free_time = day.get_eat(task)
                        if free_time > 0:
                            chunk = min(remaining_time, free_time)
                            day.add_task_chunk(task, chunk)
                            remaining_time -= chunk
                        if remaining_time <= 0:
                            break

            # --- 4. Manually Chunked Tasks (Predefined chunks) ---
            elif hasattr(task, 'assigned_chunks') and task.assigned_chunks:
                for chunk in task.assigned_chunks:
                    chunk_assigned = False
                    for day, rating in candidate_days:
                        free_time = day.get_eat(task)
                        if free_time >= chunk:
                            day.add_task_chunk(task, chunk)
                            remaining_time -= chunk
                            chunk_assigned = True
                            break
                    if not chunk_assigned:
                        # If a chunk cannot be assigned, break and flag the task.
                        remaining_time = chunk
                        break

            # --- 5. Non-Chunked Tasks ---
            else:
                if candidate_days:
                    best_day, _ = candidate_days[0]
                    free_time = best_day.get_eat(task)
                    if free_time >= remaining_time:
                        best_day.add_task_chunk(task, remaining_time)
                        remaining_time = 0

            # Flag the task if it couldn’t be fully scheduled.
            task.flagged = remaining_time > 0

    def compute_suitability_rating(self, task, day):
        """
        Compute a numeric suitability rating for scheduling a task on a given day.
        Factors include:
          - Task's global weight (scaled)
          - Whether the day matches the task's preferred workdays
          - Whether the day's effective available time can cover the task
          - The task's priority and effort level.
        """
        rating = 0
        # Base rating from global weight (scaled)
        rating += task.global_weight * 100

        # Adjust based on preferred workdays.
        day_name = day.date.strftime('%A')
        if hasattr(task, 'preferred_work_days') and task.preferred_work_days:
            rating += 20 if day_name in task.preferred_work_days else -10

        # Consider available time.
        rating += 15 if day.get_eat(task) >= task.time_estimate else -15

        # Add task priority.
        rating += task.priority

        # Factor in effort level.
        effort_bonus = {"Low": 5, "Medium": 0, "High": -5}
        rating += effort_bonus.get(task.effort_level, 0)

        return rating


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

    def add_task_chunk(self, task, chunk_size):
        """
        Add a chunk of the task to this day's schedule.

        If the task is manually scheduled and has a designated chunk for this day,
        assign it to the specified time block.

        Otherwise, for auto-chunking, select the best candidate time block(s)
        based on the task's time_of_day_preference and effort level. In each candidate
        block, if the block does not have enough free time, then rank the already
        scheduled (auto-scheduled) chunks in that block and, if the current task is more
        suitable (has a higher score), remove the lower-scoring chunks to free space.
        Removed chunks will be re-assigned later via a recursive call.

        Finally, if the block still cannot take the full chunk, the method will try
        splitting the chunk among multiple blocks.

        Manually scheduled chunks are never bumped.
        """

        def compute_time_bonus(t, interval, max_bonus, threshold=60):
            """
            t: a time object (the block's start_time)
            interval: a tuple of (start_time, end_time) for the preferred period
            max_bonus: maximum bonus to award if t is within the interval
            threshold: minutes outside the interval over which the bonus tapers to 0.
            Returns a bonus value between 0 and max_bonus.
            """

            # Convert time to minutes since midnight.
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
                if diff <= threshold:
                    return max_bonus * (1 - diff / threshold)
                else:
                    return 0
            else:  # t_val > end_val
                diff = t_val - end_val
                if diff <= threshold:
                    return max_bonus * (1 - diff / threshold)
                else:
                    return 0

        candidate_blocks = [block for block in self.time_blocks if block.block_type != "unavailable"]
        candidate_blocks = [block for block in self.time_blocks if self.qualifies(task, block)]
        # --- 1. If the task is manually scheduled for this day, honor its designated block ---
        if task.manually_scheduled and isinstance(task.manually_scheduled_chunks, dict):
            # Expecting keys: "date", "timeblock", and "duration"
            scheduled_date = task.manually_scheduled_chunks.get("date")
            if scheduled_date is not None and scheduled_date == self.date:
                designated_block_name = task.manually_scheduled_chunks.get("timeblock")
                designated_duration = task.manually_scheduled_chunks.get("duration")
                if designated_block_name and designated_duration:
                    scheduled_chunk = min(chunk_size, designated_duration)
                    for block in candidate_blocks:
                        if block.name == designated_block_name:
                            block.add_chunk(task, scheduled_chunk, 10000, auto_chunk=False)
                            return True
            return False

        # --- 2. Compute scores for candidate blocks for the current task ---
        scored_blocks = []
        # Define preferred intervals (tweak as needed)
        preferred_intervals = {
            "Morning": (time(6, 0), time(10, 0)),
            "Afternoon": (time(12, 0), time(16, 0)),
            "Evening": (time(16, 0), time(20, 0)),
            "Night": (time(20, 0), time(23, 0))
        }
        for block in candidate_blocks:
            free_time = block.get_available_time()  # Returns block.duration minus already scheduled time.
            if free_time <= 0:
                continue

            # Base score: available free time.
            score = free_time

            # Bonus for time-of-day preference.
            if hasattr(task, "time_of_day_preference") and task.time_of_day_preference:
                for pref in task.time_of_day_preference:
                    if pref in preferred_intervals:
                        bonus = compute_time_bonus(block.start_time, preferred_intervals[pref], 50)
                        score += bonus
                        break

            # Effort level adjustments using closeness.
            if hasattr(task, "effort_level"):
                if task.effort_level == "High":
                    peak_start, peak_end = self.schedule_settings.peak_productivity_hours
                    bonus = compute_time_bonus(block.start_time, (peak_start, peak_end), 50)
                    score += bonus
                elif task.effort_level == "Low":
                    off_start, off_end = self.schedule_settings.off_peak_hours
                    bonus = compute_time_bonus(block.start_time, (off_start, off_end), 30)
                    score += bonus

            scored_blocks.append((block, score, free_time))
        # Sort candidate blocks by descending score.
        scored_blocks.sort(key=lambda x: x[1], reverse=True)

        remaining = chunk_size

        if hasattr(task, "assigned_chunks") and task.assigned_chunks:
            for block, score, free_time in scored_blocks:
                if free_time >= chunk_size:
                    block.add_chunk(task, chunk_size, score, auto_chunk=False)
                    return True
            return False

        # --- 3. Try to assign the entire chunk in one block, possibly bumping lower-scored chunks ---
        if task.auto_chunk:
            for block, score, free_time in scored_blocks:
                if remaining <= 0:
                    break

                # If there is enough free time, simply attempt to add the chunk.
                if free_time >= remaining:
                    block.add_chunk(task, remaining, score)
                    break
                else:
                    # Not enough free time. See if we can bump some auto-scheduled (non-manually scheduled) chunks.
                    needed = remaining - free_time
                    # Gather removable chunks from this block.
                    # Each scheduled chunk is assumed to be a dict with keys:
                    # "task", "chunk_size", "score", and "manually_scheduled" (bool).
                    removable = []
                    for chunk in getattr(block, "task_chunks", {}):
                        if chunk.get("auto_chunk", False):
                            # Use the stored "score" (or compute a similar score) for the scheduled chunk.
                            rem_score = chunk.get("score", 0)
                            removable.append(chunk)
                    # Sort removable chunks by score (lowest first).
                    removable.sort(key=lambda c: c.get("score", 0))
                    freed = 0
                    removed_chunks = []
                    for rchunk in removable:
                        # Only remove if current block score (for current task) is higher.
                        if rchunk.get("score", 0) < score:
                            freed += rchunk["chunk_size"]
                            removed_chunks.append(rchunk)
                            if freed >= needed:
                                break
                    # If we managed to free enough space, remove those chunks.
                    if freed >= needed:
                        # Remove each bumped chunk from the block.
                        for rchunk in removed_chunks:
                            block.remove_chunk(rchunk, freed)
                            freed -= rchunk["chunk_size"]
                        # Now, free_time is increased by the total removed amount.
                        new_free_time = block.get_available_time()
                        if new_free_time >= remaining:
                            block.add_chunk(task, remaining, score)
                            # Attempt to reassign bumped chunks to other candidate blocks.
                            for rchunk in removed_chunks:
                                # Reassign the removed chunk by recursively calling add_task_chunk.
                                self.add_task_chunk(rchunk["task"], rchunk["chunk_size"])
                            break

        # --- 4. If after checking all candidate blocks the entire chunk is not assigned,
        # try splitting it among multiple blocks (if the task is flexible).
        if remaining > 0 and task.flexibility != "Strict":
            for block, score, free_time in scored_blocks:
                if remaining <= 0:
                    break
                avail = block.get_available_time()
                if avail > 0:
                    assign = min(remaining, avail)
                    unscheduled = block.add_chunk(task, assign)
                    remaining = remaining - (assign - unscheduled)
                    if remaining <= 0:
                        break

        # --- 5. Update internal mapping and return unscheduled portion (if any) ---
        self.task_chunks[task.id] = self.task_chunks.get(task.id, 0) + (chunk_size - remaining)
        return remaining

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
