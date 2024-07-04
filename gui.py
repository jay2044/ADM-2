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
        self.settings = QSettings("MyCompany", "ADM")
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
        self.right_dock = TaskListDockStacked(self)

        right_dock_geometry = json.loads(self.settings.value("rightDockGeometry", "{}"))
        dock_area = area_map.get(right_dock_geometry["area"])
        self.addDockWidget(dock_area, self.right_dock)

        # size = [int(x) for x in right_dock_geometry.get("size").split(",")]
        # self.right_dock.resize()

        self.task_list_collection.load_task_lists()

    def setup_history_dock(self):
        self.history_dock = HistoryDock(self)
        history_dock_geometry = json.loads(self.settings.value("historyDockGeometry", "{}"))
        dock_area = area_map.get(history_dock_geometry["area"])
        self.addDockWidget(dock_area, self.history_dock)

    def setup_calendar_dock(self):
        self.calendar_dock = QDockWidget("Calendar")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.calendar_dock)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("historyVisible", self.history_dock.isVisible())
        self.settings.setValue("calendarVisible", self.calendar_dock.isVisible())

        self.settings.setValue("rightDockGeometry", json.dumps(self.saveDockWidgetGeometry(self.right_dock)))
        self.settings.setValue("historyDockGeometry", json.dumps(self.saveDockWidgetGeometry(self.history_dock)))

    def load_settings(self):
        self.restoreGeometry(self.settings.value("geometry", QByteArray()))
        self.restoreState(self.settings.value("windowState", QByteArray()))
        if self.settings.value("historyVisible", False, type=bool):
            self.history_dock.setVisible(True)
        else:
            self.history_dock.setVisible(False)
        if self.settings.value("calendarVisible", False, type=bool):
            self.calendar_dock.setVisible(True)
        else:
            self.calendar_dock.setVisible(False)

        right_dock_geometry = json.loads(self.settings.value("rightDockGeometry", "{}"))
        history_dock_geometry = json.loads(self.settings.value("historyDockGeometry", "{}"))

        self.restoreDockWidgetGeometry(self.right_dock, right_dock_geometry)
        self.restoreDockWidgetGeometry(self.history_dock, history_dock_geometry)

    def restoreDockWidgetGeometry(self, dock_widget, geometry):
        if not geometry or not isinstance(geometry, dict):
            return

        pos = [int(x) for x in geometry.get("pos", "0,0").split(",")]
        size = [int(x) for x in geometry.get("size", "100,100").split(",")]
        floating = geometry.get("floating", "false").lower() == "true"

        dock_widget.resize(QSize(size[0], size[1]))
        dock_widget.move(QPoint(pos[0], pos[1]))
        dock_widget.setFloating(floating)

    def saveDockWidgetGeometry(self, dock_widget):
        return {
            "pos": f"{dock_widget.pos().x()},{dock_widget.pos().y()}",
            "size": f"{dock_widget.size().width()},{dock_widget.size().height()}",
            "floating": str(dock_widget.isFloating()),
            "area": str(self.dockWidgetArea(dock_widget))
        }

    def toggle_history(self):
        self.history_dock.toggle_history()

    def toggle_calendar(self):
        self.calendar_dock.setVisible(not self.calendar_dock.isVisible())
