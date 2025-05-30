import sqlite3
import os
from datetime import datetime, timedelta, date
import re
import json
import uuid
from core.signals import global_signals
from core.utils import *


class TaskChunk:
    def __init__(
        self,
        id,
        task,
        chunk_type,
        unit,
        size=None,
        timeblock_ratings=None,
        timeblock=None,
        date=None,
        is_recurring=False,
        status=None,
    ):
        self.id = id
        self.task = task
        self.chunk_type = chunk_type  # "manual", "auto", "placed"
        self.size = size
        self.unit = unit
        self.timeblock_ratings = timeblock_ratings or []
        self.timeblock = timeblock
        self.date = date  # Date for recurring task
        self.is_recurring = is_recurring  # True if part of a recurring task
        self.status = status if status else self.update_status()
        self.flagged = False  # Initialize flagged attribute

    def update_status(self):
        if self.date and self.is_recurring:
            if (
                isinstance(self.date, (date, datetime))
                and self.date == datetime.today().date()
            ):
                return "active"
            elif (
                isinstance(self.date, (date, datetime))
                and self.date > datetime.today().date()
            ):
                return "locked"
        return "active"

    def mark_completed(self):
        self.status = "completed"

    def mark_flagged(self):
        self.status = "flagged"

    def mark_failed(self):
        self.status = "failed"

    def split(self, ratios):
        # Only for splitting auto chunks
        if self.chunk_type == "auto":
            total_ratio = sum(ratios)
            # Guard against division by zero if ratios is empty or sums to zero
            if total_ratio <= 0:
                return [self]  # Cannot split if total ratio is not positive

            if self.unit == "time":
                subchunks = [
                    TaskChunk(
                        # Generate new unique IDs for subchunks
                        str(uuid.uuid4()),
                        self.task,
                        self.chunk_type,
                        self.unit,
                        size=(self.size * r) / total_ratio,
                        timeblock_ratings=self.timeblock_ratings,  # Subchunks might need re-rating
                        timeblock=None,  # Subchunks are initially unassigned
                        date=self.date,
                        is_recurring=self.is_recurring,
                        status=self.status,
                    )
                    for r in ratios
                ]
                min_chunk = getattr(self.task, "min_chunk_size", 0.25)
                max_chunk = getattr(self.task, "max_chunk_size", self.size)
                for sc in subchunks:
                    if sc.size < min_chunk:
                        sc.size = min_chunk
                    elif sc.size > max_chunk:
                        sc.size = max_chunk
                total_adjusted = sum(sc.size for sc in subchunks)
                if total_adjusted > 0 and total_adjusted != self.size:
                    factor = self.size / total_adjusted
                    for sc in subchunks:
                        sc.size *= factor
                return subchunks
            elif self.unit == "count":
                subchunks = [
                    TaskChunk(
                        # Generate new unique IDs for subchunks
                        str(uuid.uuid4()),
                        self.task,
                        self.chunk_type,
                        self.unit,
                        size=(self.size * r) / total_ratio,
                        timeblock_ratings=self.timeblock_ratings,  # Subchunks might need re-rating
                        timeblock=None,  # Subchunks are initially unassigned
                        date=self.date,
                        is_recurring=self.is_recurring,
                        status=self.status,
                    )
                    for r in ratios
                ]
                min_chunk = getattr(self.task, "min_chunk_size", 1)
                max_chunk = getattr(self.task, "max_chunk_size", self.size)
                for sc in subchunks:
                    if sc.size < min_chunk:
                        sc.size = min_chunk
                    elif sc.size > max_chunk:
                        sc.size = max_chunk
                total_adjusted = sum(sc.size for sc in subchunks)
                if total_adjusted > 0 and total_adjusted != self.size:
                    factor = self.size / total_adjusted
                    for sc in subchunks:
                        sc.size *= factor
                return subchunks
        return [self]


