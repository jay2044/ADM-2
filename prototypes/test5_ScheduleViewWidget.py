from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys


class HourCell(QWidget):
    """Custom widget for hour cells."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(label)


class HourScaleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hours = [
            f"{hour % 12 or 12} {'AM' if hour % 24 < 12 else 'PM'}"
            for hour in range(4, 28)
        ]
        print(self.hours)
        self.custom_heights = {i: 20 for i in range(len(self.hours))}

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.populate_cells()
        self.start_auto_update()

    def populate_cells(self):
        """Populate the widget with hour widgets."""
        for i, hour in enumerate(self.hours):
            cell_text = hour if i % 2 == 0 else "-"
            cell_widget = HourCell(cell_text, self)
            cell_widget.setFixedHeight(self.custom_heights.get(i, 20))
            self.layout.addWidget(cell_widget)

    def set_height(self, start_index, end_index, height):
        """Set the height of a specific range of intervals based on pixels."""
        height = int(height / (max(start_index, end_index) - min(start_index, end_index)))
        for index in range(start_index, end_index + 1):
            if 0 <= index < len(self.hours):
                self.custom_heights[index] = height
                self.layout.itemAt(index).widget().setFixedHeight(height)

    def set_height_by_widget(self, start_hour, end_hour, widget):
        """Set the height of intervals to match the height of another widget."""
        hours = self.hours
        start_index = hours.index(start_hour)
        end_index = hours.index(end_hour)
        widget_height = widget.height()
        self.set_height(start_index, end_index, widget_height)

    def highlight_current_hour(self):
        current_time = QTime.currentTime()
        current_hour = current_time.hour()
        start_hour = 4
        hour_index = current_hour - start_hour if current_hour >= start_hour else (current_hour + 24 - start_hour)

        for i in range(len(self.hours)):
            widget = self.layout.itemAt(i).widget()
            if i < hour_index:
                widget.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
            elif i == hour_index:
                widget.setStyleSheet("background-color: rgba(3, 204, 163, 128); font-weight: bold;")

    def start_auto_update(self):
        timer = QTimer(self)
        timer.timeout.connect(self.highlight_current_hour)
        timer.start(3600000)
        self.highlight_current_hour()


class TimeBlockWidget(QWidget):
    def __init__(self, start_time, end_time, color=None, name="", parent=None, empty=False, unavailable=False):
        super().__init__(parent)

        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.color = color
        self.tasks = []

        self.schedule_manager = parent.schedule_manager if parent and hasattr(parent, 'schedule_manager') else None
        if self.schedule_manager:
            self.tasks = self.schedule_manager.get_tasks(self.name)

        start_hour = int(self.start_time.split(':')[0])
        end_hour = int(self.end_time.split(':')[0])
        # to check if the end hour is nex day
        if end_hour < start_hour:
            end_hour += 24
        self.base_height = max(45 * (end_hour - start_hour), 45)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.frame.setFixedHeight(self.base_height)

        if not empty and not unavailable:
            self.init_ui_time_block_with_tasks()
        elif empty:
            self.init_ui_empty()
        elif unavailable:
            self.init_ui_unavailable()

        if self.tasks:
            self.load_tasks()

    def setup_frame(self, name, color):
        self.name = name
        color_rgba = QColor(color[0], color[1], color[2], 128)
        palette = self.frame.palette()
        palette.setColor(QPalette.ColorRole.Window, color_rgba)
        self.frame.setAutoFillBackground(True)
        self.frame.setPalette(palette)

        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(5, 5, 5, 5)

        self.name_label = QLabel(self.name, self.frame)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.frame_layout.addWidget(self.name_label)

        self.layout.addWidget(self.frame)

    def init_ui_time_block_with_tasks(self):
        self.setup_frame(self.name, self.color)
        self.task_list = QListWidget(self.frame)
        self.task_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frame_layout.addWidget(self.task_list)

    def init_ui_empty(self):
        self.setup_frame("No tasks", (47, 47, 47))

    def init_ui_unavailable(self):
        self.setup_frame("Unavailable", (231, 131, 97))

    def load_tasks(self):
        for task in self.tasks:
            self.add_task(task)

    def add_task(self, task):
        # TODO: make it init and add TaskWidgets
        self.task_list.addItem(task)
        task_height = self.task_list.sizeHintForRow(0)
        if (self.base_height - self.name_label.height()) / task_height < self.task_list.count():
            self.base_height += task_height
            self.frame.setFixedHeight(self.base_height)


class ScheduleViewWidget(QWidget):
    def __init__(self, schedule_manger=None):
        super().__init__()
        self.schedule_manger = schedule_manger
        self.time_blocks = self.schedule_manger.get_time_blocks() if self.schedule_manger else []
        self.initUI()
        self.load_time_blocks()

    def initUI(self):
        self.setFixedWidth(300)
        self.mainLayout = QVBoxLayout(self)

        topLayout = QHBoxLayout()
        self.expandBtn = QPushButton("Expand")
        self.quickTaskBtn = QPushButton("Add Quick Task")
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        topLayout.addWidget(self.expandBtn)
        topLayout.addItem(spacer)
        topLayout.addWidget(self.quickTaskBtn)
        self.mainLayout.addLayout(topLayout)

        viewSelectorLayout = QHBoxLayout()
        self.prevBtn = QPushButton("<")
        self.viewLabel = QLabel("Day")
        self.nextBtn = QPushButton(">")
        viewSelectorLayout.addWidget(self.prevBtn)
        viewSelectorLayout.addWidget(self.viewLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        viewSelectorLayout.addWidget(self.nextBtn)
        self.mainLayout.addLayout(viewSelectorLayout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.container = QWidget()
        self.timeAndTasksLayout = QHBoxLayout(self.container)
        self.timeAndTasksLayout.setContentsMargins(0, 0, 0, 0)
        self.timeAndTasksLayout.setSpacing(0)

        self.timeScaleWidget = HourScaleWidget()
        self.timeBlocksLayout = QVBoxLayout()
        self.timeBlocksLayout.setContentsMargins(0, 0, 0, 0)
        self.timeBlocksLayout.setSpacing(0)

        self.timeAndTasksLayout.addWidget(self.timeScaleWidget)
        self.timeAndTasksLayout.addLayout(self.timeBlocksLayout)
        scroll_area.setWidget(self.container)

        self.mainLayout.addWidget(scroll_area)
        self.setLayout(self.mainLayout)

    def load_time_blocks(self):
        for block in self.time_blocks:
            # block is like [start_time, end_time, color, name, empty, unavailable]
            start_time, end_time, color, name, empty, unavailable = block

            if empty:
                tb = TimeBlockWidget(start_time, end_time, color, name="No tasks", parent=self, empty=True)
            elif unavailable:
                tb = TimeBlockWidget(start_time, end_time, color, name="Unavailable", parent=self, unavailable=True)
            else:
                tb = TimeBlockWidget(start_time, end_time, color, name=name, parent=self)

            self.add_time_block(tb)

        QTimer.singleShot(0, self.print_time_block_heights)

    def print_time_block_heights(self):
        self.updateGeometry()
        QApplication.processEvents()
        for i in range(self.timeBlocksLayout.count()):
            tb_widget = self.timeBlocksLayout.itemAt(i).widget()
            if tb_widget:
                start_hour = int(tb_widget.start_time.split(':')[0])
                end_hour = int(tb_widget.end_time.split(':')[0])

                self.timeScaleWidget.set_height_by_widget(
                    f"{start_hour - 12 if start_hour > 12 else start_hour} {"AM" if start_hour < 12 else "PM"}",
                    f"{end_hour - 12 if end_hour > 12 else end_hour} {"AM" if end_hour < 12 else "PM"}", tb_widget)

    def add_time_block(self, time_block_widget):
        self.timeBlocksLayout.addWidget(time_block_widget)


if __name__ == "__main__":
    class MockScheduleManager:
        def get_time_blocks(self):
            # Example data: [start_time, end_time, name]
            return [
                ["04:00", "8:00", None, "", True, False],  # Empty block
                ["08:00", "09:00", (255, 200, 100), "Morning Workout", False, False],
                ["09:00", "13:00", None, "", True, False],  # Empty block
                ["13:00", "17:00", (200, 200, 255), "Project Work", False, False],
                ["17:00", "18:00", None, "Unavailable", False, True],  # Unavailable block
                ["18:00", "19:00", None, "", True, False],  # Empty block
                ["19:00", "20:00", (255, 255, 150), "Dinner", False, False],
                ["20:00", "3:00", None, "", True, False]  # Empty block
            ]

        def get_tasks(self, name):
            if name == "Project Work":
                return ["Task A", "Task B", "Task C"]
            elif name == "Development":
                return ["Dev Task 1", "Dev Task 2"]
            return []


    app = QApplication(sys.argv)
    manager = MockScheduleManager()
    window = ScheduleViewWidget(manager)
    window.setWindowTitle("Time Schedule")
    window.show()
    window.print_time_block_heights()
    sys.exit(app.exec())
