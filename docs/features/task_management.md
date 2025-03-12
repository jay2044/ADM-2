# Task Management System – ADM-2  
This document explains the inner workings of the task management system in ADM-2. It covers the architecture, data structures, task scheduling logic, and how recurring and complex tasks are handled.  

---

## Overview  
The task management system in ADM-2 is designed to handle complex task scheduling, prioritization, and conflict resolution. It allows for flexible task definitions with support for subtasks, recurring tasks, and custom scheduling constraints. Tasks are broken into smaller, manageable chunks that can be dynamically scheduled into time blocks based on user-defined priorities and system logic.

ADM-2 uses an SQLite-based backend to store task data persistently, ensuring that changes to task states, order, and priorities are reflected across sessions.

---
## **High-Level Overview**  
The task management system is based on a hierarchical structure with four key components:  

1. **Tasks**  
   - A task represents a single unit of work. Tasks are defined by attributes like time estimate, priority, effort level, flexibility, and completion status.  
   - Tasks can have subtasks, dependencies, and recurrence patterns.  
   - Tasks are broken down into smaller `TaskChunk` objects for more granular scheduling.  

2. **Task Chunks**  
   - Tasks are automatically or manually divided into `TaskChunk` objects.  
   - Chunks can represent time-based or count-based units of work (e.g., 30 minutes or 10 repetitions).  
   - Chunks are dynamically scheduled into available time blocks based on task priority and time of day preference.  

3. **Task Lists**  
   - Tasks are grouped into task lists for better organization and filtering.  
   - Task lists can be associated with specific categories and have custom sorting and filtering rules.  

4. **Task Manager**  
   - The `TaskManager` is responsible for coordinating task creation, scheduling, and conflict resolution.  
   - It manages task state persistence through an SQLite database.  
   - It dynamically adjusts the schedule based on real-time progress and conflicts.  

###  **How It All Works Together**  
- The user creates a task and defines its attributes.  
- The task is broken into manageable chunks based on time estimates and scheduling rules.  
- The `TaskManager` assigns chunks to available time blocks, adjusting dynamically based on real-time progress and conflicts.  
- If a task runs over time or a new task is added, the schedule automatically updates to handle the conflict.  
- Recurring tasks are automatically reset and rescheduled based on user-defined recurrence patterns.  

---
## Architecture  
### Core Components  
The task management system is composed of the following core classes:  

| **Component** | **Description** |  
|-------------|----------------|  
| `TaskChunk` | Represents a small portion of a task (e.g., 30 minutes of work). Chunks are used to schedule parts of a task into a time block. |  
| `Task` | Represents a single task, including details like time estimate, priority, status, subtasks, and dependencies. Tasks are composed of one or more `TaskChunk` objects. |  
| `TaskList` | A collection of related tasks grouped under a specific category. Tasks can be sorted and filtered based on user preferences. |  
| `TaskManager` | The central controller that manages tasks and task lists, handles database operations, and resolves conflicts. |  

---

## 1. **TaskChunk**  
The `TaskChunk` class allows tasks to be divided into smaller pieces that can be scheduled independently. This enables more granular scheduling and makes it easier to adjust for conflicts and shifting priorities.  

### Attributes  
| Attribute | Description |  
|----------|-------------|  
| `id` | Unique identifier for the chunk. |  
| `task` | Reference to the parent task. |  
| `chunk_type` | `"manual"`, `"auto"`, or `"placed"` — Defines how the chunk is generated. |  
| `unit` | `"time"` or `"count"` — Represents the type of work unit. |  
| `size` | Size of the chunk (e.g., duration in hours or count value). |  
| `date` | Date on which the chunk is scheduled. |  
| `timeblock` | Reference to the assigned time block. |  
| `is_recurring` | `True` if the chunk is part of a recurring task. |  
| `status` | `"active"`, `"locked"`, `"completed"`, `"flagged"`, `"failed"`. |  

### Methods  
| Method | Description |  
|--------|-------------|  
| `update_status()` | Updates the status of the chunk based on its scheduling state. |  
| `mark_completed()` | Marks the chunk as completed. |  
| `mark_failed()` | Marks the chunk as failed. |  
| `split(ratios)` | Splits the chunk into smaller chunks based on the provided ratios. Used for auto-scheduling. |  

---

## 2. **Task**  
The `Task` class represents a single task with rich attributes. Tasks can be broken into chunks, assigned to time blocks, and tracked based on progress and completion state.  

