from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


class CustomListItem(QWidget):
    def __init__(self, text):
        super().__init__()
        layout = QHBoxLayout(self)

        self.label = QLabel(text)
        self.button = QPushButton("Remove")
        self.button.clicked.connect(self.remove_item)

        layout.addWidget(self.label)
        layout.addWidget(self.button)

    def remove_item(self):
        list_widget = self.parent().parent()
        item = list_widget.itemAt(self.pos())
        if item:
            list_widget.takeItem(list_widget.row(item))


class SuggestionPanelProt(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)

        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("QToolBar { border: none; }")

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        add_action = QAction("Configure", self)
        add_action.triggered.connect(self.configure_weights)

        self.toolbar.addWidget(spacer)  # Pushes buttons to the right
        self.toolbar.addAction(add_action)

        self.list_widget = QListWidget()

        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.list_widget)

    def configure_weights(self):
        print("configure bruh")


if __name__ == "__main__":
    app = QApplication([])
    window = SuggestionPanelProt()
    window.show()
    app.exec()
