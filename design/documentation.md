# task_manager.py
This module manages task lists and tasks, providing functionality to add, update, delete, and manage tasks with SQLite as the storage backend. It includes three primary classes: `Task`, `TaskList`, and `TaskListManager`.

### Functions:
- **`sanitize_name(name)`**: 
  - Replaces non-word characters in `name` with underscores.
  - **Parameters**: 
    - `name`: The string to be sanitized.
  - **Returns**: A sanitized version of the name.

## Class: `Task`
Represents an individual task with various properties such as title, description, due date, priority, and recurrence.

### Variables:
- **`id`**: (int) The unique identifier for the task.
- **`title`**: (str) The title of the task.
- **`description`**: (str) A brief description of the task.
- **`due_date`**: (str) The due date of the task in the format 'YYYY-MM-DD'.
- **`due_time`**: (str) The due time of the task in the format 'HH:MM'.
- **`completed`**: (bool) Indicates whether the task is completed.
- **`priority`**: (int) The priority level of the task, ranging from 0 (lowest) to 10 (highest).
- **`is_important`**: (bool) Marks the task as important.
- **`added_date_time`**: (datetime) The date and time when the task was added.
- **`categories`**: (list) A list of categories associated with the task.
- **`recurring`**: (bool) Indicates if the task is recurring.
- **`recur_every`**: (int) The recurrence interval in days.
- **`last_completed_date`**: (datetime) The date and time when the task was last completed.

### Methods:
- **`__init__()`**: Initializes a new task with specified properties.
- **`mark_as_important()`**: Marks the task as important.
- **`unmark_as_important()`**: Unmarks the task as important.
- **`set_priority(priority)`**: Sets the priority level of the task.
- **`set_completed()`**: Marks the task as completed and updates the last completed date.
- **`add_category(category)`**: Adds a new category to the task if it doesn't already exist.
- **`is_category(category)`**: Checks if the task belongs to a specified category.
- **`set_recurring(every)`**: Sets the task as recurring with the specified interval in days.
- **`get_unique_identifier()`**: Returns a unique identifier for the task based on its title, due date, and due time.
- **`__str__()`**: Returns a formatted string representation of the task.

## Class: `TaskList`
Manages a collection of tasks within a specific list.

### Variables:
- **`list_name`**: (str) The name of the task list.
- **`manager`**: (`TaskListManager`) The manager responsible for handling task lists.
- **`tasks`**: (list) A list of `Task` objects belonging to this list.
- **`pin`**: (bool) Indicates if the list is pinned.
- **`queue`**: (bool) Indicates if the tasks in the list should be treated as a queue.
- **`stack`**: (bool) Indicates if the tasks in the list should be treated as a stack.

### Methods:
- **`__init__(list_name, manager, pin=False, queue=False, stack=False)`**: Initializes a new task list with the specified properties.
- **`load_tasks()`**: Loads tasks from the database into the list.
- **`add_task(task)`**: Adds a task to the list and the database.
- **`remove_task(task)`**: Removes a task from the list and the database.
- **`update_task(task)`**: Updates the task in the database.
- **`get_tasks()`**: Returns all tasks in the list, sorted based on the `queue` or `stack` settings.
- **`get_completed_tasks()`**: Returns all completed tasks in the list.
- **`get_important_tasks()`**: Returns all important tasks in the list that are not completed.
- **`get_tasks_filter_category(category)`**: Returns all tasks in the list filtered by a specific category.
- **`get_tasks_filter_priority()`**: Returns all non-completed tasks sorted by priority.
- **`__str__()`**: Returns a formatted string representation of all non-completed tasks in the list.

## Class: `TaskListManager`
Handles all task lists and task operations, including database interactions.

### Variables:
- **`data_dir`**: (str) The directory where the database file is stored.
- **`db_file`**: (str) The path to the SQLite database file.
- **`conn`**: (sqlite3.Connection) The connection object for the SQLite database.
- **`task_lists`**: (list) A list of all task lists managed by this manager.