class Task:
    default_progress_order = ["subtasks", "count", "time"]

    def __init__(self, **kwargs):

        required_attributes = ["name", "list_name"]
        for attr in required_attributes:
            if attr not in kwargs or kwargs[attr] is None:
                raise ValueError(
                    f"'{attr}' is a required attribute and cannot be None."
                )

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
                kwargs.get("start_date", None), ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]
            )
            self.due_datetime = self._parse_date(
                kwargs.get("due_datetime", None),
                ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"],
            )
            self.added_date_time = self._parse_date(
                kwargs.get("added_date_time", None),
                ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"],
            )
            self.last_completed_date = self._parse_date(
                kwargs.get("last_completed_date", None),
                ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"],
            )
        except ValueError as e:
            raise ValueError(
                f"Date parsing error for Task '{self.name}' (ID: {self.id}). Details: {str(e)}"
            )

        self.list_order = kwargs.get("list_order", 0)
        self.list_name = kwargs.get("list_name")

        self.recurring = kwargs.get("recurring", False)
        self.recur_every = kwargs.get(
            "recur_every", None
        )  # An int for recurrence every x days or a list of weekdays for recurrence.
        self.recurrences = kwargs.get("recurrences", 0)

        self.time_estimate = kwargs.get("time_estimate", 0.25)
        self.time_logged = kwargs.get("time_logged", 0.0)
        self.count_required = kwargs.get("count_required", 0)
        self.count_completed = kwargs.get("count_completed", 0)

        # example_chunk = {
        #     "id": str(uuid.uuid4()),  # Unique ID for the chunk
        #     "size": 1.5,  # Represents 1.5 hours or count units
        #     "type": "auto",  # "manual", "auto", or "placed"
        #     "unit": "time",  # "time" for duration-based tasks, "count" for count-based tasks
        #     "status": "active",  # "active", "locked", "completed", etc.
        #     "time_block": None,  # Assume this references a TimeBlock ID
        #     "date": "2025-02-12",  # The date on which this chunk is scheduled
        #     "is_recurring": False  # Whether this chunk is part of a recurring task
        # }

        self.chunks = kwargs.get("chunks", [])
        self.chunk_preference = kwargs.get("chunk_preference", None)  # "time", "count"
        self.min_chunk_size = kwargs.get("min_chunk_size", 0.0)
        self.max_chunk_size = kwargs.get("max_chunk_size", 0.0)

        self.subtasks = kwargs.get(
            "subtasks", []
        )  # [{"order": 1, "name": "test sub task", "completed": True}]
        self.dependencies = kwargs.get("dependencies", None)

        self.status = kwargs.get(
            "status", "Not Started"
        )  # ["Not Started", "In Progress", "Completed", "Failed", "On Hold"]
        self.flexibility = kwargs.get(
            "flexibility", "Flexible"
        )  # ["Strict", "Flexible", "Very Flexible]
        self.effort_level = kwargs.get(
            "effort_level", "Medium"
        )  # ["Low", "Medium", "High"]
        self.priority = kwargs.get("priority", 0)  # (0-10)
        self.previous_priority = kwargs.get("previous_priority", self.priority)
        self.preferred_work_days = kwargs.get(
            "preferred_work_days", []
        )  # ["Monday", "Wednesday", ...]
        self.time_of_day_preference = kwargs.get(
            "time_of_day_preference", []
        )  # ["Morning", "Afternoon", "Evening", "Night"]

        self.progress = self.calculate_progress()

        self.include_in_schedule = kwargs.get("include_in_schedule", False)

        self.global_weight = kwargs.get("global_weight", None)

    def add_chunk(
        self,
        size,
        chunk_type="manual",
        unit="time",
        time_block=None,
        date=None,
        is_recurring=False,
        status=None,
    ):
        """Adds a new chunk to the task's chunk list."""
        chunk = {
            "id": str(uuid.uuid4()),  # Generate a unique ID for the chunk
            "size": size,
            "type": chunk_type,  # "manual", "auto", "placed"
            "unit": unit,  # "time", "count"
            "status": status if status else ("locked" if is_recurring else "active"),
            "time_block": time_block,  # Stores the assigned time block (if placed)
            "date": date,  # Stores the assigned date (if placed)
            "is_recurring": is_recurring,
        }
        self.chunks.append(chunk)

    def update_chunk(self, updated_chunk_data: dict):
        """Updates a chunk in the task's chunk list using a dictionary."""
        chunk_id = updated_chunk_data.get("id")
        if not chunk_id:
            return False  # No ID provided, can't update

        for chunk in self.chunks:
            if chunk["id"] == chunk_id:
                for key, value in updated_chunk_data.items():
                    if key in chunk:  # Only update existing keys
                        chunk[key] = value
                return True  # Update successful

        return False  # Chunk not found

    def remove_chunk(self, chunk_id):
        """Removes a chunk from the task's chunk list based on chunk ID."""
        self.chunks = [chunk for chunk in self.chunks if chunk["id"] != chunk_id]

    def update_chunk_obj(self, task_chunk: TaskChunk) -> bool:
        """
        Update a chunk in the task's chunk list using a TaskChunk object.
        If the chunk's status changes to 'completed', update time_logged or count_completed.
        """
        for chunk in self.chunks:
            if chunk["id"] == task_chunk.id:
                previous_status = chunk.get("status", "active")
                # Update chunk details from the TaskChunk object.
                chunk["size"] = task_chunk.size
                chunk["type"] = task_chunk.chunk_type
                chunk["unit"] = task_chunk.unit
                chunk["status"] = task_chunk.status
                chunk["time_block"] = task_chunk.timeblock
                chunk["date"] = task_chunk.date
                chunk["is_recurring"] = task_chunk.is_recurring
                # If the chunk has just been marked as complete, update totals.
                if task_chunk.status == "completed" and previous_status != "completed":
                    if task_chunk.unit == "time":
                        self.time_logged += task_chunk.size
                    elif task_chunk.unit == "count":
                        self.count_completed += task_chunk.size
                return True
        return False

    def delete_chunk(self, task_chunk: TaskChunk) -> bool:
        """
        Delete a chunk from the task's chunk list using a TaskChunk object.
        If the chunk is marked as complete, subtract its size from time_logged or count_completed.
        """
        for i, chunk in enumerate(self.chunks):
            if chunk["id"] == task_chunk.id:
                # If the chunk is complete, adjust totals.
                if chunk.get("status") == "completed":
                    if chunk.get("unit") == "time":
                        self.time_logged -= chunk["size"]
                    elif chunk.get("unit") == "count":
                        self.count_completed -= chunk["size"]
                del self.chunks[i]
                return True
        return False

    def get_chunks(self):
        return self.chunks

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

        # Create a copy to avoid mutating the original list
        fmts = list(formats)
        # Add format with fractional seconds
        fmts.append("%Y-%m-%dT%H:%M:%S.%f")

        # Otherwise parse the string
        for fmt in fmts:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # If parsing fails with all formats, try ISO format as a last resort
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass  # Ignore ISO format parse error if it fails

        raise ValueError(
            f"Date '{date_str}' does not match any of the provided formats: {fmts} or ISO format"
        )

    def _progress_by_subtasks(self):
        """Calculate progress based on completed subtasks. Returns 0-100 float or None."""
        if self.subtasks:
            completed_subtasks = sum(
                1 for subtask in self.subtasks if subtask.get("completed", False)
            )
            total_subtasks = len(self.subtasks)
            if total_subtasks > 0:
                return (completed_subtasks / total_subtasks) * 100
            else:
                return 0.0  # Treat as 0% if list exists but is empty
        return None  # No subtasks defined

    def _progress_by_count(self):
        """Calculate progress based on item count. Returns 0-100 float or None."""
        if self.count_required > 0:
            return (self.count_completed / self.count_required) * 100
        # If count_required is 0 or not set, this method isn't applicable
        return None

    def _progress_by_time(self):
        """Calculate progress based on time logged vs estimate. Returns 0-100 float or None."""
        if self.time_estimate > 0:
            # Clamp progress at 100% even if time_logged exceeds estimate
            progress = (self.time_logged / self.time_estimate) * 100
            return min(progress, 100.0)
        # If time_estimate is 0 or not set, this method isn't applicable
        return None

    def calculate_progress(self, order=None):
        """Calculates task progress based on a configurable order of strategies."""
        order = order or self.default_progress_order
        strategy_map = {
            "subtasks": self._progress_by_subtasks,
            "count": self._progress_by_count,
            "time": self._progress_by_time,
        }

        for strategy_name in order:
            if strategy_name in strategy_map:
                progress_func = strategy_map[strategy_name]
                percentage = progress_func()
                if percentage is not None:
                    # First applicable strategy found, return its value
                    return percentage

        # If no strategy yielded a valid percentage, return 0.0
        return 0.0

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
            self.last_completed_date = (
                self._parse_date(completion_date, "%Y-%m-%d %H:%M")
                if completion_date
                else datetime.now()
            )
            self.progress = 100
            print(
                f"Task '{self.name}' (ID: {self.id}) marked as completed on {self.last_completed_date}."
            )

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
            self.subtasks = [
                subtask for subtask in self.subtasks if subtask["name"] != name
            ]

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

    def __repr__(self):
        # Provides a developer-friendly representation
        return f"<Task(id={self.id}, name='{self.name}', list='{self.list_name}')>"

    def __str__(self):
        # Provides a user-friendly string representation
        return f"Task: {self.name} (List: {self.list_name})"


