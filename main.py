from PyQt6.QtWidgets import QApplication
import sys
from gui import MainWindow
from task_manager import TaskList
import os


def main():
    app = QApplication(sys.argv)
    with open('styles.qss', 'r') as f:
        app.setStyleSheet(f.read())
    main_window = MainWindow(app)
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
