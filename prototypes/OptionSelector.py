from PyQt6.QtWidgets import *


class OptionSelector(QWidget):
    def __init__(self, name: str, options: list[str], default_value: str = None, fixed_width: int = None):
        super().__init__()

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name + ":")
        main_layout.addWidget(name_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        for option in options:
            btn = QPushButton(option)
            btn.setCheckable(True)
            btn.setFlat(False)
            if fixed_width:
                btn.setFixedWidth(fixed_width)
            self.button_group.addButton(btn)

            if option == default_value:
                btn.setChecked(True)
            button_layout.addWidget(btn)

        container = QWidget()
        container.setLayout(button_layout)
        main_layout.addWidget(container)

        self.setLayout(main_layout)


app = QApplication([])
window = OptionSelector("Flexibility", ["Strict", "Flexible", "Very Flexible"], default_value="Flexible")
window.show()
app.exec()