class TaskList:
    def __init__(self, **kwargs):

        required_attributes = ["category", "name"]
        for attr in required_attributes:
            if attr not in kwargs or kwargs[attr] is None:
                raise ValueError(
                    f"'{attr}' is a required attribute and cannot be None."
                )

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
        self.default_start_date = self._parse_date(
            kwargs.get("default_start_date"), "%Y-%m-%d"
        )
        self.default_due_datetime = self._parse_date(
            kwargs.get("default_due_datetime"), "%Y-%m-%d %H:%M"
        )
        self.default_time_of_day_preference = kwargs.get(
            "default_time_of_day_preference", None
        )
        self.default_flexibility = kwargs.get("default_flexibility", None)
        self.default_effort_level = kwargs.get("default_effort_level", None)
        self.default_priority = kwargs.get("default_priority", None)
        self.default_preferred_work_days = kwargs.get(
            "default_preferred_work_days", None
        )

        self.consider_in_schedule = kwargs.get("consider_in_schedule", True)

        self.sort_by_queue = kwargs.get("sort_by_queue", False)
        self.sort_by_stack = kwargs.get("sort_by_stack", False)
        self.sort_by_priority = kwargs.get("sort_by_priority", False)
        self.sort_by_due_datetime = kwargs.get("sort_by_due_datetime", False)
        self.sort_by_tags = kwargs.get("sort_by_tags", False)
        self.sort_by_time_estimate = kwargs.get("sort_by_time_estimate", False)

        self.tasks = kwargs.get("tasks", [])
        self.progress = self.calculate_progress()

    @staticmethod
    def _parse_date(date_str, fmt):
        if date_str is None:
            return None

        # If already a datetime or date object, return it directly
        if isinstance(date_str, (datetime, date)):
            return date_str

        # Otherwise, attempt to parse as a string
        if isinstance(date_str, str):
            try:
                return (
                    datetime.strptime(date_str, fmt).date()
                    if "H" not in fmt
                    else datetime.strptime(date_str, fmt)
                )
            except ValueError:
                # If the primary format fails, try ISO format as a fallback for datetime
                if "H" in fmt:
                    try:
                        return datetime.fromisoformat(date_str)
                    except ValueError:
                        pass
                # If date format fails, try ISO date format
                else:
                    try:
                        return date.fromisoformat(date_str)
                    except ValueError:
                        pass
                # If all parsing fails, raise an error or return None
                raise ValueError(
                    f"Date string '{date_str}' does not match format '{fmt}' or ISO standard"
                )

        # Handle unexpected types
        raise TypeError(f"Unexpected type for date parsing: {type(date_str)}")

    def calculate_progress(self):
        if not self.tasks:
            return 0.0  # No tasks, 0% progress

        total_progress = 0
        tasks_with_progress = 0
        for task in self.tasks:
            # Assuming task.progress is already calculated (0-100)
            # We only average tasks that meaningfully contribute (e.g., have subtasks/count/time)
            # A task returning 0 progress from calculate_progress might be counted or ignored based on definition.
            # Let's assume task.progress accurately reflects its state.
            total_progress += task.progress
            tasks_with_progress += 1  # Count every task for the average

        if tasks_with_progress == 0:
            return 0.0  # Avoid division by zero if no tasks were counted

        return total_progress / tasks_with_progress

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
        print(f"DEBUG TaskList.get_tasks: name={self.name} due={self.sort_by_due_datetime} estimate={self.sort_by_time_estimate} queue={self.sort_by_queue} stack={self.sort_by_stack} priority={self.sort_by_priority}")
        # Sort by due date if toggled
        if self.sort_by_due_datetime:
            tasks_sorted = [t for t in self.tasks if t.status not in ["Completed","Failed"]]
            tasks_sorted.sort(key=lambda t: t.due_datetime or datetime.max)
            return tasks_sorted
        # Sort by time estimate if toggled
        if self.sort_by_time_estimate:
            tasks_sorted = [t for t in self.tasks if t.status not in ["Completed","Failed"]]
            tasks_sorted.sort(key=lambda t: t.time_estimate or 0)
            return tasks_sorted
        important_tasks = [
            task
            for task in self.tasks
            if task.priority == 10 and task.status not in ["Completed", "Failed"]
        ]
        other_tasks = [
            task
            for task in self.tasks
            if task.priority < 10 and task.status not in ["Completed", "Failed"]
        ]

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
        important_tasks = [
            task for task in self.tasks if task.priority == 10 and task.has_tag(tag)
        ]
        other_tasks = [
            task for task in self.tasks if not task.priority == 10 and task.has_tag(tag)
        ]

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
        filtered_tasks = [
            task for task in self.tasks if task.status not in ["Completed", "Failed"]
        ]

        def safe_priority_key(task):
            return task.priority if task.priority is not None else float("inf")

        return sorted(filtered_tasks, key=safe_priority_key)

    def disable_all_filters(self):
        self.sort_by_queue = False
        self.sort_by_stack = False
        self.sort_by_priority = False
        self.sort_by_due_datetime = False
        self.sort_by_tags = False
        self.sort_by_time_estimate = False

    def __str__(self):
        return "\n".join(
            str(task) for task in self.tasks if not task.status == "Completed"
        )