### Methods:
- **`__init__()`**: Initializes the manager, sets up the database connection, and loads task lists.
- **`create_tables()`**: Creates the necessary tables in the database if they do not exist.
- **`load_task_lists()`**: Loads all task lists from the database.
- **`load_tasks(list_name)`**: Loads all tasks for a specific task list from the database.
- **`add_task_list(list_name, pin=False, queue=False, stack=False)`**: Adds a new task list to the database.
- **`remove_task_list(list_name)`**: Removes a task list and its tasks from the database.
- **`change_task_list_name(task_list, new_name)`**: Changes the name of a task list and updates it in the database.
- **`add_task(task, list_name)`**: Adds a new task to a specific list in the database.
- **`update_task(task)`**: Updates an existing task in the database.
- **`remove_task(task)`**: Removes a task from the database.
- **`update_task_list(task_list)`**: Updates the properties of a task list in the database.
- **`pin_task_list(list_name)`**: Toggles the pinned status of a task list.
- **`get_task_lists()`**: Returns all task lists, with pinned lists appearing first.
- **`get_task_list(task_list_name)`**: Returns a specific task list by its name.
- **`get_task_list_count()`**: Returns the total number of task lists.
- **`manage_recurring_tasks()`**: Manages recurring tasks, resetting their status and due dates as needed.
- **`__del__()`**: Closes the database connection when the manager is deleted.

# gui.py
This module defines the main GUI interface for the task management application. It uses PyQt6 to create a windowed interface that includes task list widgets, history, and calendar docks. The `MainWindow` class is the central component that sets up and manages various UI elements.
### `setup_font(app)` Function
- **Purpose**: Sets up the font for the entire application.
- **Parameters**:
  - `app`: The main application instance.
- **Returns**: None.

## Class: `MainWindow`
The primary class representing the main window of the application. It handles the layout and management of the task lists, docks, and application settings.

### Variables:
- **`task_manager`**: (`TaskListManager`) Instance of the `TaskListManager` that handles the logic for managing task lists.
- **`settings`**: (`QSettings`) Stores application settings such as window geometry and dock states.
- **`left_widget`**: (`QWidget`) The main widget on the left side of the main window.
- **`left_layout`**: (`QVBoxLayout`) The layout for the `left_widget`.
- **`task_list_collection`**: (`TaskListCollection`) Displays a collection of task lists.
- **`left_top_toolbar`**: (`TaskListManagerToolbar`) A toolbar on the left side for managing task lists.
- **`info_bar`**: (`InfoBar`) A widget that shows information about the task list.
- **`stacked_task_list`**: (`TaskListDockStacked`) A stacked widget on the right side that shows detailed tasks.
- **`history_dock`**: (`HistoryDock`) A dock widget that shows the history of completed tasks.
- **`calendar_dock`**: (`QDockWidget`) A dock widget that shows a calendar.

### Methods:

#### `__init__(self, app)`
- **Purpose**: Initializes the `MainWindow` instance, sets up the UI components, and loads the saved settings.
- **Parameters**:
  - `app`: The main application instance.
- **Returns**: None.

#### `setup_ui(self, app)`
- **Purpose**: Sets up the main UI components including the main window, left and right widgets, history, and calendar docks.
- **Parameters**:
  - `app`: The main application instance.
- **Returns**: None.

#### `setup_main_window(self)`
- **Purpose**: Sets up the main window properties like title, size, and position.
- **Parameters**: None.
- **Returns**: None.

#### `options(self)`
- **Purpose**: Configures the dock options such as allowing tabbed docks and nested docks.
- **Parameters**: None.
- **Returns**: None.

#### `setup_layouts(self)`
- **Purpose**: Sets up the layout for the left side of the main window.
- **Parameters**: None.
- **Returns**: None.

#### `setup_left_widgets(self)`
- **Purpose**: Sets up the widgets for the left side of the window, including task list collection, toolbar, and info bar.
- **Parameters**: None.
- **Returns**: None.

#### `setup_right_widgets(self)`
- **Purpose**: Sets up the right side widgets, such as the `TaskListDockStacked`.
- **Parameters**: None.
- **Returns**: None.

#### `setup_history_dock(self)`
- **Purpose**: Sets up the history dock widget to display the history of completed tasks.
- **Parameters**: None.
- **Returns**: None.

