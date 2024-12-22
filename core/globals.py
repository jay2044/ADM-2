DUE_TODAY_COLOR = "#4fa7f2"
DUE_TOMORROW_COLOR = "#648742"
PAST_DUE_COLOR = "#ec4f4f"
DUE_THIS_WEEK_COLOR = "orange"
DEFAULT_COLOR = "white"

from PyQt6.QtWidgets import QApplication, QMainWindow


def get_main_window():
    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, QMainWindow):
            return widget
    return None
