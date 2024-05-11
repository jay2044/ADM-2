from PyQt6.QtWidgets import QApplication
import sys
from gui import MainWindow


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow(app)
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
