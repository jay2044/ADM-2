from PyQt6.QtWidgets import QApplication
import sys
from ui.gui import MainWindow


def main():
    app = QApplication(sys.argv)
    with open('themes/styles.qss', 'r') as f:
        app.setStyleSheet(f.read())
    main_window = MainWindow(app)
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