#### `setup_calendar_dock(self)`
- **Purpose**: Sets up the calendar dock widget to display a calendar view.
- **Parameters**: None.
- **Returns**: None.

#### `closeEvent(self, event)`
- **Purpose**: Overrides the default close event to save the application settings before closing.
- **Parameters**:
  - `event`: The close event object.
- **Returns**: None.

#### `save_settings(self)`
- **Purpose**: Saves the current window geometry, state, and dock widget positions to `QSettings`.
- **Parameters**: None.
- **Returns**: None.

#### `load_settings(self)`
- **Purpose**: Loads and applies the saved settings for the window geometry, state, and dock widget positions.
- **Parameters**: None.
- **Returns**: None.

#### `restoreDockWidgetGeometry(self, dock_widget, geometry)`
- **Purpose**: Restores the geometry and visibility of a dock widget based on saved settings.
- **Parameters**:
  - `dock_widget`: The dock widget to restore.
  - `geometry`: A dictionary containing geometry data for the dock widget.
- **Returns**: None.

#### `saveDockWidgetGeometry(self, dock_widget)`
- **Purpose**: Saves the geometry and visibility of a dock widget as a dictionary.
- **Parameters**:
  - `dock_widget`: The dock widget whose geometry will be saved.
- **Returns**: A dictionary containing the dock widget's geometry and visibility state.

#### `toggle_stacked_task_list(self)`
- **Purpose**: Toggles the visibility of the stacked task list widget.
- **Parameters**: None.
- **Returns**: None.

#### `toggle_history(self)`
- **Purpose**: Toggles the visibility of the history dock.
- **Parameters**: None.
- **Returns**: None.

#### `toggle_calendar(self)`
- **Purpose**: Toggles the visibility of the calendar dock.
- **Parameters**: None.
- **Returns**: None.

#### `clear_settings(self)`
- **Purpose**: Clears all saved settings and prompts the user to restart the application.
- **Parameters**: None.
- **Returns**: None.

# widgets.py


This module contains various custom widgets used in the GUI for the task management application. These widgets include task representations, task list views, toolbars, and other UI components necessary for managing and displaying tasks.

## Class: `TaskWidget`
Represents a single task as a widget in the task list. Provides a checkbox for marking the task as completed and a radio button for marking it as important.

### Variables:
- **`task_list_widget`**: (`TaskListWidget`) Reference to the parent task list widget.
- **`task`**: (`Task`) The task object represented by this widget.
- **`is_dragging`**: (`bool`) Indicates whether the widget is currently being dragged.

### Methods:

#### `__init__(self, task_list_widget, task)`
- **Purpose**: Initializes the widget with the given task and parent task list widget.
- **Parameters**:
  - `task_list_widget`: The parent task list widget.
  - `task`: The task to be represented by this widget.
- **Returns**: None.

#### `setup_ui(self)`
- **Purpose**: Sets up the UI elements of the widget, including the checkbox and radio button.
- **Parameters**: None.
- **Returns**: None.

#### `setup_timer(self)`
- **Purpose**: Sets up a timer to detect long presses for editing the task.
- **Parameters**: None.
- **Returns**: None.

#### `mousePressEvent(self, event)`
- **Purpose**: Starts a timer on left mouse button press to detect if the task is being dragged.
- **Parameters**:
  - `event`: The mouse press event.
- **Returns**: None.

#### `mouseMoveEvent(self, event)`
- **Purpose**: Detects if the mouse is being dragged and stops the timer if so.
- **Parameters**:
  - `event`: The mouse move event.
- **Returns**: None.

#### `mouseReleaseEvent(self, event)`
- **Purpose**: Stops the timer and opens the edit dialog if the task was not dragged.
- **Parameters**:
  - `event`: The mouse release event.
- **Returns**: None.

#### `edit_task(self)`
- **Purpose**: Opens the edit dialog for the task when the task widget is clicked.
- **Parameters**: None.
- **Returns**: None.

#### `task_checked(self, state)`
- **Purpose**: Updates the task completion status when the checkbox is toggled and refreshes the task list.
- **Parameters**:
  - `state`: The new state of the checkbox.
- **Returns**: None.

#### `mark_important(self)`
- **Purpose**: Toggles the importance of the task and updates the task list.
- **Parameters**: None.
- **Returns**: None.

