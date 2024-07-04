import sys
import os
import json

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from task_manager import *

from control import *
from widgets import *

area_map = {
    "DockWidgetArea.LeftDockWidgetArea": Qt.DockWidgetArea.LeftDockWidgetArea,
    "DockWidgetArea.RightDockWidgetArea": Qt.DockWidgetArea.RightDockWidgetArea,
    "DockWidgetArea.TopDockWidgetArea": Qt.DockWidgetArea.TopDockWidgetArea,
    "DockWidgetArea.BottomDockWidgetArea": Qt.DockWidgetArea.BottomDockWidgetArea,
}


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
        self.settings = QSettings("123", "ADM")
        self.setup_ui(app)
        self.options()
        self.load_settings()

    def setup_ui(self, app):
        setup_font(app)
        self.setup_main_window()
        self.setup_layouts()
        self.setup_left_widgets()
        self.setup_right_widgets()
        self.setup_history_dock()
        self.setup_calendar_dock()

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

    def options(self):
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks |
                            QMainWindow.DockOption.AllowNestedDocks |
                            QMainWindow.DockOption.AnimatedDocks)

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
        self.stacked_task_list = TaskListDockStacked(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.stacked_task_list)

        self.task_list_collection.load_task_lists()

    def setup_history_dock(self):
        self.history_dock = HistoryDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.history_dock)

    def setup_calendar_dock(self):
        self.calendar_dock = QDockWidget("Calendar")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.calendar_dock)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("rightDockGeometry", json.dumps(self.saveDockWidgetGeometry(self.stacked_task_list)))
        self.settings.setValue("historyDockGeometry", json.dumps(self.saveDockWidgetGeometry(self.history_dock)))
        self.settings.setValue("calendarDockGeometry", json.dumps(self.saveDockWidgetGeometry(self.calendar_dock)))

    def load_settings(self):
        self.restoreGeometry(self.settings.value("geometry", QByteArray()))

        stacked_task_list_geometry = json.loads(self.settings.value("rightDockGeometry", "{}"))
        history_dock_geometry = json.loads(self.settings.value("historyDockGeometry", "{}"))
        calendar_dock_geometry = json.loads(self.settings.value("calendarDockGeometry", "{}"))

        self.restoreDockWidgetGeometry(self.stacked_task_list, stacked_task_list_geometry)
        self.restoreDockWidgetGeometry(self.history_dock, history_dock_geometry)
        self.restoreDockWidgetGeometry(self.calendar_dock, calendar_dock_geometry)

        self.restoreState(self.settings.value("windowState", QByteArray()))

    def restoreDockWidgetGeometry(self, dock_widget, geometry):
        if not geometry or not isinstance(geometry, dict):
            return

        floating = geometry.get("floating", "false").lower() == "true"
        dock_widget.setFloating(floating)

        if floating:
            pos = [int(x) for x in geometry.get("pos", "0,0").split(",")]
            size = [int(x) for x in geometry.get("size", "100,100").split(",")]
            dock_widget.resize(QSize(size[0], size[1]))
            dock_widget.move(QPoint(pos[0], pos[1]))

        area = area_map.get(geometry.get("area"), Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(area, dock_widget)

        dock_widget.setVisible(geometry.get("visible") == "True")

    def saveDockWidgetGeometry(self, dock_widget):
        return {
            "pos": f"{dock_widget.pos().x()},{dock_widget.pos().y()}",
            "size": f"{dock_widget.size().width()},{dock_widget.size().height()}",
            "floating": str(dock_widget.isFloating()),
            "area": str(self.dockWidgetArea(dock_widget)),
            "visible": str(dock_widget.isVisible())
        }

    def toggle_stacked_task_list(self):
        self.stacked_task_list.setVisible(not self.stacked_task_list.isVisible())

    def toggle_history(self):
        self.history_dock.toggle_history()

    def toggle_calendar(self):
        self.calendar_dock.setVisible(not self.calendar_dock.isVisible())

    def clear_settings(self):
        self.settings.clear()
        QMessageBox.information(self, "Settings Cleared",
                                "All settings have been cleared. Please restart the application.")
