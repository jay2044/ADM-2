# Advanced Day Manager (ADM-2)

## Introduction

*Advanced Day Manager* (ADM-2) is a comprehensive, open-source task management and scheduling application designed to streamline day-to-day operations. It combines task management with automated scheduling, allowing users to prioritize tasks, track progress, and generate a structured daily plan. ADM-2 is ideal for both students managing assignments and professionals optimizing their workflow.

## Project Structure

The project is organized into several directories and files, each serving a specific purpose:

```
/ADM-2
|-- /.idea
|-- /core
|-- /fonts
|-- /tests
|-- /themes
|-- /ui
|-- /widgets
|-- README.md
```

### Detailed Breakdown of the Project

#### 1. `/core`

- **globals.py**: Defines global constants and utility functions for the application.
- **schedule_manager.py**: Manages the scheduling logic, including time blocks, task weights, and schedule generation.
- **signals.py**: Implements custom signals using PyQt for inter-component communication.
- **task_manager.py**: Handles task-related logic, including task creation, updating, and management.

#### 2. `/ui`

- **gui.py**: Contains the main graphical user interface setup, including the main window and its components.
- **main.py**: Entry point for the application, setting up the application and loading the main window.

#### 3. `/widgets`

- **container_widgets.py**: Defines various container widgets used throughout the application, such as the `ResourcesWidget` for handling task resources.
- **dock_widgets.py**: Implements dockable widgets for displaying task details and other information.
- **input_widgets.py**: Provides input widgets for user interaction, such as the `TagInputWidget` for managing task tags.
- **schedule_widgets.py**: Contains widgets related to scheduling, including the `ScheduleViewWidget`.
- **task_progress_widgets.py**: Widgets to display task progress, like `TaskProgressBar`.
- **task_widgets.py**: Implements the task-related widgets used in the task list view.
- **toolbar_widgets.py**: Contains toolbar widgets for task and list management.

#### 4. `/themes`

- **styles.css**: Main stylesheet for the application.
- **retro_theme.qss**: A retro-themed stylesheet for the application.

#### 5. `/tests`

This directory is intended for unit tests, though specific test files are empty as of now.

#### 6. `/fonts`

This directory is reserved for font files used in the application.

#### 7. `/.idea`

Contains project configuration files for the IDE, which are typically used by JetBrains IDEs like PyCharm.

### Installation & Running

#### Manual Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/ADM-2.git
   cd adm
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run ADM:**
   ```bash
   python main.py
   ```

#### Contributing

Contributions are welcome. Whether you're adding new features, fixing bugs, or improving documentation, feel free to open an issue or submit a pull request.

#### License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

ADM-2 continues to evolve, focusing on flexible organization, automated scheduling, and user control to become indispensable for effective day management. Try ADM-2 today and enhance your productivity!