## Class: `TaskListWidget`
A widget that represents a list of tasks. Allows tasks to be displayed, dragged, and dropped within the list.

### Variables:
- **`task_list_name`**: (`str`) The name of the task list.
- **`parent`**: (`MainWindow`) The main window containing this widget.
- **`manager`**: (`TaskListManager`) The manager responsible for managing the task list.
- **`task_list`**: (`TaskList`) The task list object containing the tasks.

### Methods:

#### `__init__(self, task_list_name, parent, pin, queue, stack)`
- **Purpose**: Initializes the task list widget with the given task list name and settings.
- **Parameters**:
  - `task_list_name`: The name of the task list.
  - `parent`: The parent widget (main window).
  - `pin`: Indicates if the task list is pinned.
  - `queue`: Indicates if the task list is treated as a queue.
  - `stack`: Indicates if the task list is treated as a stack.
- **Returns**: None.

#### `setup_ui(self)`
- **Purpose**: Sets up the UI properties of the task list widget, such as enabling drag and drop.
- **Parameters**: None.
- **Returns**: None.

#### `load_tasks(self, priority_filter=False)`
- **Purpose**: Loads the tasks from the task list and displays them in the widget.
- **Parameters**:
  - `priority_filter`: Whether to filter tasks by priority.
- **Returns**: None.

#### `delete_task(self, task)`
- **Purpose**: Deletes a task from the task list and the widget.
- **Parameters**:
  - `task`: The task to be deleted.
- **Returns**: None.

#### `startDrag(self, supportedActions)`
- **Purpose**: Initiates a drag operation when a task item is dragged.
- **Parameters**:
  - `supportedActions`: The supported drag actions.
- **Returns**: None.

#### `dragEnterEvent(self, event)`
- **Purpose**: Accepts the drag event if the source is the same widget.
- **Parameters**:
  - `event`: The drag enter event.
- **Returns**: None.

#### `dragMoveEvent(self, event)`
- **Purpose**: Handles the drag move event.
- **Parameters**:
  - `event`: The drag move event.
- **Returns**: None.

## Class: `TaskListManagerToolbar`
A toolbar for managing task lists, providing buttons for adding, toggling, and deleting task lists.

### Methods:

#### `__init__(self, parent=None)`
- **Purpose**: Initializes the toolbar with buttons for task list operations.
- **Parameters**:
  - `parent`: The parent widget.
- **Returns**: None.

#### `add_action(self, text, parent, function)`
- **Purpose**: Adds a button to the toolbar with the specified text and function.
- **Parameters**:
  - `text`: The text label for the button.
  - `parent`: The parent widget.
  - `function`: The function to be called when the button is clicked.
- **Returns**: None.

## Class: `TaskListCollection`
Represents a collection of task lists. Allows adding, removing, and managing multiple task lists.

### Variables:
- **`parent`**: (`MainWindow`) The main window containing this widget.
- **`dragging`**: (`bool`) Indicates if a task list item is being dragged.
- **`drag_item`**: (`QListWidgetItem`) The task list item being dragged.

### Methods:

#### `__init__(self, parent)`
- **Purpose**: Initializes the task list collection widget.
- **Parameters**:
  - `parent`: The parent widget (main window).
- **Returns**: None.

#### `setup_ui(self)`
- **Purpose**: Sets up the UI properties and context menu for the task list collection.
- **Parameters**: None.
- **Returns**: None.

#### `load_task_lists(self)`
- **Purpose**: Loads all task lists from the task manager and displays them.
- **Parameters**: None.
- **Returns**: None.

#### `add_task_list(self, task_list_name="", pin=False, queue=False, stack=False)`
- **Purpose**: Adds a new task list to the collection.
- **Parameters**:
  - `task_list_name`: The name of the new task list.
  - `pin`: Indicates if the task list is pinned.
  - `queue`: Indicates if the task list is treated as a queue.
  - `stack`: Indicates if the task list is treated as a stack.
- **Returns**: None.

#### `switch_stack_widget_by_hash(self, current)`
- **Purpose**: Switches the current task list widget in the stack based on its hash.
- **Parameters**:
  - `current`: The current task list item.
