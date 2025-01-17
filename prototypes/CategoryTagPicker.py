# CategoryTagPicker.py

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt


class _ClickableItem(QWidget):
    def __init__(self, text):
        super().__init__()
        self._state = 0

        self.button = QPushButton(text)
        self.button.setCheckable(False)
        self.button.setFixedSize(100, 30)
        self.button.clicked.connect(self._handle_click)

        self.button.setStyleSheet("border: 1px solid black; border-radius: 10px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)
        layout.setContentsMargins(0, 0, 0, 0)

        self._update_style()

    def _handle_click(self):
        self._state = (self._state + 1) % 3
        self._update_style()

    def _update_style(self):
        if self._state == 0:
            self.button.setStyleSheet("border: 1px solid black; border-radius: 10px; background: none;")
        elif self._state == 1:
            self.button.setStyleSheet("border: 1px solid black; border-radius: 10px; background: rgb(105, 170, 110);")
        else:
            self.button.setStyleSheet("border: 1px solid black; border-radius: 10px; background: rgb(204, 97, 65);")

    def get_state(self):
        return self._state

    def text(self):
        return self.button.text()


class CategoryTagPicker(QWidget):
    def __init__(self, categories, tags, parent=None):
        super().__init__(parent)

        self.categories = categories
        self.tags = tags
        self.category_items = []  # Explicitly store category items
        self.tag_items = []  # Explicitly store tag items

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        cat_layout = QVBoxLayout()
        main_layout.addLayout(cat_layout)

        cat_label = QLabel("Task List Categories:")
        cat_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cat_label.setStyleSheet("font-weight: bold;")
        cat_layout.addWidget(cat_label)

        cat_grid = QGridLayout()
        cat_layout.addLayout(cat_grid)
        self._populate_grid(cat_grid, categories, self.category_items)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(divider)

        tag_layout = QVBoxLayout()
        main_layout.addLayout(tag_layout)

        tag_label = QLabel("Task Tags:")
        tag_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tag_label.setStyleSheet("font-weight: bold;")
        tag_layout.addWidget(tag_label)

        tag_grid = QGridLayout()
        tag_layout.addLayout(tag_grid)
        self._populate_grid(tag_grid, tags, self.tag_items)

        button = QPushButton("Print Choices")
        button.clicked.connect(self.print_choices)
        main_layout.addWidget(button)

    def _populate_grid(self, grid, items, item_list):
        for idx, item in enumerate(items):
            row, col = divmod(idx, 3)
            clickable_item = _ClickableItem(item)
            grid.addWidget(clickable_item, row, col)
            item_list.append(clickable_item)

    def get_choices(self):
        def extract_choices(items):
            include, exclude = [], []
            for item in items:
                state = item.get_state()
                if state == 1:
                    include.append(item.text())
                elif state == 2:
                    exclude.append(item.text())
            return include, exclude

        include_categories, exclude_categories = extract_choices(self.category_items)
        include_tags, exclude_tags = extract_choices(self.tag_items)

        return {
            'categories': {'include': include_categories, 'exclude': exclude_categories},
            'tags': {'include': include_tags, 'exclude': exclude_tags}
        }

    def print_choices(self):
        choices = self.get_choices()
        print("Choices:", choices)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    categories = ["Work", "Personal", "Errands", "Health"]
    tags = ["urgent", "low-priority", "optional", "high-priority"]

    picker = CategoryTagPicker(categories, tags)
    picker.setWindowTitle("Category and Tag Picker")
    picker.show()


    def on_close():
        choices = picker.get_choices()
        print("Choices:", choices)


    app.aboutToQuit.connect(on_close)
    sys.exit(app.exec())
