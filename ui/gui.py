from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QFont
from widgets.dock_widgets import *
from core.task_manager import *
from core.signals import global_signals

area_map = {
    "DockWidgetArea.LeftDockWidgetArea": Qt.DockWidgetArea.LeftDockWidgetArea,
    "DockWidgetArea.RightDockWidgetArea": Qt.DockWidgetArea.RightDockWidgetArea,
    "DockWidgetArea.TopDockWidgetArea": Qt.DockWidgetArea.TopDockWidgetArea,
    "DockWidgetArea.BottomDockWidgetArea": Qt.DockWidgetArea.BottomDockWidgetArea,
}

# Global Settings Keys
APP_NAME = "ADM"
ORG_NAME = "x"
SETTINGS_MAIN_WINDOW_STATE = "mainWindowState"
SETTINGS_OPEN_DOCK_WIDGETS = "openDockWidgets"

DEFAULT_DOCK_AREA = Qt.DockWidgetArea.RightDockWidgetArea


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
        self.task_lists = {}
        self.hash_to_widget = {}
        self.settings = QSettings("x", "ADM")
        self.setup_ui(app)
        self.options()
        self.load_settings()
        self.setAcceptDrops(True)
        self.setup_signals()
        # self.reset_settings()

    def reset_settings(self):
        confirm = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to default? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            # Clear the settings
            self.settings.clear()

            # Reset UI components to their default state
            self.restoreState(QByteArray())  # Clear window state
            self.task_lists.clear()
            self.hash_to_widget.clear()

            # Close all dock widgets
            for dock_widget in self.findChildren(QDockWidget):
                dock_widget.close()

            # Notify the user and prompt for restart
            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been reset. Please restart the application for changes to take effect."
            )

    def setup_signals(self):
        global_signals.task_list_updated.connect(self.handle_task_list_update)

    def setup_ui(self, app):
        setup_font(app)

        self.stacked_task_list = TaskListDockStacked(self)
        self.setup_main_window()
        self.setup_right_widgets()
        self.setup_history_dock()
        self.setup_calendar_dock()
        self.stacked_task_list.update_toolbar()

        self.navigation_sidebar_dock.task_list_collection.search_bar.textChanged.connect(
            self.stacked_task_list.filter_current_task_list)

    def setup_main_window(self):
        self.setWindowTitle('ADM')
        screen_geometry = QApplication.primaryScreen().geometry()
        center_point = screen_geometry.center()
        window_width, window_height = 700, 600
        self.resize(window_width, window_height)
        top_left_point = center_point - QPoint(window_width // 2, window_height // 2)
        self.move(top_left_point)

        # Create central dock widget
        self.navigation_sidebar_dock = NavigationSidebarDock(self)
        self.navigation_sidebar_dock.setObjectName("NavigationSidebarDock")

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.navigation_sidebar_dock)
        self.navigation_sidebar_dock.setFixedWidth(200)

    def options(self):
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks |
                            QMainWindow.DockOption.AllowNestedDocks |
                            QMainWindow.DockOption.AnimatedDocks)

    def setup_right_widgets(self):
        self.stacked_task_list.setObjectName("stackedTaskListDock")
        self.stacked_task_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.stacked_task_list)
        self.splitDockWidget(self.navigation_sidebar_dock, self.stacked_task_list, Qt.Orientation.Horizontal)

    def setup_history_dock(self):
        self.history_dock = HistoryDock(self)
        self.history_dock.setObjectName("historyDock")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.history_dock)
        self.history_dock.hide()

    def setup_calendar_dock(self):
        self.calendar_dock = CalendarDock(self)
        self.calendar_dock.setObjectName("calendarDock")
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.calendar_dock)
        self.calendar_dock.hide()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        settings = QSettings(ORG_NAME, APP_NAME)
        settings.setValue(SETTINGS_MAIN_WINDOW_STATE, self.saveState())

        open_dock_widgets = []
        for dock in self.findChildren(TaskListDock):
            if dock.isVisible():
                dock_info = {
                    'objectName': dock.objectName(),
                    'task_list_name': dock.task_list_name
                }
                open_dock_widgets.append(dock_info)
        settings.setValue(SETTINGS_OPEN_DOCK_WIDGETS, json.dumps(open_dock_widgets))

    def load_settings(self):
        try:
            settings = QSettings(ORG_NAME, APP_NAME)

            open_dock_widgets = json.loads(settings.value(SETTINGS_OPEN_DOCK_WIDGETS, "[]"))
            for dock_info in open_dock_widgets:
                dock = TaskListDock(dock_info['task_list_name'], self)
                dock.setObjectName(dock_info['objectName'])
                dock.setWindowTitle(dock_info['task_list_name'])
                self.addDockWidget(DEFAULT_DOCK_AREA, dock)

            self.restoreState(settings.value(SETTINGS_MAIN_WINDOW_STATE))
        except Exception as e:
            print(e)

    def toggle_stacked_task_list(self):
        self.stacked_task_list.setVisible(not self.stacked_task_list.isVisible())

    def toggle_history(self):
        self.history_dock.toggle_history()

    def toggle_calendar(self):
        self.calendar_dock.setVisible(not self.calendar_dock.isVisible())

    def add_task_detail_dock(self, task, task_list_widget):
        for dock in self.findChildren(TaskDetailDock):
            if dock.task == task:
                dock.raise_()
                dock.activateWindow()
                return

        unique_id = random.randint(1000, 9999)
        task_detail_dock = TaskDetailDock(task, task_list_widget, parent=self)
        task_detail_dock.setObjectName(f"TaskListDock_{task.title}_{unique_id}")
        task_detail_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        existing_docks = [
            d for d in self.findChildren(QDockWidget)
            if self.dockWidgetArea(d) == Qt.DockWidgetArea.RightDockWidgetArea
        ]

        if existing_docks:
            self.tabifyDockWidget(existing_docks[-1], task_detail_dock)
        else:
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, task_detail_dock)

        QApplication.processEvents()

        task_detail_dock.raise_()
        task_detail_dock.activateWindow()

    def clear_settings(self):
        self.settings.clear()
        QMessageBox.information(self, "Settings Cleared",
                                "All settings have been cleared. Please restart the application.")

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    # def dropEvent(self, event):
    #     try:
    #         if event.source() == self.task_list_collection.tree_widget:
    #             task_list_item = self.task_list_collection.tree_widget.currentItem()
    #             if task_list_item and task_list_item.parent():
    #                 task_list_name = task_list_item.text(0)
    #
    #                 unique_id = random.randint(1000, 9999)
    #                 dock = TaskListDock(task_list_name, self)
    #                 dock.setObjectName(f"TaskListDock_{task_list_name}_{unique_id}")
    #
    #                 drop_pos = event.position().toPoint()
    #
    #                 if drop_pos.x() < self.width() // 3:
    #                     area = Qt.DockWidgetArea.LeftDockWidgetArea
    #                 elif drop_pos.x() > (2 * self.width()) // 3:
    #                     area = Qt.DockWidgetArea.RightDockWidgetArea
    #                 elif drop_pos.y() < self.height() // 3:
    #                     area = Qt.DockWidgetArea.TopDockWidgetArea
    #                 else:
    #                     area = Qt.DockWidgetArea.BottomDockWidgetArea
    #
    #                 self.addDockWidget(area, dock)
    #                 dock.show()
    #                 event.accept()
    #             else:
    #                 event.ignore()
    #         else:
    #             event.ignore()
    #     except Exception as e:
    #         print(f"Error in dropEvent: {e}")

    def handle_task_list_update(self):
        for task_list in self.task_lists.values():
            task_list.refresh_tasks()

        for dock_widget in self.findChildren(TaskListDock):
            dock_widget.task_list_widget.load_tasks()

        current_widget = self.stacked_task_list.get_current_task_list_widget()
        if current_widget:
            current_widget.load_tasks()

        self.history_dock.update_history()
        self.calendar_dock.update_calendar()

        print("Task list has been updated globally")