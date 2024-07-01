import sys
import os

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from task_manager import *

from control import *
from widgets import *


def setup_font(app):
    # font_id = QFontDatabase.addApplicationFont("fonts/entsans.ttf")
    # font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    # font = QFont(font_family, 12)
    font = QFont()
    font.setPointSize(12)
    app.setFont(font)


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.task_manager = TaskListManager()
        self.setup_ui(app)
        self.load_settings()

    def setup_ui(self, app):
        setup_font(app)
        self.setup_main_window()
        self.setup_layouts()
        self.setup_left_widgets()
        self.setup_right_widgets()

    def setup_main_window(self):
        self.setWindowTitle('ADM')
        screen_geometry = QApplication.primaryScreen().geometry()
        center_point = screen_geometry.center()
        window_width, window_height = 700, 600
        self.resize(window_width, window_height)
        top_left_point = center_point - QPoint(window_width // 2, window_height // 2)
        self.move(top_left_point)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

    def setup_layouts(self):
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)
        self.main_layout.addWidget(self.left_widget)

    def setup_left_widgets(self):
        self.hash_to_widget = {}
        self.task_list_collection = TaskListCollection(self)
        self.left_top_toolbar = TaskListManagerToolbar(self)
        self.left_layout.addWidget(self.left_top_toolbar)
        self.left_layout.addWidget(self.task_list_collection)
        self.info_bar = InfoBar(self)
        self.left_layout.addWidget(self.info_bar)

    def setup_right_widgets(self):
        self.right_dock = TaskListDockStacked(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)
        self.history_widget = self.create_history_widget()
        self.calendar_widget = self.create_calendar_widget()
        self.task_list_collection.load_task_lists()

    def create_history_widget(self):
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_label = QLabel("History", self)
        self.history_list = QListWidget(self)
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.history_list)
        history_widget.hide()
        return history_widget

    def create_calendar_widget(self):
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(calendar_widget)
        calendar_label = QLabel("Calendar", self)
        calendar_layout.addWidget(calendar_label)
        calendar_widget.hide()
        return calendar_widget

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        settings = QSettings("MyCompany", "ADM")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def load_settings(self):
        settings = QSettings("MyCompany", "ADM")
        self.restoreGeometry(settings.value("geometry", QByteArray()))
        self.restoreState(settings.value("windowState", QByteArray()))

    def toggle_history(self):
        self.history_widget.setVisible(not self.history_widget.isVisible())
        if self.history_widget.isVisible():
            self.update_history()

    def update_history(self):
        self.history_list.clear()
        for task_list_info in self.task_manager.get_task_lists():
            task_list = TaskList(task_list_info["list_name"], self.task_manager, task_list_info["pin"],
                                 task_list_info["queue"], task_list_info["stack"])
            for task in task_list.get_completed_tasks():
                self.history_list.addItem(f"{task.title} (Completed on {task.due_date})")

    def toggle_calendar(self):
        self.calendar_widget.setVisible(not self.calendar_widget.isVisible())
