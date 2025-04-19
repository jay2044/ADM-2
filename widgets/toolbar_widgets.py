from PyQt6.QtWidgets import *
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


class TaskListManagerToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_action("+", parent.parent, parent.task_list_collection.add_task_list)
        self.add_action("T", parent.parent, parent.parent.toggle_stacked_task_list)
        self.add_action("H", parent.parent, parent.parent.toggle_history)
        self.add_action("C", parent.parent, parent.parent.toggle_calendar)
        self.setObjectName("taskListManagerToolbar")

    def add_action(self, text, parent, function):
        action = QAction(text, parent)
        action.triggered.connect(function)
        self.addAction(action)


class InfoBar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.task_manager = parent.task_manager
        self.task_list_count_label = QLabel()
        self.update_task_list_count_label()
        self.task_list_count_label.setStyleSheet("font-size: 12px;")
        self.task_list_count_label.setFixedHeight(9)

        # Layout to add the label to the InfoBar
        layout = QHBoxLayout()
        layout.addWidget(self.task_list_count_label)
        layout.addStretch()
        self.setLayout(layout)

    def update_task_list_count_label(self):
        task_count = len(self.task_manager.task_lists)
        self.task_list_count_label.setText(f"  {task_count}")


class TaskListToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_action("+", parent, parent.add_task)
        self.add_action("Q", parent, parent.set_queue)
        self.add_action("S", parent, parent.set_stack)
        self.add_action("P", parent, parent.priority_sort)
        self.add_action("D", parent, parent.set_due)
        self.add_action("E", parent, parent.set_time_estimate)
        self.add_action("MS", parent, parent.toggle_multi_select)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def add_action(self, text, parent, function):
        action = QAction(text, parent)
        action.triggered.connect(function)
        self.addAction(action)
