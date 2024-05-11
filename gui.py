import sys
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        font_id = QFontDatabase.addApplicationFont("fonts/entsans.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        # font = QFont(font_family)
        font = QFont()
        font.setPointSize(12)
        app.setFont(font)

        self.setWindowTitle('ADM')
        screen_geometry = QApplication.primaryScreen().geometry()
        center_point = screen_geometry.center()
        window_width, window_height = 800, 600
        self.resize(window_width, window_height)
        top_left_point = center_point - QPoint(window_width // 2, window_height // 2)
        self.move(top_left_point)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # left layout containing widgets related to handling tabs of task lists.
        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout, stretch=1)

        # widget for collection of task lists
        self.task_list_collection = QListWidget()
        self.left_layout.addWidget(self.task_list_collection)

        # right layout containing widgets related to handling tasks
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_layout, stretch=4)

        # Stack to switch between different task list tabs
        self.stack_widget = QStackedWidget()
        self.right_layout.addWidget(self.stack_widget)

        # add task button
        add_task_button = QPushButton('Add Task')
        self.right_layout.addWidget(add_task_button, alignment=Qt.AlignmentFlag.AlignBottom)
        add_task_button.clicked.connect(self.add_task)

        # Button to create a new task list
        add_task_button = QPushButton('Add Task List')
        self.left_layout.addWidget(add_task_button, alignment=Qt.AlignmentFlag.AlignBottom)
        add_task_button.clicked.connect(self.add_tab)

        # Connect the current row change to switching the stack index
        self.task_list_collection.currentRowChanged.connect(self.stack_widget.setCurrentIndex)

    def add_tab(self):
        tab_name = f"Tab {self.task_list_collection.count() + 1}"
        self.task_list_collection.addItem(tab_name)
        task_list = QListWidget()
        self.stack_widget.addWidget(task_list)

    def add_task(self):
        # Determine the current QListWidget in the stack
        current_task_list = self.stack_widget.currentWidget()

        try:
            task = QListWidgetItem()
            task.setSizeHint(QSize(100, 40))
            checkbox = QCheckBox('Task')
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.task_checked)
            current_task_list.addItem(task)
            current_task_list.setItemWidget(task, checkbox)
        except Exception as e:
            print(f"An error occurred while adding a task: {e}")

    def task_checked(self, state):
        pass
