# Main Technologies Used  

## Programming Language  
- **Python** – Core language for backend logic, scheduling, and UI management.  

---

## GUI Framework  
- **PyQt6** – Provides the graphical interface, including main window, widgets, dialogs, and dynamic updates.  
  - `PyQt6.QtCore` – Core utilities for event handling, signals, and threading.  
  - `PyQt6.QtWidgets` – Provides widgets like buttons, labels, list views, and dialogs.  
  - `PyQt6.QtGui` – Handles styling, font rendering, and advanced UI customization.  

---

## Scheduling Engine  
- **OR-Tools CP-SAT Solver** – Google's Constraint Programming Solver used for complex scheduling and conflict resolution.  
  - `from ortools.sat.python import cp_model` – Core import for CP-SAT Solver.  

---

## Database  
- **SQLite** – Lightweight, file-based relational database used to store tasks, schedules, and settings.  
  - `sqlite3` – Python standard library for SQLite database integration.  

---