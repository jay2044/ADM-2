from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpacerItem, QSizePolicy, QScrollArea, QFrame, QGridLayout, QListWidget
)
from PyQt6.QtCore import Qt
import sys


class ProportionalGrid(QWidget):
    def __init__(self, num_rows):
        super().__init__()
        self.num_rows = num_rows
        self.row_proportions = [1] * num_rows  # Default equal proportions
        self.rows = []
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setup_grid()

    def setup_grid(self):
        for i in range(self.num_rows):
            self._add_row(i)

    def set_proportions(self, proportions):
        if len(proportions) != self.num_rows:
            raise ValueError("Number of proportions must match the number of rows.")
        self.row_proportions = proportions
        self.update_row_heights()

    def update_row_heights(self):
        for i, proportion in enumerate(self.row_proportions):
            self.layout.setRowStretch(i, proportion)

    def add_widget_to_row(self, row_index, widget, column_index=0):
        if 0 <= row_index < self.num_rows:
            # Clear any existing layout in that cell before adding a new one
            cell_widget = self.rows[row_index][column_index]
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(0)
            cell_layout.addWidget(widget)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        else:
            raise IndexError("Row index out of range.")

    def add_row(self, proportion=1):
        row_index = self.num_rows
        self.num_rows += 1
        self.row_proportions.append(proportion)
        self._add_row(row_index)
        self.update_row_heights()

    def _add_row(self, row_index):
        timescale_widget = QWidget()
        tasks_widget = QWidget()
        timescale_widget.setObjectName(f"Timescale_Row_{row_index}")
        tasks_widget.setObjectName(f"Tasks_Row_{row_index}")

        self.layout.addWidget(timescale_widget, row_index, 0)
        self.layout.addWidget(tasks_widget, row_index, 1)
        self.layout.setColumnStretch(0, 1)  # Narrower for timescale
        self.layout.setColumnStretch(1, 3)  # Wider for tasks

        self.rows.append([timescale_widget, tasks_widget])

    def get_row_count(self):
        return self.num_rows


class ScheduleViewWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Sample tasks covering multiple hours
        self.time_blocks = [
            ["4:00 AM", "6:00 AM", "Early Task"],
            ["4:30 AM", "5:30 AM", "Another Early Task"],
            ["6:00 AM", "7:00 AM", "Morning Task"],
            ["6:15 AM", "7:45 AM", "Overlapping Morning Task"],
            ["10:00 AM", "12:00 PM", "Midday Task 1"],
            ["10:30 AM", "12:00 PM", "Midday Task 2"],
            ["2:00 PM", "3:00 PM", "Afternoon Task"],
            ["2:30 PM", "4:00 PM", "Long Afternoon Task"]
        ]
        self.initUI()

    def initUI(self):
        self.setFixedWidth(300)
        self.mainLayout = QVBoxLayout(self)

        # Top Buttons Layout
        topLayout = QHBoxLayout()
        self.expandBtn = QPushButton("Expand")
        self.quickTaskBtn = QPushButton("Add Quick Task")
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        topLayout.addWidget(self.expandBtn)
        topLayout.addItem(spacer)
        topLayout.addWidget(self.quickTaskBtn)
        self.mainLayout.addLayout(topLayout)

        # View Selector
        viewSelectorLayout = QHBoxLayout()
        self.prevBtn = QPushButton("<")
        self.viewLabel = QLabel("Day")
        self.nextBtn = QPushButton(">")
        viewSelectorLayout.addWidget(self.prevBtn)
        viewSelectorLayout.addWidget(self.viewLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        viewSelectorLayout.addWidget(self.nextBtn)
        self.mainLayout.addLayout(viewSelectorLayout)

        # Scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.container = QWidget()
        self.timeAndTasksLayout = QVBoxLayout(self.container)
        self.timeAndTasksLayout.setContentsMargins(0, 0, 0, 0)
        self.timeAndTasksLayout.setSpacing(0)

        # Build the time grid: Each hour from 4 AM to 4 AM next day (24 hours total)
        self.start_time = "4:00 AM"
        self.end_time = "4:00 AM"  # next day
        self.hours_list = self.generate_hours_list()

        # Calculate proportions based on tasks
        # Each row corresponds to an hour; if hour is even => show label, if odd => show '-'
        # Count how many tasks overlap each hour to determine row proportion
        row_proportions, hour_tasks_map = self.calculate_proportions()

        self.timeBlocksWidget = ProportionalGrid(len(self.hours_list))
        self.timeBlocksWidget.set_proportions(row_proportions)

        # Populate the grid
        for i, hour in enumerate(self.hours_list):
            if i == 0:
                # First hour line (e.g. 4 AM)
                timescale_label = QLabel(self.format_time_label(hour))
            else:
                # Even hour lines (full hour) show time; Odd hour lines (intermediate) show '-'
                # Determine if current hour is even or odd compared to the start hour
                base_dt = datetime.strptime("4:00 AM", "%I:%M %p")
                current_dt = datetime.strptime(hour, "%I:%M %p")
                delta_hours = int((current_dt - base_dt).total_seconds() // 3600)
                if delta_hours % 2 == 0:
                    # Even hour offset => show time
                    timescale_label = QLabel(self.format_time_label(hour))
                else:
                    # Odd hour offset => show '-'
                    timescale_label = QLabel("-")

            timescale_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            timescale_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.timeBlocksWidget.add_widget_to_row(i, timescale_label, column_index=0)

            # Tasks side: Create a QListWidget to hold tasks
            tasks_list_widget = QListWidget()
            tasks_list_widget.setStyleSheet("background-color: rgba(224,247,250,0.2); border: 1px solid #ccc;")
            tasks_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # Add tasks that overlap this hour line
            for task_name in hour_tasks_map[i]:
                tasks_list_widget.addItem(task_name)

            self.timeBlocksWidget.add_widget_to_row(i, tasks_list_widget, column_index=1)

        self.timeAndTasksLayout.addWidget(self.timeBlocksWidget)
        scroll_area.setWidget(self.container)

        self.mainLayout.addWidget(scroll_area)
        self.setLayout(self.mainLayout)

    def generate_hours_list(self):
        # From 4 AM to next day 4 AM = 24 hours
        # We'll generate a list of times every hour from 4 to 28 (since 4 AM +24 hours= next day 4 AM)
        hours_list = []
        base_time = datetime.strptime("4:00 AM", "%I:%M %p")
        for h in range(24):
            current_time = base_time + timedelta(hours=h)
            hours_list.append(current_time.strftime("%I:00 %p"))
        return hours_list

    def calculate_proportions(self):
        # Determine how many tasks overlap each hour
        # Convert tasks and hours to minutes from 4 AM, count how many tasks each hour intersects
        def time_to_minutes(t_str):
            base_time = datetime.strptime("4:00 AM", "%I:%M %p")
            current_time = datetime.strptime(t_str, "%I:%M %p")
            if current_time < base_time:
                current_time += timedelta(days=1)
            return int((current_time - base_time).total_seconds() // 60)

        hour_tasks_map = {i: [] for i in range(len(self.hours_list))}
        # Each hour line represents the starting of that hour to the next hour
        # For i-th hour, interval = [i, i+1) hours from 4 AM in hours
        # in minutes: [i*60, (i+1)*60)
        for i, hour_str in enumerate(self.hours_list):
            hour_start_min = time_to_minutes(hour_str)
            hour_end_min = hour_start_min + 60

            # Check tasks for overlap
            for t_start, t_end, t_name in self.time_blocks:
                start_min = time_to_minutes(t_start)
                end_min = time_to_minutes(t_end)
                # Overlap if intervals intersect
                if not (end_min <= hour_start_min or start_min >= hour_end_min):
                    hour_tasks_map[i].append(t_name)

        # Proportion = 1 + number_of_tasks for that hour
        proportions = [1 + len(hour_tasks_map[i]) for i in range(len(self.hours_list))]

        return proportions, hour_tasks_map

    def format_time_label(self, time_str):
        # Convert "HH:00 AM/PM" into a cleaner format like "4 AM", "10 AM"
        dt = datetime.strptime(time_str, "%I:00 %p")
        hour = dt.hour
        am_pm = "AM" if hour < 12 else "PM"
        display_hour = hour if 1 <= hour <= 12 else (hour-12 if hour > 12 else 12)
        return f"{display_hour} {am_pm}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScheduleViewWidget()
    window.setWindowTitle("Time Schedule")
    window.show()
    sys.exit(app.exec())
