import sys
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ADM')
        self.setGeometry(100, 100, 1000, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Create left layout (a vertical box layout)
        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout, stretch=1)

        # Setting up left widget for collection of task lists
        self.task_list_collection = QListWidget()
        self.left_layout.addWidget(self.task_list_collection)

        # Setting up right widget for displaying tasks
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_layout, stretch=3)

        self.stack_widget = QStackedWidget()
        self.right_layout.addWidget(self.stack_widget)

        # Create the add task button and connect to add_task function
        add_task_button = QPushButton('Add Task')
        self.right_layout.addWidget(add_task_button, alignment=Qt.AlignmentFlag.AlignBottom)
        add_task_button.clicked.connect(self.add_task)

        add_task_button = QPushButton('Add Tab')
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
            task.setSizeHint(QSize(100, 50))
            checkbox = QCheckBox('Task')
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.task_checked)
            current_task_list.addItem(task)
            current_task_list.setItemWidget(task, checkbox)
        except Exception as e:
            print(f"An error occurred while adding a task: {e}")

    def task_checked(self, state):
        print(f"Task state changed to: {state}")