### Attributes  
| Attribute | Description |  
|----------|-------------|  
| `name` | Name of the task. |  
| `description` | Description of the task. |  
| `list_name` | Name of the list to which the task belongs. |  
| `tags` | List of tags for organizing and filtering. |  
| `time_estimate` | Estimated time required to complete the task. |  
| `count_required` | Total count of actions required to complete the task. |  
| `priority` | Task priority on a scale from `0` (low) to `10` (critical). |  
| `status` | `"Not Started"`, `"In Progress"`, `"Completed"`, `"Failed"`, `"On Hold"`. |  
| `due_datetime` | Due date and time for the task. |  
| `flexibility` | `"Strict"`, `"Flexible"`, `"Very Flexible"`. |  
| `preferred_work_days` | List of preferred days for scheduling the task. |  
| `effort_level` | `"Low"`, `"Medium"`, `"High"`. |  
| `subtasks` | List of subtasks (including order and completion status). |  
| `dependencies` | List of other tasks that must be completed first. |  

### Methods  
| Method | Description |  
|--------|-------------|  
| `add_chunk()` | Creates and assigns a new chunk to the task. |  
| `update_chunk()` | Updates the state of an existing chunk. |  
| `remove_chunk()` | Removes a chunk from the task. |  
| `set_priority()` | Changes the task's priority level. |  
| `set_recurring()` | Marks the task as recurring. |  
| `calculate_progress()` | Calculates progress based on time logged, count completed, or subtasks completed. |  

---

## 3. **TaskList**  
The `TaskList` class allows tasks to be grouped into logical collections for better organization and filtering.  

### Attributes  
| Attribute | Description |  
|----------|-------------|  
| `name` | Name of the task list. |  
| `category` | Category to which the list belongs. |  
| `notifications_enabled` | Boolean — True if notifications are enabled. |  
| `sort_by_priority` | Boolean — True if tasks are sorted by priority. |  
| `tasks` | List of tasks in the list. |  

### Methods  
| Method | Description |  
|--------|-------------|  
| `add_task_to_model_list()` | Adds a task to the list and sets its order. |  
| `get_tasks()` | Returns all tasks in the list. |  
| `get_completed_tasks()` | Returns all completed tasks in the list. |  
| `get_tasks_filtered_by_tag()` | Returns tasks filtered by a specific tag. |  

---

## 4. **TaskManager**  
The `TaskManager` class manages task creation, modification, and scheduling. It interacts directly with the SQLite database and handles recurring task management.  

### Methods  
| Method | Description |  
|--------|-------------|  
| `add_task()` | Adds a new task to the database. |  
| `remove_task()` | Removes a task from the database. |  
| `update_task()` | Updates the attributes of an existing task. |  
| `get_task()` | Retrieves a task by ID. |  
| `manage_recurring_tasks()` | Resets recurring tasks and generates new instances as needed. |  
| `initialize_system_category()` | Creates a protected "System" category for quick tasks. |  

### How It Works  
1. **Task Creation:**  
   - A new task is created and assigned to a `TaskList`.  
   - Task properties (e.g., priority, flexibility, status) are recorded in the SQLite database.  

2. **Chunking:**  
   - Tasks are automatically divided into chunks based on size and scheduling rules.  
   - Chunks are created when tasks are added or modified.  

3. **Scheduling:**  
   - ADM-2 assigns chunks to available time blocks based on priority, preferred time of day, and available hours.  
   - Conflicts are resolved automatically using dynamic rescheduling.  

4. **Real-Time Updates:**  
   - If a task is completed early or delayed, the schedule is adjusted in real time.  
   - If a conflict occurs, ADM-2 will either shift tasks forward or reassign time blocks.  

5. **Recurring Tasks:**  
   - Tasks with recurrence settings are reset based on their schedule.  
   - Tasks are automatically re-created based on recurrence rules (e.g., every Monday).  

---

## **Conflict Resolution**  
1. If two tasks are scheduled at the same time:  
   - Higher-priority task is scheduled first.  
   - Lower-priority task is rescheduled or broken into smaller chunks.  

2. If a task exceeds its scheduled time:  
   - Subsequent tasks are pushed back.  
   - Lower-priority tasks may be rescheduled to another day.  

3. If a recurring task conflicts with a user-defined task:  
   - The user-defined task takes priority.  

---

This document serves as a technical reference for extending or modifying ADM-2's task management capabilities.