class TaskManager:
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_file = os.path.join(self.data_dir, "adm.db")
        # Connect with type detection enabled
        self.conn = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.initialize_system_category()
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
            creation_date TIMESTAMP,
            default_start_date DATE,
            default_due_datetime TIMESTAMP,
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
            sort_by_tags BOOLEAN NOT NULL DEFAULT 0,
            sort_by_time_estimate BOOLEAN NOT NULL DEFAULT 0
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
                start_date DATE,
                due_datetime TIMESTAMP,
                added_date_time TIMESTAMP,
                last_completed_date DATE,
                list_order INTEGER DEFAULT 0,
                list_name TEXT NOT NULL,

                recurring BOOLEAN NOT NULL DEFAULT 0,
                recur_every TEXT,
                recurrences INTEGER DEFAULT 0,

                time_estimate REAL DEFAULT 0.25,
                time_logged REAL DEFAULT 0.0,
                count_required INTEGER DEFAULT 0,
                count_completed INTEGER DEFAULT 0,

                chunks TEXT DEFAULT '[]',
                chunk_preference TEXT,
                min_chunk_size REAL DEFAULT 0.0,
                max_chunk_size REAL DEFAULT 0.0,

                subtasks TEXT DEFAULT '[]',
                dependencies TEXT,

                status TEXT DEFAULT 'Not Started',
                flexibility TEXT DEFAULT 'Flexible',
                effort_level TEXT DEFAULT 'Medium',
                priority INTEGER DEFAULT 0,
                previous_priority INTEGER DEFAULT 0,
                preferred_work_days TEXT DEFAULT '[]',
                time_of_day_preference TEXT DEFAULT '[]',

                include_in_schedule BOOLEAN NOT NULL DEFAULT 0,

                global_weight REAL,

                FOREIGN KEY(list_name) REFERENCES task_lists(name) ON DELETE CASCADE
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
            # Use the new conversion utilities
            task_list_data["notifications_enabled"] = from_bool_int(
                task_list_data["notifications_enabled"]
            )
            task_list_data["archived"] = from_bool_int(task_list_data["archived"])
            task_list_data["in_trash"] = from_bool_int(task_list_data["in_trash"])
            task_list_data["consider_in_schedule"] = from_bool_int(
                task_list_data["consider_in_schedule"]
            )
            task_list_data["sort_by_queue"] = from_bool_int(
                task_list_data["sort_by_queue"]
            )
            task_list_data["sort_by_stack"] = from_bool_int(
                task_list_data["sort_by_stack"]
            )
            task_list_data["sort_by_priority"] = from_bool_int(
                task_list_data["sort_by_priority"]
            )
            task_list_data["sort_by_due_datetime"] = from_bool_int(
                task_list_data["sort_by_due_datetime"]
            )
            task_list_data["sort_by_tags"] = from_bool_int(
                task_list_data["sort_by_tags"]
            )
            task_list_data["sort_by_time_estimate"] = from_bool_int(
                task_list_data["sort_by_time_estimate"]
            )
            print(f"DEBUG load_task_lists: list={task_list_data.get('name')} due={task_list_data.get('sort_by_due_datetime')} estimate={task_list_data.get('sort_by_time_estimate')}")
            # Create the TaskList object first
            task_list = TaskList(**task_list_data)
            # Now load its tasks from the DB and assign them
            task_list.tasks = self.get_tasks_by_list_name(task_list.name)
            task_lists.append(task_list)
        return task_lists

    def initialize_system_category(self):
        """
        Create a protected category 'system' and within it a default task list called 'quick tasks'.
        These cannot be deleted or edited.
        """
        cursor = self.conn.cursor()
        # Check if the system category exists; use "System" for comparison.
        cursor.execute("SELECT * FROM categories WHERE name=?", ("System",))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO categories (`order`, name) VALUES (?, ?)",
                (10000, "System"),
            )
            self.conn.commit()
            print("Protected system category created.")

        # Check if the system task list "quick tasks" exists.
        cursor.execute(
            "SELECT * FROM task_lists WHERE name=? AND category=?",
            ("quick tasks", "System"),
        )
        if not cursor.fetchone():
            # Create a TaskList instance for quick tasks.
            quick_tasks = TaskList(
                id=6363,
                order=1000000000,
                name="quick tasks",
                description="Default system quick tasks",
                category="System",
                notifications_enabled=True,
                archived=False,
                in_trash=False,
                creation_date=datetime.now().strftime("%Y-%m-%d"),  # Fix here
                default_start_date=datetime.now().strftime("%Y-%m-%d"),  # Fix here
                default_due_datetime=datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),  # Fix here
                default_time_of_day_preference=None,
                default_flexibility=None,
                default_effort_level=None,
                default_priority=0,
                default_preferred_work_days=[],
                consider_in_schedule=True,
                sort_by_queue=False,
                sort_by_stack=False,
                sort_by_priority=False,
                sort_by_due_datetime=False,
                sort_by_tags=False,
                sort_by_time_estimate=False,
                tasks=[],
            )
            self.add_task_list(quick_tasks)
            print("Protected 'quick tasks' task list created in system category.")

    def get_tasks_by_list_name(self, list_name):
        tasks = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE list_name=?", (list_name,))
        rows = cursor.fetchall()
        for row in rows:
            task_data = dict(row)
            task_data["tags"] = (
                safe_json_loads(
                    task_data["tags"], [], "tags", f"for task in list '{list_name}'"
                )
                if task_data.get("tags")
                else []
            )
            task_data["resources"] = (
                safe_json_loads(
                    task_data["resources"],
                    [],
                    "resources",
                    f"for task in list '{list_name}'",
                )
                if task_data.get("resources")
                else []
            )
            task_data["recur_every"] = (
                safe_json_loads(
                    task_data["recur_every"],
                    None,
                    "recur_every",
                    f"for task in list '{list_name}'",
                )
                if task_data.get("recur_every")
                else None
            )
            task_data["subtasks"] = (
                safe_json_loads(
                    task_data["subtasks"],
                    [],
                    "subtasks",
                    f"for task in list '{list_name}'",
                )
                if task_data.get("subtasks")
                else []
            )
            task_data["dependencies"] = (
                safe_json_loads(
                    task_data["dependencies"],
                    [],
                    "dependencies",
                    f"for task in list '{list_name}'",
                )
                if task_data.get("dependencies")
                else []
            )
            task_data["chunks"] = (
                safe_json_loads(
                    task_data["chunks"], [], "chunks", f"for task in list '{list_name}'"
                )
                if task_data.get("chunks")
                else []
            )
            task_data["preferred_work_days"] = (
                safe_json_loads(
                    task_data["preferred_work_days"],
                    [],
                    "preferred_work_days",
                    f"for task in list '{list_name}'",
                )
                if task_data.get("preferred_work_days")
                else []
            )
            task_data["time_of_day_preference"] = (
                safe_json_loads(
                    task_data["time_of_day_preference"],
                    [],
                    "time_of_day_preference",
                    f"for task in list '{list_name}'",
                )
                if task_data.get("time_of_day_preference")
                else []
            )

            task_data["recurring"] = bool(task_data["recurring"])
            task_data["include_in_schedule"] = bool(task_data["include_in_schedule"])

            task = Task(**task_data)
            tasks.append(task)
        return tasks

    def load_categories(self):
        categories = {
            "Uncategorized": {"order": 0, "task_lists": []},
            "System": {"order": 0, "task_lists": []},
        }

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY `order`")
        category_rows = cursor.fetchall()

        for row in category_rows:
            order_val = row["order"]
            name_val = row["name"]
            if name_val not in ("Uncategorized", "System"):
                categories[name_val] = {"order": order_val, "task_lists": []}

        for tl in self.task_lists:
            cat = tl.category or "Uncategorized"
            if cat not in categories:
                cat = "Uncategorized"
            categories[cat]["task_lists"].append(tl)

        for cat_name, cat_data in categories.items():
            cat_data["task_lists"].sort(key=lambda t: getattr(t, "order", float("inf")))

        return dict(
            sorted(
                categories.items(),
                key=lambda item: (
                    (float("inf"), 0)
                    if item[0] == "Uncategorized"
                    else (
                        (float("inf"), 1)
                        if item[0] == "System"
                        else (item[1]["order"], -1)
                    )
                ),
            )
        )

    def get_category_tasklist_names(self):
        try:
            cursor = self.conn.cursor()

            # Fetch categories
            cursor.execute("SELECT id, name FROM categories ORDER BY `order`")
            categories = cursor.fetchall()

            # Initialize dictionary
            category_tasklists = {
                category[1]: [] for category in categories
            }  # category[1] is 'name'
            category_tasklists["Uncategorized"] = (
                []
            )  # Ensure "Uncategorized" always exists

            # Fetch task lists and their associated categories
            cursor.execute(
                """
                SELECT task_lists.name AS task_list_name, categories.name AS category_name
                FROM task_lists
                LEFT JOIN categories ON task_lists.category = categories.name
                ORDER BY task_lists.`order`
            """
            )
            task_lists = cursor.fetchall()

            # Populate category_tasklists
            for task_list_name, category_name in task_lists:
                category_name = (
                    category_name or "Uncategorized"
                )  # Handle uncategorized task lists
                category_tasklists.setdefault(category_name, []).append(task_list_name)

            return category_tasklists
        except sqlite3.Error as e:
            print(f"Database error while fetching categories and task lists: {e}")
            return {}

    def add_category(self, category_name):
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT MAX(`order`) FROM categories")
            max_order = cursor.fetchone()[0]
            new_order = max_order + 1 if max_order is not None else 1
            cursor.execute(
                "INSERT INTO categories (name, `order`) VALUES (?, ?)",
                (category_name, new_order),
            )
            self.conn.commit()
            # Update in-memory structure
            self.categories[category_name] = {"order": new_order, "task_lists": []}
        except sqlite3.IntegrityError as e:
            print(
                f"Error adding category '{category_name}': {e}"
            )  # Likely duplicate name
            if self.conn:
                self.conn.rollback()
        except Exception as e:
            print(f"Unexpected error while adding category '{category_name}': {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def remove_category(self, category_name):
        if category_name.lower() == "system":
            print("Error: The system category cannot be removed.")
            return
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM categories WHERE name=?", (category_name,))
            self.conn.commit()
            # Reload categories from DB to reflect change
            self.categories = self.load_categories()
        except sqlite3.Error as e:  # Changed from IntegrityError to general Error
            print(f"Error removing category '{category_name}': {e}")
            if self.conn:
                self.conn.rollback()
        except Exception as e:
            print(f"Unexpected error while removing category '{category_name}': {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def rename_category(self, old_name, new_name):
        if old_name.lower() == "system":
            print("Error: The system category cannot be renamed.")
            return
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE categories SET name=? WHERE name=?", (new_name, old_name)
            )
            # Check if the row was actually updated
            if cursor.rowcount == 0:
                print(f"Warning: Category '{old_name}' not found for renaming.")
            else:
                self.conn.commit()
            # Reload categories to reflect changes
            self.categories = self.load_categories()
        except sqlite3.IntegrityError as e:  # Could be duplicate new_name
            print(f"Error renaming category from '{old_name}' to '{new_name}': {e}")
            if self.conn:
                self.conn.rollback()
        except Exception as e:
            print(
                f"Unexpected error while renaming category from '{old_name}' to '{new_name}': {e}"
            )
            if self.conn:
                self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def update_category_order(self, category_name, new_order):
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE categories SET `order` = ? WHERE name = ?",
                (new_order, category_name),
            )
            if cursor.rowcount == 0:
                print(
                    f"Warning: Category '{category_name}' not found for order update."
                )
            else:
                self.conn.commit()
                # Update in-memory order
                if category_name in self.categories:
                    self.categories[category_name]["order"] = new_order
                else:  # Might need reload if category wasn't loaded correctly initially
                    print(
                        f"Warning: Category '{category_name}' updated in DB but not found in memory cache."
                    )
        except sqlite3.Error as e:
            print(f"Failed to update order for category '{category_name}': {e}")
            if self.conn:
                self.conn.rollback()
        except Exception as e:
            print(
                f"Unexpected error while updating category order for '{category_name}': {e}"
            )
            if self.conn:
                self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def add_task_list(self, task_list: TaskList):
        cursor = None
        try:
            cursor = self.conn.cursor()
            # Determine order if not set
            if task_list.order is None:
                cursor.execute("SELECT MAX(`order`) FROM task_lists")
                max_order = cursor.fetchone()[0]
                task_list.order = max_order + 1 if max_order is not None else 1

            cursor.execute(
                """
                INSERT INTO task_lists (
                    `order`, name, description, category, notifications_enabled,
                    archived, in_trash, creation_date, default_start_date,
                    default_due_datetime, default_time_of_day_preference,
                    default_flexibility, default_effort_level, default_priority,
                    default_preferred_work_days, consider_in_schedule,
                    sort_by_queue, sort_by_stack, sort_by_priority,
                    sort_by_due_datetime, sort_by_tags, sort_by_time_estimate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_list.order,
                    task_list.name,
                    task_list.description,
                    task_list.category,
                    to_bool_int(task_list.notifications_enabled),
                    to_bool_int(task_list.archived),
                    to_bool_int(task_list.in_trash),
                    task_list.creation_date.strftime("%Y-%m-%d") if task_list.creation_date else None,
                    task_list.default_start_date.strftime("%Y-%m-%d") if task_list.default_start_date else None,
                    task_list.default_due_datetime.strftime("%Y-%m-%d %H:%M") if task_list.default_due_datetime else None,
                    task_list.default_time_of_day_preference,
                    task_list.default_flexibility,
                    task_list.default_effort_level,
                    task_list.default_priority,
                    safe_json_dumps(task_list.default_preferred_work_days, "[]", "default_preferred_work_days"),
                    to_bool_int(task_list.consider_in_schedule),
                    to_bool_int(task_list.sort_by_queue),
                    to_bool_int(task_list.sort_by_stack),
                    to_bool_int(task_list.sort_by_priority),
                    to_bool_int(task_list.sort_by_due_datetime),
                    to_bool_int(task_list.sort_by_tags),
                    to_bool_int(task_list.sort_by_time_estimate)
                )
            )
            self.conn.commit()
            # Get the newly assigned ID if it's autoincrement (assuming it is)
            task_list.id = cursor.lastrowid

            # Add to in-memory lists
            if not hasattr(self, "task_lists"):
                self.task_lists = []
            self.task_lists.append(task_list)
            if task_list.category not in self.categories:
                # Handle case where category might not exist in memory yet
                # Option 1: Add it dynamically (might mess up order)
                # self.categories[task_list.category] = {'order': some_default_order, 'task_lists': [task_list]}
                # Option 2: Reload categories (safer but potentially slower)
                self.categories = self.load_categories()
                # Option 3: Log warning and proceed
                # print(f"Warning: Category '{task_list.category}' not found in memory cache when adding task list '{task_list.name}'")
            else:
                self.categories[task_list.category]["task_lists"].append(task_list)

        except sqlite3.Error as e:
            print(f"Database error while adding task_list '{task_list.name}': {e}")
            if self.conn:
                self.conn.rollback()
        except Exception as e:
            print(f"Unexpected error while adding task list '{task_list.name}': {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def remove_task_list(self, name):
        cursor = None
        try:
            cursor = self.conn.cursor()
            # Check if protected system task list first
            cursor.execute("SELECT category FROM task_lists WHERE name=?", (name,))
            row = cursor.fetchone()
            if row and row["category"] == "System" and name == "quick tasks":
                print(
                    "Error: The 'quick tasks' list in the system category cannot be removed."
                )
                return

            # Proceed with deletion
            cursor.execute("DELETE FROM task_lists WHERE name = ?", (name,))
            if cursor.rowcount == 0:
                print(f"Warning: Task list '{name}' not found in database for removal.")
            else:
                self.conn.commit()
                # Remove from in-memory lists AFTER successful commit
                self.task_lists[:] = [tl for tl in self.task_lists if tl.name != name]
                for category in self.categories.values():
                    category["task_lists"][:] = [
                        tl for tl in category["task_lists"] if tl.name != name
                    ]

        except sqlite3.Error as e:
            print(f"Database error while removing task list '{name}': {e}")
            if self.conn:
                self.conn.rollback()
        except Exception as e:
            print(f"Unexpected error while removing task list '{name}': {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def update_task_list(self, task_list: TaskList):
        # Check protected status first
        if task_list.category == "System" and task_list.name == "quick tasks":
            print(
                "Error: The 'quick tasks' list in the system category cannot be edited."
            )
            return

        cursor = None
        try:
            cursor = self.conn.cursor()
            print(f"DEBUG update_task_list: saving list={task_list.name} due={task_list.sort_by_due_datetime} estimate={task_list.sort_by_time_estimate}")
            cursor.execute(
                "UPDATE task_lists SET `order` = ?, name = ?, description = ?, category = ?, notifications_enabled = ?, archived = ?, in_trash = ?, creation_date = ?, default_start_date = ?, default_due_datetime = ?, default_time_of_day_preference = ?, default_flexibility = ?, default_effort_level = ?, default_priority = ?, default_preferred_work_days = ?, consider_in_schedule = ?, sort_by_queue = ?, sort_by_stack = ?, sort_by_priority = ?, sort_by_due_datetime = ?, sort_by_tags = ?, sort_by_time_estimate = ? WHERE id = ?",
                (
                    task_list.order,
                    task_list.name,
                    task_list.description,
                    task_list.category,
                    to_bool_int(task_list.notifications_enabled),
                    to_bool_int(task_list.archived),
                    to_bool_int(task_list.in_trash),
                    task_list.creation_date.strftime("%Y-%m-%d") if task_list.creation_date else None,
                    task_list.default_start_date.strftime("%Y-%m-%d") if task_list.default_start_date else None,
                    task_list.default_due_datetime.strftime("%Y-%m-%d %H:%M") if task_list.default_due_datetime else None,
                    task_list.default_time_of_day_preference,
                    task_list.default_flexibility,
                    task_list.default_effort_level,
                    task_list.default_priority,
                    safe_json_dumps(task_list.default_preferred_work_days, "[]", "default_preferred_work_days"),
                    to_bool_int(task_list.consider_in_schedule),
                    to_bool_int(task_list.sort_by_queue),
                    to_bool_int(task_list.sort_by_stack),
                    to_bool_int(task_list.sort_by_priority),
                    to_bool_int(task_list.sort_by_due_datetime),
                    to_bool_int(task_list.sort_by_tags),
                    to_bool_int(task_list.sort_by_time_estimate),
                    task_list.id
                )
            )
            print(f"DEBUG update_task_list: executed update, rowcount={cursor.rowcount}")
            if cursor.rowcount == 0:
                print(
                    f"Warning: Task list '{task_list.name}' not found in database for update."
                )
            else:
                self.conn.commit()
                # Update in-memory representation (find and update/replace)
                found_in_memory = False
                for i, tl in enumerate(self.task_lists):
                    if tl.id == task_list.id:  # Assuming ID is reliable
                        # Replace the old object with the updated one
                        self.task_lists[i] = task_list
                        found_in_memory = True
                        break
                if found_in_memory:
                    # Also update within categories dictionary
                    self.categories = (
                        self.load_categories()
                    )  # Reload to ensure consistency
                else:
                    print(
                        f"Warning: Updated task list '{task_list.name}' in DB but not found/updated in memory cache."
                    )

        except sqlite3.Error as e:
            print(f"Database error while updating task list '{task_list.name}': {e}")
            if self.conn:
                self.conn.rollback()
        except Exception as e:
            print(f"Unexpected error while updating task list '{task_list.name}': {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def update_task_list_order(self, task_list_name, new_order):
        try:
            cursor = self.conn.cursor()

            # Update the order in the database
            cursor.execute(
                "UPDATE task_lists SET `order` = ? WHERE name = ?",
                (new_order, task_list_name),
            )
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
                raise ValueError(
                    f"Task list '{task_list_name}' not found in loaded categories."
                )

        except sqlite3.Error as e:
            print(f"Database error while updating task list order: {e}")
        except Exception as e:
            print(f"Unexpected error while updating task list order: {e}")

    def add_task(self, task: Task):
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
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

                    chunks,
                    chunk_preference,
                    min_chunk_size,
                    max_chunk_size,

                    subtasks,
                    dependencies,

                    status,
                    flexibility,
                    effort_level,
                    priority,
                    previous_priority,
                    preferred_work_days,
                    time_of_day_preference,

                    include_in_schedule,
                    global_weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task.name,
                    task.description,
                    task.notes,
                    safe_json_dumps(task.tags, "[]", "tags") if task.tags else None,
                    (
                        safe_json_dumps(task.resources, "[]", "resources")
                        if task.resources
                        else None
                    ),
                    task.start_date.strftime("%Y-%m-%d") if task.start_date else None,
                    (
                        task.due_datetime.strftime("%Y-%m-%d %H:%M")
                        if task.due_datetime
                        else None
                    ),
                    (
                        task.added_date_time.strftime("%Y-%m-%d %H:%M")
                        if task.added_date_time
                        else None
                    ),
                    (
                        task.last_completed_date.strftime("%Y-%m-%d %H:%M")
                        if task.last_completed_date
                        else None
                    ),
                    task.list_order,
                    task.list_name,
                    int(task.recurring),
                    (
                        safe_json_dumps(task.recur_every, "null", "recur_every")
                        if task.recur_every
                        else None
                    ),
                    task.recurrences,
                    task.time_estimate,
                    task.time_logged,
                    task.count_required,
                    task.count_completed,
                    (
                        safe_json_dumps(task.chunks, "[]", "chunks")
                        if task.chunks
                        else "[]"
                    ),
                    task.chunk_preference,
                    task.min_chunk_size,
                    task.max_chunk_size,
                    (
                        safe_json_dumps(task.subtasks, "[]", "subtasks")
                        if task.subtasks
                        else "[]"
                    ),
                    (
                        safe_json_dumps(task.dependencies, "[]", "dependencies")
                        if task.dependencies
                        else None
                    ),
                    task.status,
                    task.flexibility,
                    task.effort_level,
                    task.priority,
                    task.previous_priority,
                    safe_json_dumps(
                        task.preferred_work_days, "[]", "preferred_work_days"
                    ),
                    safe_json_dumps(
                        task.time_of_day_preference, "[]", "time_of_day_preference"
                    ),
                    int(task.include_in_schedule),
                    task.global_weight,
                ),
            )
            self.conn.commit()
            task.id = cursor.lastrowid

            # Add to the in-memory model
            for task_list in self.task_lists:
                if task_list.name == task.list_name:
                    task_list.add_task_to_model_list(task)
                    break

            print(f"Task '{task.name}' successfully added with ID: {task.id}")
        except sqlite3.Error as e:
            print(f"Database error while adding task '{task.name}': {e}")
            if self.conn:
                self.conn.rollback()  # Rollback on error
            # Optionally re-raise or handle
        except Exception as e:
            print(f"Unexpected error while adding task '{task.name}': {e}")
            if self.conn:
                self.conn.rollback()  # Rollback on error
            # Optionally re-raise or handle
        finally:
            if cursor:
                cursor.close()

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
            list_name = task.list_name
            for task_list in self.task_lists:
                if task_list.name == list_name:
                    task_list.tasks[:] = [t for t in task_list.tasks if t.id != task_id]
                    break
            print(
                f"Task '{task.name if isinstance(task, Task) else task_id}' successfully removed."
            )

        except sqlite3.Error as e:
            print(f"Database error while removing task: {e}")
        except Exception as e:
            print(f"Unexpected error while removing task: {e}")

    def update_task(self, task: Task):
        cursor = None
        try:
            # Find old list name *before* starting transaction potentially
            old_task = self.get_task(task.id)
            old_list_name = old_task.list_name if old_task else None

            cursor = self.conn.cursor()
            cursor.execute(
                """
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

                    chunks = ?,
                    chunk_preference = ?,
                    min_chunk_size = ?,
                    max_chunk_size = ?,

                    subtasks = ?,
                    dependencies = ?,

                    status = ?,
                    flexibility = ?,
                    effort_level = ?,
                    priority = ?,
                    previous_priority = ?,
                    preferred_work_days = ?,
                    time_of_day_preference = ?,

                    include_in_schedule = ?,
                    global_weight = ?

                WHERE id = ?
            """,
                (
                    task.name,
                    task.description,
                    task.notes,
                    safe_json_dumps(task.tags, "[]", "tags") if task.tags else None,
                    (
                        safe_json_dumps(task.resources, "[]", "resources")
                        if task.resources
                        else None
                    ),
                    task.start_date.isoformat() if task.start_date else None,
                    task.due_datetime.isoformat() if task.due_datetime else None,
                    task.added_date_time.isoformat() if task.added_date_time else None,
                    (
                        task.last_completed_date.isoformat()
                        if task.last_completed_date
                        else None
                    ),
                    task.list_order,
                    task.list_name,
                    int(task.recurring),
                    (
                        safe_json_dumps(task.recur_every, "null", "recur_every")
                        if task.recur_every
                        else None
                    ),
                    task.recurrences,
                    task.time_estimate,
                    task.time_logged,
                    task.count_required,
                    task.count_completed,
                    (
                        safe_json_dumps(task.chunks, "[]", "chunks")
                        if task.chunks
                        else "[]"
                    ),
                    task.chunk_preference,
                    task.min_chunk_size,
                    task.max_chunk_size,
                    (
                        safe_json_dumps(task.subtasks, "[]", "subtasks")
                        if task.subtasks
                        else "[]"
                    ),
                    (
                        safe_json_dumps(task.dependencies, "[]", "dependencies")
                        if task.dependencies
                        else None
                    ),
                    task.status,
                    task.flexibility,
                    task.effort_level,
                    task.priority,
                    task.previous_priority,
                    safe_json_dumps(
                        task.preferred_work_days, "[]", "preferred_work_days"
                    ),
                    safe_json_dumps(
                        task.time_of_day_preference, "[]", "time_of_day_preference"
                    ),
                    int(task.include_in_schedule),
                    task.global_weight,
                    task.id,
                ),
            )

            if cursor.rowcount == 0:
                # Handle case where task ID doesn't exist - maybe log warning
                print(
                    f"Warning: Task with ID {task.id} not found in database during update."
                )
                # Decide if this should be a fatal error or just a warning
                # raise ValueError(f"Task with ID {task.id} does not exist.")
            else:
                self.conn.commit()  # Commit only if update was successful

            # Update in-memory list references only after successful DB commit
            if cursor.rowcount > 0:
                if old_list_name and old_list_name != task.list_name:
                    # Remove from old list
                    old_task_list = next(
                        (tl for tl in self.task_lists if tl.name == old_list_name), None
                    )
                    if old_task_list:
                        old_task_list.tasks[:] = [
                            t for t in old_task_list.tasks if t.id != task.id
                        ]

                    # Add to new list
                    new_task_list = next(
                        (tl for tl in self.task_lists if tl.name == task.list_name),
                        None,
                    )
                    if new_task_list:
                        # Ensure the task object itself is updated if necessary
                        # (though it should be the same object passed in)
                        new_task_list.add_task_to_model_list(
                            task
                        )  # Use the method to handle order etc.
                else:
                    # Update within the same list
                    current_list = next(
                        (tl for tl in self.task_lists if tl.name == task.list_name),
                        None,
                    )
                    if current_list:
                        for i, t in enumerate(current_list.tasks):
                            if t.id == task.id:
                                current_list.tasks[i] = (
                                    task  # Replace the old task object
                                )
                                break

        except sqlite3.Error as e:
            print(f"Database error while updating task with ID {task.id}: {e}")
            if self.conn:
                self.conn.rollback()
        except Exception as e:
            print(f"Unexpected error while updating task with ID {task.id}: {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            if cursor:
                cursor.close()

    def get_task(self, task_id):
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task_row = cursor.fetchone()

            if not task_row:
                return None

            task_data = dict(task_row)
            task_data["tags"] = (
                safe_json_loads(task_data["tags"], [], "tags", f"for task ID {task_id}")
                if task_data.get("tags")
                else []
            )
            task_data["resources"] = (
                safe_json_loads(
                    task_data["resources"], [], "resources", f"for task ID {task_id}"
                )
                if task_data.get("resources")
                else []
            )
            task_data["recur_every"] = (
                safe_json_loads(
                    task_data["recur_every"],
                    None,
                    "recur_every",
                    f"for task ID {task_id}",
                )
                if task_data.get("recur_every")
                else None
            )
            task_data["subtasks"] = (
                safe_json_loads(
                    task_data["subtasks"], [], "subtasks", f"for task ID {task_id}"
                )
                if task_data.get("subtasks")
                else []
            )
            task_data["dependencies"] = (
                safe_json_loads(
                    task_data["dependencies"],
                    [],
                    "dependencies",
                    f"for task ID {task_id}",
                )
                if task_data.get("dependencies")
                else []
            )
            task_data["chunks"] = (
                safe_json_loads(
                    task_data["chunks"], [], "chunks", f"for task ID {task_id}"
                )
                if task_data.get("chunks")
                else []
            )
            task_data["preferred_work_days"] = (
                safe_json_loads(
                    task_data["preferred_work_days"],
                    [],
                    "preferred_work_days",
                    f"for task ID {task_id}",
                )
                if task_data.get("preferred_work_days")
                else []
            )
            task_data["time_of_day_preference"] = (
                safe_json_loads(
                    task_data["time_of_day_preference"],
                    [],
                    "time_of_day_preference",
                    f"for task ID {task_id}",
                )
                if task_data.get("time_of_day_preference")
                else []
            )

            return Task(**task_data)

        except sqlite3.Error as e:
            print(f"Error fetching task by ID {task_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def manage_recurring_tasks(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE recurring = 1")
            rows = cursor.fetchall()

            rollover_statuses = {"Completed", "Failed", "Skipped"}
            weekday_mapping = {
                "mon": 0,
                "monday": 0,
                "tue": 1,
                "tuesday": 1,
                "wed": 2,
                "wednesday": 2,
                "thu": 3,
                "thursday": 3,
                "fri": 4,
                "friday": 4,
                "sat": 5,
                "saturday": 5,
                "sun": 6,
                "sunday": 6,
            }

            for row in rows:
                task_data = dict(row)
                task_data["tags"] = (
                    safe_json_loads(
                        task_data["tags"],
                        [],
                        "tags",
                        f"while managing recurring task '{task_data.get('name', 'unknown')}'",
                    )
                    if task_data.get("tags")
                    else []
                )
                task_data["resources"] = (
                    safe_json_loads(
                        task_data["resources"],
                        [],
                        "resources",
                        f"while managing recurring task '{task_data.get('name', 'unknown')}'",
                    )
                    if task_data.get("resources")
                    else []
                )
                task_data["recur_every"] = (
                    safe_json_loads(
                        task_data["recur_every"],
                        None,
                        "recur_every",
                        f"while managing recurring task '{task_data.get('name', 'unknown')}'",
                    )
                    if task_data.get("recur_every")
                    else None
                )
                task_data["subtasks"] = (
                    safe_json_loads(
                        task_data["subtasks"],
                        [],
                        "subtasks",
                        f"while managing recurring task '{task_data.get('name', 'unknown')}'",
                    )
                    if task_data.get("subtasks")
                    else []
                )
                task_data["dependencies"] = (
                    safe_json_loads(
                        task_data["dependencies"],
                        [],
                        "dependencies",
                        f"while managing recurring task '{task_data.get('name', 'unknown')}'",
                    )
                    if task_data.get("dependencies")
                    else []
                )
                task_data["chunks"] = (
                    safe_json_loads(
                        task_data["chunks"],
                        [],
                        "chunks",
                        f"while managing recurring task '{task_data.get('name', 'unknown')}'",
                    )
                    if task_data.get("chunks")
                    else []
                )
                task_data["preferred_work_days"] = (
                    safe_json_loads(
                        task_data["preferred_work_days"],
                        [],
                        "preferred_work_days",
                        f"while managing recurring task '{task_data.get('name', 'unknown')}'",
                    )
                    if task_data.get("preferred_work_days")
                    else []
                )
                task_data["time_of_day_preference"] = (
                    safe_json_loads(
                        task_data["time_of_day_preference"],
                        [],
                        "time_of_day_preference",
                        f"while managing recurring task '{task_data.get('name', 'unknown')}'",
                    )
                    if task_data.get("time_of_day_preference")
                    else []
                )

                task = Task(**task_data)

                if task.status not in rollover_statuses:
                    continue

                now = datetime.now()
                old_due = task.due_datetime

                # Handle recurrence calculation
                if isinstance(task.recur_every, int):
                    anchor = old_due or task.last_completed_date or now
                    next_due = anchor + timedelta(days=task.recur_every)

                elif isinstance(task.recur_every, list):
                    today = now.date()
                    today_weekday = today.weekday()
                    days_to_next = min(
                        (weekday_mapping[d.lower()] - today_weekday) % 7
                        for d in task.recur_every
                    )
                    start_date = old_due.date() if old_due else today
                    next_due = datetime.combine(
                        start_date + timedelta(days=days_to_next),
                        (old_due or now).time(),
                    )

                else:
                    continue

                if next_due <= now:
                    task.status = "Not Started"
                    task.time_logged = 0 if task.time_estimate else task.time_logged
                    task.count_completed = (
                        0 if task.count_required else task.count_completed
                    )
                    task.recurrences = (task.recurrences or 0) + 1
                    task.due_datetime = next_due

                    self.update_task(task)

        except sqlite3.Error as e:
            print(f"Database error while managing recurring tasks: {e}")
        except Exception as e:
            print(f"Unexpected error while managing recurring tasks: {e}")
        finally:
            if cursor:
                cursor.close()

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
        cursor.execute(
            "SELECT category FROM task_lists WHERE name = ?", (task_list_name,)
        )
        result = cursor.fetchone()
        if result:
            return result["category"]
        return None

    def __del__(self):
        self.conn.close()
