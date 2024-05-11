import sys
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Uncomment if frameless is desired
        self.setWindowTitle('ADM')
        self.setGeometry(100, 100, 1000, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Setting up left widget for collection of task lists
        self.task_list_collection = QListWidget()
        self.left_layout = QVBoxLayout()
        self.task_list_collection.setLayout(self.left_layout)
        self.main_layout.addWidget(self.task_list_collection, stretch=1)

        # Setting up right widget for displaying tasks
        self.task_list = QListWidget()
        self.right_layout = QVBoxLayout()
        self.task_list.setLayout(self.right_layout)
        self.main_layout.addWidget(self.task_list, stretch=3)

        self.add_task_button = QPushButton('Add Task')
        self.right_layout.addWidget(self.add_task_button, alignment=Qt.AlignmentFlag.AlignBottom)
        self.add_task_button.clicked.connect(self.add_task)

    def add_task(self):
        try:
            task = QListWidgetItem()
            task.setText("task_item")
            self.task_list.addItem(task)
        except Exception as e:
            print(f"An error occurred while adding a task: {e}")
