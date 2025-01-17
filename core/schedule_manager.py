import os
import sqlite3
import json
import uuid
from datetime import datetime, date, time, timedelta
import random
from core.task_manager import TaskManager


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
                ideal_sleep_duration INTEGER,
                overtime_flexibility TEXT,
                hours_of_day_available INTEGER,
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
            self.ideal_sleep_duration = 8
            self.overtime_flexibility = "auto"
            self.hours_of_day_available = None
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
            task_manager_instance=None,
            name="",
            schedule=None,
            list_categories=None,
            task_tags=None,
            tasks=None,
            block_type="user_defined",
            color=None,
            duration=0.0
    ):
        self.id = block_id if block_id else uuid.uuid4().int
        self.task_manager_instance = task_manager_instance
        self.name = name
        self.schedule = schedule if schedule else {}
        self.list_categories = list_categories if list_categories else {"include": [], "exclude": []}
        self.task_tags = task_tags if task_tags else {"include": [], "exclude": []}
        self.tasks_dict = tasks if tasks else {"include": [], "exclude": []}
        self.block_type = block_type
        self.duration = float(duration)
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

    # def load_tasks(self):
    #     if not self.task_manager_instance:
    #         raise ValueError("task_manager_instance must be defined")
    #     for category in self.list_categories["include"]:
    #         self.tasks.extend(self.task_manager_instance.get_tasks_by_category(category))
    #     for tag in self.task_tags["include"]:
    #         self.tasks.extend(self.task_manager_instance.get_tasks_by_tag(tag))
    #     for task_id in self.tasks_dict["include"]:
    #         task = self.task_manager_instance.get_task(task_id)
    #         if task and task not in self.tasks:
    #             self.tasks.append(task)
    #     self.tasks = [
    #         task for task in self.tasks
    #         if not any(cat in self.list_categories["exclude"] for cat in task.categories)
    #            and not any(tag in self.task_tags["exclude"] for tag in task.tags)
    #            and task.id not in self.tasks_dict["exclude"] and task.include_in_schedule
    #     ]
    #     for task in self.tasks:
    #         task.currently_in_schedule = True


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
                    schedule_id INTEGER,
                    name TEXT DEFAULT '',
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    schedule TEXT DEFAULT '{}',
                    list_categories TEXT DEFAULT '{"include": [], "exclude": []}',
                    task_tags TEXT DEFAULT '{"include": [], "exclude": []}',
                    tasks TEXT DEFAULT '{"include": [], "exclude": []}',
                    block_type TEXT DEFAULT 'system_defined',
                    color TEXT DEFAULT '',
                    duration REAL DEFAULT 0.0,
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

    # ---------------------
    # MAIN SCHEDULE METHODS
    # ---------------------

    def generate_schedule(self, target_date: date):
        """
        1) Checks if a schedule for target_date exists.
           - If it does, returns it as-is, or optionally overwrite if needed.
        2) If not, it creates a fresh DaySchedule for 'target_date'.
        3) Assigns tasks (which may push some tasks out).
        4) Saves the final block structure in the schedules table.
        5) Returns the created or loaded DaySchedule.
        """
        existing_schedule = self._load_schedule_from_db(target_date)
        if existing_schedule:
            # If you want to forcibly overwrite:
            # self.reset_schedule(target_date)  # optional
            # else just return the existing schedule
            return self.load_schedule(target_date)

        # 1) Build the day schedule with relevant blocks.
        #    Possibly build from self.time_blocks or day-specific logic
        day_schedule = DaySchedule(
            date=target_date,
            time_blocks=self._get_time_blocks_for_day(target_date),
            task_manager_instance=self.task_manager_instance,
            schedule_settings=self.schedule_settings
        )

        # 2) Assign tasks to blocks
        day_schedule.assign_schedule_weights()

        # 3) Save the final schedule to DB
        self._save_schedule_to_db(target_date, day_schedule)

        return day_schedule

    def load_schedule(self, target_date: date):
        """
        Loads an existing schedule from the DB and reconstructs it
        as a DaySchedule object, or None if not found.
        """
        schedule_data = self._load_schedule_from_db(target_date)
        if not schedule_data:
            return None

        # Rebuild the time blocks
        time_blocks_dict = json.loads(schedule_data["time_blocks"])
        time_blocks = []
        for block_info in time_blocks_dict:
            tb = TimeBlock(
                block_id=block_info["id"],
                name=block_info["name"],
                schedule=block_info["schedule"],
                list_categories=block_info["list_categories"],
                task_tags=block_info["task_tags"],
                tasks=block_info["tasks"],
                block_type=block_info["block_type"],
                color=tuple(block_info["color"]) if isinstance(block_info["color"], list) else (47, 47, 47),
                duration=block_info["duration"]
            )
            time_blocks.append(tb)

        # Build the DaySchedule
        loaded_schedule = DaySchedule(
            date=target_date,
            time_blocks=time_blocks,
            task_manager_instance=self.task_manager_instance,
            schedule_settings=self.schedule_settings
        )

        return loaded_schedule

    def reset_schedule(self, target_date: date):
        """
        Resets the schedule for target_date and all future dates (not past).
        This means:
         - Setting tasks' schedule_weight=0 and currently_in_schedule=0
           for tasks scheduled on these days.
         - Removing entries from 'schedules' table for these days.
        """
        # 1) Identify all schedules from target_date onward
        self.conn.execute("""
            DELETE FROM schedules
            WHERE schedule_date >= ?
        """, (target_date.isoformat(),))

        # 2) Reset tasks that had schedule_weight != 0 and were assigned
        #    to dates >= target_date. If you store scheduled_date in tasks, do:
        #    WHERE scheduled_date >= ?
        #    For now, we reset all tasks that have schedule_weight != 0
        self.conn.execute("""
            UPDATE tasks
            SET schedule_weight = 0,
                currently_in_schedule = 0
            WHERE schedule_weight != 0
        """)

        self.conn.commit()

    # ---------------------------------------
    # HELPER METHODS FOR SCHEDULE PERSISTENCE
    # ---------------------------------------

    def _save_schedule_to_db(self, target_date: date, day_schedule):
        """
        Serializes 'DaySchedule' time_blocks into JSON and stores
        it in 'schedules' table for 'target_date'.
        """

        def serialize_schedule(schedule):
            """Convert schedule's time objects to string."""
            serialized = {}
            for day, times in schedule.items():
                start_time, end_time = times
                serialized[day] = (start_time.strftime("%H:%M"), end_time.strftime("%H:%M"))
            return serialized

        blocks_to_store = []
        for block in day_schedule.time_blocks:
            block_dict = {
                "id": block.id,
                "name": block.name,
                "schedule": serialize_schedule(block.schedule),  # Serialize the schedule
                "list_categories": block.list_categories,
                "task_tags": block.task_tags,
                "tasks": block.tasks_dict,  # or you might store the actual tasks
                "block_type": block.block_type,
                "color": list(block.color) if block.color else [47, 47, 47],
                "duration": block.duration
            }
            blocks_to_store.append(block_dict)

        with self.conn:
            self.conn.execute("""
                INSERT INTO schedules (schedule_date, time_blocks)
                VALUES (?, ?)
            """, (
                target_date.isoformat(),
                json.dumps(blocks_to_store)
            ))

    def _load_schedule_from_db(self, target_date):
        """
        Fetches the schedule for the given date from the database.
        Converts target_date to a date object if it's provided as a string.
        """
        if isinstance(target_date, str):
            try:
                target_date = datetime.fromisoformat(target_date).date()
            except ValueError:
                raise ValueError(f"Invalid date string format: {target_date}. Expected ISO 8601 format.")

        if not isinstance(target_date, date):
            raise TypeError(f"target_date must be a date or ISO-formatted string, got {type(target_date)}.")

        cursor = self.conn.execute("""
            SELECT * FROM schedules
            WHERE schedule_date = ?
        """, (target_date.isoformat(),))
        return cursor.fetchone()

    def _get_time_blocks_for_day(self, target_date: date):
        to_return = []
        target_day = target_date.strftime('%A').lower()

        for timeblock in self.time_blocks:
            if timeblock.schedule and target_day in timeblock.schedule:
                to_return.append(timeblock)

        return to_return

    def add_time_block(self, time_block):
        with self.conn:
            self.conn.execute("""
                INSERT INTO time_blocks (
                    name, start_time, end_time, schedule, 
                    list_categories, task_tags, tasks, block_type, color, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time_block.name,
                json.dumps(time_block.schedule),
                json.dumps(time_block.list_categories),
                json.dumps(time_block.task_tags),
                json.dumps(time_block.tasks_dict),
                time_block.block_type,
                json.dumps(time_block.color),
                time_block.duration
            ))

    def remove_time_block(self, time_block_id):
        with self.conn:
            self.conn.execute("DELETE FROM time_blocks WHERE id = ?", (time_block_id,))

    def update_time_block(self, time_block_id, updated_time_block):
        with self.conn:
            self.conn.execute("""
                UPDATE time_blocks
                SET 
                    schedule_id = ?,
                    name = ?,
                    start_time = ?,
                    end_time = ?,
                    schedule = ?,
                    list_categories = ?,
                    task_tags = ?,
                    tasks = ?,
                    block_type = ?,
                    color = ?,
                    duration = ?
                WHERE id = ?
            """, (
                updated_time_block.schedule_manager.id if updated_time_block.schedule_manager else None,
                updated_time_block.name,
                json.dumps(updated_time_block.schedule),
                json.dumps(updated_time_block.list_categories),
                json.dumps(updated_time_block.task_tags),
                json.dumps(updated_time_block.tasks_dict),
                updated_time_block.block_type,
                json.dumps(updated_time_block.color),
                updated_time_block.duration,
                time_block_id
            ))

    def load_time_blocks(self):
        self.time_blocks = []
        cursor = self.conn.execute("SELECT * FROM time_blocks")
        rows = cursor.fetchall()
        for row in rows:
            self.time_blocks.append(self._row_to_time_block(row))

    def get_time_block(self, time_block_id):
        cursor = self.conn.execute("SELECT * FROM time_blocks WHERE id = ?", (time_block_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_time_block(row)
        return None

    @staticmethod
    def _row_to_time_block(row):
        return TimeBlock(
            block_id=row["id"],
            name=row["name"],
            schedule=json.loads(row["schedule"]),
            list_categories=json.loads(row["list_categories"]),
            task_tags=json.loads(row["task_tags"]),
            tasks=json.loads(row["tasks"]),
            block_type=row["block_type"],
            color=tuple(json.loads(row["color"])),
            duration=row["duration"]
        )

    # ---------------------------
    # GLOBAL WEIGHT CALCULATIONS
    # ---------------------------

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

        workday_preference_weight = self.theta * (
            1 if datetime.now().strftime('%A') in task.preferred_work_days else 0
        )

        return (
                priority_weight + urgency_weight + flexibility_weight + added_time_weight +
                effort_weight + time_estimate_weight + time_logged_weight + workday_preference_weight
        )

    def update_task_global_weights(self):
        cursor = self.conn.execute("""
            SELECT * FROM tasks
            WHERE include_in_schedule = 1
              AND status != 'Completed'
        """)
        rows = cursor.fetchall()

        if not rows:
            return

        tasks = [Task(**dict(row)) for row in rows]

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
            self.conn.execute("UPDATE tasks SET global_weight = ? WHERE id = ?", (global_weight, task.id))

        self.conn.commit()

    def get_day_schedule(self, date):
        schedule = self.load_schedule(date)
        if schedule:
            return schedule
        else:
            return self.generate_schedule(date)


class DaySchedule:
    def __init__(self, date, time_blocks, task_manager_instance, schedule_settings):
        """
        :param date: A datetime.date object for which the schedule is generated
        :param time_blocks: A list of TimeBlock objects (user_defined + system_defined)
        :param task_manager_instance: The TaskManager used to fetch tasks from the DB
        :param schedule_settings: An instance of ScheduleSettings for configuring sleep, peak hours, etc.
        """
        self.date = date
        self.time_blocks = time_blocks
        self.task_manager_instance = task_manager_instance
        self.schedule_settings = schedule_settings
        self.time_blocks = self._generate_schedule()  # Build out final blocks (sleep + fill gaps)

    def _generate_schedule(self):
        """
        Inserts a 'sleep' block at the start of the day, plus system-defined blocks for gaps.
        Returns the final list of TimeBlock objects (both user_defined and system_defined).
        """
        day_start = datetime.combine(self.date, self.schedule_settings.day_start)
        sleep_duration = timedelta(hours=self.schedule_settings.ideal_sleep_duration)
        sleep_end = day_start + sleep_duration

        target_day_str = self.date.strftime('%A').lower()

        # Filter user-defined blocks that apply to this day
        user_blocks = [
            block for block in self.time_blocks
            if block.schedule and target_day_str in block.schedule and block.block_type == 'user_defined'
        ]
        user_blocks.sort(key=lambda b: b.schedule[target_day_str][0])  # Sort by start time in that day's schedule

        final_blocks = []
        current_time = day_start

        # (1) Sleep Block
        sleep_block = TimeBlock(
            block_id=None,
            name="Sleep",
            schedule={target_day_str: (day_start.time(), sleep_end.time())},
            block_type="unavailable",
            color=(173, 216, 230),
            duration=self.schedule_settings.ideal_sleep_duration
        )
        # Set start_time/end_time
        sleep_block.start_time = day_start.time()
        sleep_block.end_time = sleep_end.time()
        final_blocks.append(sleep_block)
        current_time = sleep_end

        # (2) Insert user-defined blocks, filling gaps with system-defined blocks
        for block in user_blocks:
            block_start_dt = datetime.combine(self.date, block.schedule[target_day_str][0])
            block_end_dt = datetime.combine(self.date, block.schedule[target_day_str][1])

            # If there's a gap before the user-defined block starts, create a system-defined block
            if current_time < block_start_dt:
                gap_duration = (block_start_dt - current_time).total_seconds() / 3600
                gap_block = TimeBlock(
                    block_id=None,
                    name="Unscheduled",
                    schedule={target_day_str: (current_time.time(), block_start_dt.time())},
                    block_type="system_defined",
                    color=(200, 200, 200),
                    duration=gap_duration
                )
                gap_block.start_time = current_time.time()
                gap_block.end_time = block_start_dt.time()
                final_blocks.append(gap_block)

            # Update the user-defined block with actual start/end times for this date
            block.start_time = block_start_dt.time()
            block.end_time = block_end_dt.time()
            final_blocks.append(block)

            current_time = block_end_dt

        # (3) If there's leftover time until day_end (24h from day_start), fill it with a system-defined block
        day_end = day_start + timedelta(hours=24)
        if current_time < day_end:
            leftover_duration = (day_end - current_time).total_seconds() / 3600
            gap_block = TimeBlock(
                block_id=None,
                name="Unscheduled",
                schedule={target_day_str: (current_time.time(), day_end.time())},
                block_type="system_defined",
                color=(200, 200, 200),
                duration=leftover_duration
            )
            gap_block.start_time = current_time.time()
            gap_block.end_time = day_end.time()
            final_blocks.append(gap_block)

        return final_blocks

    def assign_schedule_weights(self):
        """
        Populates all blocks with tasks that have not yet been scheduled
        (schedule_weight=0), making sure tasks fit in each block’s available time.
        """
        tasks_to_schedule = self._get_unscheduled_tasks()
        tasks_to_schedule = self._prioritize_tasks(tasks_to_schedule)

        for block in self.time_blocks:
            self._populate_or_reorder_block(block, tasks_to_schedule)

    def _get_unscheduled_tasks(self):
        """
        Fetches tasks that:
          - include_in_schedule = 1
          - status != 'Completed'
          - (schedule_weight is NULL or 0)
        """
        cursor = self.task_manager_instance.conn.execute("""
            SELECT * FROM tasks
            WHERE include_in_schedule = 1
              AND status != 'Completed'
              AND (schedule_weight IS NULL OR schedule_weight = 0)
        """)
        rows = cursor.fetchall()
        return [Task(**dict(row)) for row in rows]

    def _prioritize_tasks(self, tasks):
        """
        Sort tasks primarily by earliest due_date,
        then by descending global_weight.
        """

        def due_date_key(t):
            return t.due_datetime.timestamp() if t.due_datetime else float('inf')

        def global_weight_key(t):
            return -1 * (t.global_weight or 0)

        tasks.sort(key=lambda x: (due_date_key(x), global_weight_key(x)))
        return tasks

    def _populate_or_reorder_block(self, block, tasks_to_schedule):
        """
        Reorders tasks in a user-defined block by due_date/global_weight,
        then fills leftover time with tasks from tasks_to_schedule (peak vs off-peak).
        """
        # 1. For user_defined, reorder already-loaded tasks
        if block.block_type == "user_defined":
            block.tasks.sort(key=lambda t: (
                t.due_datetime.timestamp() if t.due_datetime else float('inf'),
                -1 * (t.global_weight or 0)
            ))

        # 2. Calculate leftover time
        already_assigned_time = sum((t.time_estimate or 0) for t in block.tasks)
        available_duration = block.duration - already_assigned_time
        if available_duration <= 0:
            return  # No space left in this block

        self._assign_tasks_to_block(block, tasks_to_schedule, available_duration)

    def _assign_tasks_to_block(self, block, tasks_list, available_duration):
        """
        Inserts tasks into the block, respecting peak/off-peak hours and time estimates.
        """
        # Check if block is fully in peak hours
        target_day_str = self.date.strftime('%A').lower()
        if block.schedule and target_day_str in block.schedule:
            start_dt, end_dt = block.schedule[target_day_str]
            is_peak = self._is_within_peak_hours(start_dt, end_dt)
        else:
            is_peak = False

        # Sort tasks differently if peak vs off-peak
        if is_peak:
            tasks_list.sort(key=lambda t: -1 * self._effort_map(t.effort_level))
        else:
            tasks_list.sort(key=lambda t: self._effort_map(t.effort_level))

        used_time = 0.0
        i = 0
        while i < len(tasks_list):
            task = tasks_list[i]
            task_duration = task.time_estimate or 0

            # If block is already 70% used and task not urgent, skip it for now
            usage_fraction = used_time / block.duration if block.duration else 1
            if usage_fraction > 0.7 and not self._is_urgent(task):
                i += 1
                continue

            if task_duration <= (available_duration - used_time):
                block.tasks.append(task)
                used_time += task_duration
                self._mark_task_as_scheduled(task)
                tasks_list.pop(i)
            else:
                i += 1

            if used_time >= available_duration:
                break

    def _is_within_peak_hours(self, start_time, end_time):
        """
        Returns True if [start_time, end_time] is within the configured peak hours.
        start_time/end_time are datetime.time objects.
        """
        peak_start, peak_end = self.schedule_settings.peak_productivity_hours
        return (start_time >= peak_start) and (end_time <= peak_end)

    def _is_urgent(self, task):
        """A simple example: tasks due within 2 days are urgent."""
        if not task.due_datetime:
            return False
        return (task.due_datetime - datetime.now()) <= timedelta(days=2)

    def _effort_map(self, level):
        """Map string effort levels to numeric values for sorting."""
        mapping = {"Easy": 1, "Medium": 2, "Hard": 3}
        return mapping.get(level, 2)

    def _mark_task_as_scheduled(self, task):
        """
        Updates a task as scheduled (schedule_weight=1.0, currently_in_schedule=1).
        """
        task.schedule_weight = 1.0
        task.currently_in_schedule = True
        self.task_manager_instance.conn.execute(
            "UPDATE tasks SET schedule_weight = ?, currently_in_schedule = 1 WHERE id = ?",
            (task.schedule_weight, task.id)
        )
        self.task_manager_instance.conn.commit()

    def get_time_blocks(self):
        """
        Returns the final list of TimeBlocks after assignment.
        """
        return self.time_blocks