- **Returns**: None.

#### `task_list_collection_context_menu(self, position)`
- **Purpose**: Displays a context menu for the task list collection.
- **Parameters**:
  - `position`: The position to display the context menu.
- **Returns**: None.

#### `rename_task_list(self, task_list_widget)`
- **Purpose**: Renames a task list in the collection.
- **Parameters**:
  - `task_list_widget`: The task list widget to be renamed.
- **Returns**: None.

#### `pin_task_list(self, task_list)`
- **Purpose**: Pins or unpins a task list in the collection.
- **Parameters**:
  - `task_list`: The task list to be pinned or unpinned.
- **Returns**: None.

#### `duplicate_task_list(self, task_list_widget)`
- **Purpose**: Duplicates a task list in the collection.
- **Parameters**:
  - `task_list_widget`: The task list widget to be duplicated.
- **Returns**: None.

#### `delete_task_list(self, task_list)`
- **Purpose**: Deletes a task list from the collection.
- **Parameters**:
  - `task_list`: The task list to be deleted.
- **Returns**: None.

#### `startDrag(self, supportedActions)`
- **Purpose**: Initiates a drag operation when a task list item is dragged.
- **Parameters**:
  - `supportedActions`: The supported drag actions.
- **Returns**: None.

#### `dragMoveEvent(self, event)`
- **Purpose**: Handles the drag move event within the widget.
- **Parameters**:
  - `event`: The drag move event.
- **Returns**: None.

#### `dropEvent(self, event)`
- **Purpose**: Handles the drop event within the widget.
- **Parameters**:
  - `

event`: The drop event.
- **Returns**: None.

#### `eventFilter(self, obj, event)`
- **Purpose**: Filters events to detect when a task list item is dropped outside the widget.
- **Parameters**:
  - `obj`: The object that received the event.
  - `event`: The event to be filtered.
- **Returns**: None.

## Class: `InfoBar`
Displays information about the current task list, such as the number of tasks.

### Variables:
- **`task_manager`**: (`TaskListManager`) Reference to the task manager.
- **`task_list_count_label`**: (`QLabel`) Label displaying the number of task lists.

### Methods:

#### `__init__(self, parent)`
- **Purpose**: Initializes the info bar with the task list count.
- **Parameters**:
  - `parent`: The parent widget.
- **Returns**: None.

#### `update_task_list_count_label(self)`
- **Purpose**: Updates the task list count label with the current number of task lists.
- **Parameters**: None.
- **Returns**: None.

## Class: `TaskListToolbar`
A toolbar for managing tasks within a task list. Provides buttons for adding tasks, setting queue or stack mode, and sorting by priority.

### Methods:

#### `__init__(self, parent=None)`
- **Purpose**: Initializes the toolbar with buttons for task operations.
- **Parameters**:
  - `parent`: The parent widget.
- **Returns**: None.

#### `add_action(self, text, parent, function)`
- **Purpose**: Adds a button to the toolbar with the specified text and function.
- **Parameters**:
  - `text`: The text label for the button.
  - `parent`: The parent widget.
  - `function`: The function to be called when the button is clicked.
- **Returns**: None.

## Class: `TaskListDockStacked`
A dock widget that displays task lists in a stacked layout.

### Variables:
- **`priority_filter`**: (`bool`) Indicates if tasks should be filtered by priority.
- **`parent`**: (`MainWindow`) The main window containing this widget.
- **`task_manager`**: (`TaskListManager`) Reference to the task manager.

### Methods:

#### `__init__(self, parent=None)`
- **Purpose**: Initializes the dock widget with a stacked layout.
- **Parameters**:
  - `parent`: The parent widget.
- **Returns**: None.

#### `set_allowed_areas(self)`
- **Purpose**: Sets the allowed dock areas for the widget.
- **Parameters**: None.
- **Returns**: None.

#### `setup_ui(self)`
- **Purpose**: Sets up the UI elements of the dock widget.
- **Parameters**: None.
- **Returns**: None.

#### `setup_toolbar(self)`
- **Purpose**: Sets up the toolbar for managing tasks.
- **Parameters**: None.
- **Returns**: None.

