import sys
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


class Task(QListWidgetItem):
    def __init__(self, task_list, task_name='Task'):
        super().__init__()
        self.task_list = task_list  # Store the reference to the QListWidget

        self.widget = QWidget()
        self.layout = QHBoxLayout()
        self.checkbox = QCheckBox(task_name)
        self.checkbox.setChecked(False)
        self.checkbox.stateChanged.connect(self.task_checked)
        self.layout.addWidget(self.checkbox)

        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_task)
        self.layout.addWidget(self.delete_button)

        self.widget.setLayout(self.layout)
        self.setSizeHint(self.widget.sizeHint())

    def task_checked(self, state):
        pass

    def delete_task(self):
        row = self.task_list.row(self)
        self.task_list.takeItem(row)


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
        self.task_list_collection.setDragEnabled(True)
        self.task_list_collection.setAcceptDrops(True)
        self.task_list_collection.setDropIndicatorShown(True)
        self.task_list_collection.setDragDropMode(QListWidget.DragDropMode.InternalMove)

        # Mapping of hash values to stack widget pages
        self.hash_to_widget = {}
        self.task_list_collection.currentItemChanged.connect(self.switch_stack_widget_by_hash)

        self.left_layout.addWidget(self.task_list_collection)
        self.task_list_collection.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list_collection.customContextMenuRequested.connect(self.task_list_collection_context_menu)

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
        add_task_button.clicked.connect(self.add_task_list)

    def add_task_list(self):
        try:
            task_list_name, ok = QInputDialog.getText(self, "New Task List", "Enter name:")
            if not ok or not task_list_name.strip():
                return
            self.task_list_collection.addItem(task_list_name)
            task_list = QListWidget()
            self.stack_widget.addWidget(task_list)
            self.hash_to_widget[hash(task_list_name)] = task_list
        except Exception as e:
            print(f"An error occurred while adding a task list: {e}")

    def switch_stack_widget_by_hash(self, current, previous):
        try:
            if current:
                hash_key = hash(current.text())
                if hash_key in self.hash_to_widget:
                    self.stack_widget.setCurrentWidget(self.hash_to_widget[hash_key])
        except Exception as e:
            print(f"An error occurred while switching stack: {e}")

    def add_task(self):
        current_task_list = self.stack_widget.currentWidget()
        if not isinstance(current_task_list, QListWidget):
            return

        try:
            task = Task(current_task_list, "New Task")
            current_task_list.addItem(task)
            current_task_list.setItemWidget(task, task.widget)
        except Exception as e:
            print(f"An error occurred while adding a task: {e}")

    def task_list_collection_context_menu(self, position):
        try:
            task_list = self.task_list_collection.itemAt(position)
            if not task_list:
                return

            # Create the context menu
            menu = QMenu()
            edit_action = QAction('Edit', self)
            delete_action = QAction('Delete', self)

            # Connect actions to methods
            edit_action.triggered.connect(lambda: self.edit_task_list(task_list))
            delete_action.triggered.connect(lambda: self.delete_task_list(task_list))

            # Add actions to the menu
            menu.addAction(edit_action)
            menu.addAction(delete_action)

            # Show the context menu at the current mouse position
            menu.exec(self.task_list_collection.viewport().mapToGlobal(position))
        except Exception as e:
            print(f"An error occurred in task_list_collection_context_menu: {e}")

    def edit_task_list(self, task_list):
        print(f"Editing item: {task_list.text()}")

    def delete_task_list(self, task_list):
        try:
            row = self.task_list_collection.row(task_list)
            hash_key = hash(task_list.text())
            # Remove the corresponding widget from the stack
            if hash_key in self.hash_to_widget:
                widget_to_remove = self.hash_to_widget.pop(hash_key)
                self.stack_widget.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()
            self.task_list_collection.takeItem(row)
        except Exception as e:
            print(f"An error occurred while deleting a task list: {e}")
