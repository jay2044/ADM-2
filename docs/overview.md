# Files Overview

## Application Core  

### `main.py`  
- **App Initialization** – Initializes the PyQt6 application and sets up the main event loop.  
- **Theme Loading** – Loads and applies a CSS-based theme from `themes/styles.css`.  
- **Main Window Setup** – Instantiates and displays the main window (`MainWindow`).  
- **Graceful Exit** – Ensures the app exits cleanly when the main window is closed.  

---

## UI and Window Management  

### `gui.py`  
- **UI Setup** – Initializes and configures the main window using PyQt6.  
- **Theme Setup** – Applies a default font and theme to the app interface.  
- **Task Management Integration** – Instantiates `TaskManager` for task handling and updates.  
- **Dock Widget Configuration** – Creates and manages dockable widgets (e.g., task list, history, calendar).  
- **Persistent State Management** – Saves and restores window state and open dock widgets using `QSettings`.  
- **Signal Handling** – Connects global signals for handling task list updates dynamically.  
- **Drag-and-Drop Support** – Implements drag-and-drop functionality for task organization.  
- **Conflict Resolution** – Handles task list updates and synchronizes docked widgets accordingly.  

---

## Scheduling and Task Management  

### `schedule_manager.py`  
- **Time Block Management** – Defines and manages user-defined and system-generated time blocks.  
- **Schedule Generation** – Generates a structured schedule by fitting tasks into available time blocks.  
- **Dynamic Scheduling** – Uses OR-Tools CP-SAT to optimize task allocation and resolve conflicts in real-time.  
- **Weight Calculation** – Implements a weighted priority formula based on task attributes.  
- **Conflict Resolution** – Adjusts the schedule dynamically when conflicts arise.  
- **Chunking Tasks** – Divides large tasks into smaller manageable chunks for better scheduling.  
- **Manual Scheduling Override** – Allows manual task assignments without breaking automated scheduling.  
- **Recurrence Handling** – Supports recurring tasks and schedules them automatically.  
- **Open Block Insertion** – Fills empty gaps in the schedule with open blocks for new tasks.  
- **Manual Time Block Editing** – Allows manual adjustment of time blocks while preserving structure.  

---

## Task Management  

### `task_manager.py`  
- **Task and Task Chunk Management** – Defines `Task` and `TaskChunk` objects with attributes like time estimates, chunking preferences, recurring settings, etc.  
- **Task Prioritization and Sorting** – Supports priority-based sorting and filtering for tasks.  
- **Task Dependencies** – Allows tasks to define dependencies that must be resolved before scheduling or completion.  
- **Recurring Task Handling** – Automatically manages recurring tasks.  
- **Task Completion and Progress Tracking** – Tracks task completion and calculates progress based on time logged or count completed.  
- **Subtask Handling** – Allows adding, updating, and reordering of subtasks within tasks.  
- **Tag-Based Filtering** – Supports filtering tasks by assigned tags.  
- **Task Archiving and Restoration** – Supports archiving and restoring tasks and lists.  

---

## UI Components and Widgets  

### `container_widgets.py`  
- **Resource Management** – Allows adding, removing, and managing URLs and file paths associated with a task.  
- **Subtask Management** – Allows adding, editing, deleting, and reordering subtasks.  
- **Tree-Based Task List Management** – Supports hierarchical organization of task lists.  
- **Interactive Checkbox for Task Completion** – Supports marking subtasks as complete.  
- **Drag-and-Drop for Reordering** – Enables drag-and-drop to reorder subtasks and task lists.  

---

## Scheduling and Time Tracking  

### `schedule_widgets.py`  
- **Schedule Settings Configuration** – Allows users to set day start, sleep duration, available hours, and more.  
- **Conflict Resolution** – Handles overlapping time blocks and dynamically adjusts the schedule.  
- **Drag and Drop Task Reordering** – Supports task chunk dragging and dropping between time blocks.  
- **Dynamic Schedule Update** – Auto-calculates available hours based on sleep time and updates them dynamically.  
- **Recurrence Handling** – Marks recurring task chunks and reflects them in the schedule.  

---

## Task Progress and State Management  

### `task_progress_widgets.py`  
- **Task Progress Bar** – Displays overall task progress based on count, time, and subtask completion.  
- **Time Progress Widget** – Tracks time logged versus time estimated.  
- **Signal-Based Updates** – Uses `global_signals` to notify other components when task progress is updated.  

---

## Task List and Toolbar  

### `task_widgets.py`  
- **Drag-and-drop task reordering** – Tasks can be reordered within the list using drag-and-drop.  
- **Multi-selection mode** – Allows selection of multiple tasks for batch actions.  
- **Task sorting** – Tasks can be sorted by queue, stack, or priority.  
- **Context menu for tasks** – Right-clicking a task shows a context menu with options.  
- **Dynamic task label formatting** – Task labels are dynamically styled based on due date, status, and priority.  

---

## Signals and Global State  

### `signals.py`  
- **Global Signal Handling** – Defines a `GlobalSignals` class to manage signals across the app.  
- **Task List Update Signal** – Emits a signal when the task list is updated.  
- **Schedule Refresh Signal** – Emits a signal to trigger a schedule refresh.  

---

## Error Handling and Logging  

### `globals.py`  
- **Color Configuration** – Defines global color constants for different task states.  
- **Main Window Retrieval** – Implements a utility function to get the current main window instance.  
- **Logging** – Captures detailed logs for debugging and performance analysis.  

---