#### `setup_stack_widget(self)`
- **Purpose**: Sets up the stacked widget layout.
- **Parameters**: None.
- **Returns**: None.

#### `add_task(self)`
- **Purpose**: Opens the dialog to add a new task.
- **Parameters**: None.
- **Returns**: None.

#### `show_add_task_dialog(self, task_list_widget)`
- **Purpose**: Displays the dialog for adding a new task to the specified task list widget.
- **Parameters**:
  - `task_list_widget`: The task list widget to add the task to.
- **Returns**: None.

#### `set_queue(self)`
- **Purpose**: Toggles the queue mode for the current task list.
- **Parameters**: None.
- **Returns**: None.

#### `set_stack(self)`
- **Purpose**: Toggles the stack mode for the current task list.
- **Parameters**: None.
- **Returns**: None.

#### `priority_sort(self)`
- **Purpose**: Sorts tasks by priority.
- **Parameters**: None.
- **Returns**: None.

#### `get_current_task_list_widget(self)`
- **Purpose**: Gets the current task list widget.
- **Parameters**: None.
- **Returns**: The current task list widget.

## Class: `TaskListDock`
A dock widget representing a task list. Allows adding tasks and toggling queue and stack modes.

### Variables:
- **`task_list_widget`**: (`TaskListWidget`) The widget representing the task list.
- **`priority_filter`**: (`bool`) Indicates if tasks should be filtered by priority.
- **`parent`**: (`MainWindow`) The main window containing this widget.
- **`task_manager`**: (`TaskListManager`) Reference to the task manager.

### Methods:

#### `__init__(self, task_list_name, parent=None)`
- **Purpose**: Initializes the dock widget with the specified task list name.
- **Parameters**:
  - `task_list_name`: The name of the task list.
  - `parent`: The parent widget.
- **Returns**: None.

#### `set_allowed_areas(self)`
- **Purpose**: Sets the allowed dock areas for the widget.
- **Parameters**: None.
- **Returns**: None.

#### `setup_ui(self)`
- **Purpose**: Sets up the UI elements of the dock widget.
- **Parameters**: None.
- **Returns**: None.

#### `setup_toolbar(self)`
- **Purpose**: Sets up the toolbar for managing tasks.
- **Parameters**: None.
- **Returns**: None.

#### `add_task(self)`
- **Purpose**: Opens the dialog to add a new task.
- **Parameters**: None.
- **Returns**: None.

#### `show_add_task_dialog(self, task_list_widget)`
- **Purpose**: Displays the dialog for adding a new task to the specified task list widget.
- **Parameters**:
  - `task_list_widget`: The task list widget to add the task to.
- **Returns**: None.

#### `set_queue(self)`
- **Purpose**: Toggles the queue mode for the task list.
- **Parameters**: None.
- **Returns**: None.

#### `set_stack(self)`
- **Purpose**: Toggles the stack mode for the task list.
- **Parameters**: None.
- **Returns**: None.

#### `priority_sort(self)`
- **Purpose**: Sorts tasks by priority.
- **Parameters**: None.
- **Returns**: None.

## Class: `HistoryDock`
A dock widget that displays the history of completed tasks.

### Variables:
- **`parent`**: (`MainWindow`) The main window containing this widget.
- **`history_widget`**: (`QWidget`) The widget displaying the history list.
- **`history_layout`**: (`QVBoxLayout`) The layout for the history widget.
- **`history_list`**: (`QListWidget`) The list widget displaying completed tasks.

### Methods:

#### `__init__(self, parent)`
- **Purpose**: Initializes the history dock widget.
- **Parameters**:
  - `parent`: The parent widget.
- **Returns**: None.

#### `set_allowed_areas(self)`
- **Purpose**: Sets the allowed dock areas for the widget.
- **Parameters**: None.
- **Returns**: None.

#### `toggle_history(self)`
- **Purpose**: Toggles the visibility of the history dock.
- **Parameters**: None.
- **Returns**: None.

#### `update_history(self)`
- **Purpose**: Updates the history list with completed tasks.
- **Parameters**: None.
- **Returns**: None.

# control.py
## Class: `CustomDateEdit`
A custom date editing widget that extends `QDateEdit` to provide additional functionality, such as setting the current date when the widget gains focus if it contains a default placeholder date.

### Variables:
- **`parent`**: (`QWidget`) The parent widget.

### Methods:

#### `__init__(self, parent=None)`
- **Purpose**: Initializes the `CustomDateEdit` widget with a calendar popup.
- **Parameters**:
  - `parent`: The parent widget (default is `None`).
- **Returns**: None.

#### `focusInEvent(self, event)`
- **Purpose**: Sets the date to the current date if the widget contains a placeholder date (`2000-01-01`) when it gains focus.
- **Parameters**:
  - `event`: The focus event.
- **Returns**: None.

## Class: `AddTaskDialog`
A dialog for adding new tasks to a task list. Includes fields for entering the task title, description, due date, due time, and importance.

### Variables:
- **`title_edit`**: (`QLineEdit`) Input field for the task title.
- **`description_edit`**: (`QLineEdit`) Input field for the task description.
- **`due_date_edit`**: (`CustomDateEdit`) Custom date input field for the task due date.
- **`due_time_edit`**: (`QTimeEdit`) Input field for the task due time.
- **`important_checkbox`**: (`QCheckBox`) Checkbox to mark the task as important.
- **`buttons`**: (`QDialogButtonBox`) Dialog button box containing "Ok" and "Cancel" buttons.

### Methods:

#### `__init__(self, parent=None)`
- **Purpose**: Initializes the dialog with input fields for creating a new task.
- **Parameters**:
  - `parent`: The parent widget (default is `None`).
- **Returns**: None.

#### `get_task_data(self)`
- **Purpose**: Retrieves the entered task data from the input fields.
- **Parameters**: None.
- **Returns**: A dictionary containing the task data:
  - `title`: The task title.
  - `description`: The task description.
  - `due_date`: The task due date in `yyyy-MM-dd` format.
  - `due_time`: The task due time in `HH:mm` format.
  - `is_important`: Whether the task is marked as important (`True` or `False`).

## Class: `EditTaskDialog`
A dialog for editing an existing task in a task list. Allows modifying the task's title, description, due date, due time, priority, and importance. Also provides a delete button to remove the task.

### Variables:
- **`task`**: (`Task`) The task object to be edited.
- **`task_list_widget`**: (`TaskListWidget`) The parent task list widget containing this task.
- **`title_edit`**: (`QLineEdit`) Input field for the task title, pre-filled with the current title.
- **`description_edit`**: (`QLineEdit`) Input field for the task description, pre-filled with the current description.
- **`due_date_edit`**: (`CustomDateEdit`) Custom date input field for the task due date, pre-filled with the current due date or a default date if none exists.
- **`due_time_edit`**: (`QTimeEdit`) Input field for the task due time, pre-filled with the current due time or default time if none exists.
- **`priority_spinbox`**: (`QSpinBox`) Spin box for setting the task priority, pre-filled with the current priority.
- **`important_checkbox`**: (`QCheckBox`) Checkbox to mark the task as important, pre-checked based on the current importance status.
- **`delete_button`**: (`QPushButton`) Button to delete the task.
- **`buttons`**: (`QDialogButtonBox`) Dialog button box containing "Ok" and "Cancel" buttons.

### Methods:

#### `__init__(self, task, task_list_widget, parent=None)`
- **Purpose**: Initializes the dialog with the existing task data for editing.
- **Parameters**:
  - `task`: The task to be edited.
  - `task_list_widget`: The parent task list widget.
  - `parent`: The parent widget (default is `None`).
- **Returns**: None.

#### `get_task_data(self)`
- **Purpose**: Retrieves the modified task data from the input fields.
- **Parameters**: None.
- **Returns**: A dictionary containing the updated task data:
  - `title`: The updated task title.
  - `description`: The updated task description.
  - `due_date`: The updated task due date in `yyyy-MM-dd` format.
  - `due_time`: The updated task due time in `HH:mm` format.
  - `priority`: The updated task priority (integer).
  - `is_important`: Whether the task is marked as important (`True` or `False`).

#### `delete_task_button_action(self)`
- **Purpose**: Deletes the task from the task list and closes the dialog.
- **Parameters**: None.
- **Returns**: None.