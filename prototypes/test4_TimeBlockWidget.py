from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QListWidget, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette


class TimeBlockWidget(QWidget):
    def __init__(self, start_time, end_time, color=None, name="", parent=None, empty=False, unavailable=False):
        super().__init__(parent)

        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.color = color
        self.tasks = []

        self.schedule_manager = parent.schedule_manager if parent and hasattr(parent, 'schedule_manager') else None
        if self.schedule_manager:
            self.tasks = self.schedule_manager.get_tasks(self.name)

        start_hour = int(self.start_time.split(':')[0])
        end_hour = int(self.end_time.split(':')[0])
        self.base_height = max(40 * (end_hour - start_hour), 40)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.frame.setFixedHeight(self.base_height)

        if not empty and not unavailable:
            self.init_ui_time_block_with_tasks()
        elif empty:
            self.init_ui_empty()
        elif unavailable:
            self.init_ui_unavailable()

        if self.tasks:
            self.load_tasks()

    def setup_frame(self, name, color):
        self.name = name
        color_rgba = QColor(color[0], color[1], color[2], 128)
        palette = self.frame.palette()
        palette.setColor(QPalette.ColorRole.Window, color_rgba)
        self.frame.setAutoFillBackground(True)
        self.frame.setPalette(palette)

        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(5, 5, 5, 5)

        self.name_label = QLabel(self.name, self.frame)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.frame_layout.addWidget(self.name_label)

        self.layout.addWidget(self.frame)

    def init_ui_time_block_with_tasks(self):
        self.setup_frame(self.name, self.color)
        self.task_list = QListWidget(self.frame)
        self.task_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frame_layout.addWidget(self.task_list)

    def init_ui_empty(self):
        self.setup_frame("No tasks", (47, 47, 47))

    def init_ui_unavailable(self):
        self.setup_frame("Unavailable", (231, 131, 97))

    def load_tasks(self):
        for task in self.tasks:
            self.add_task(task)

    def add_task(self, task):
        self.task_list.addItem(task)
        task_height = self.task_list.sizeHintForRow(0)
        if (self.base_height - self.name_label.height()) / task_height < self.task_list.count():
            self.base_height += task_height
            self.frame.setFixedHeight(self.base_height)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    demo_window = QWidget()
    demo_layout = QVBoxLayout(demo_window)

    # Create TimeBlockWidgets
    time_block_1 = TimeBlockWidget("7:00 AM", "9:00 AM", (3, 204, 163), name="Morning Routine")
    time_block_1.add_task("Exercise")
    time_block_1.add_task("Breakfast")
    time_block_1.add_task("Exercise")
    time_block_1.add_task("Breakfast")
    time_block_1.add_task("Exercise")
    time_block_1.add_task("Breakfast")
    time_block_1.add_task("Exercise")
    time_block_1.add_task("Breakfast")
    time_block_1.add_task("Exercise")
    time_block_1.add_task("Breakfast")

    time_block_2 = TimeBlockWidget("9:00 AM", "5:00 PM", (0, 123, 255), "Work")
    time_block_2.add_task("Meeting with team")
    time_block_2.add_task("Finish report")
    time_block_2.add_task("Meeting with team")
    time_block_2.add_task("Finish report")
    time_block_2.add_task("Meeting with team")
    time_block_2.add_task("Finish report")
    time_block_2.add_task("Meeting with team")
    time_block_2.add_task("Finish report")

    time_block_3 = TimeBlockWidget("6:00 PM", "8:00 PM", unavailable=True)
    time_block_4 = TimeBlockWidget("4:00 AM", "7:00 AM", empty=True)

    demo_layout.addWidget(time_block_1)
    demo_layout.addWidget(time_block_2)
    demo_layout.addWidget(time_block_3)
    demo_layout.addWidget(time_block_4)

    demo_window.resize(400, 600)
    demo_window.show()

    print(time_block_1.height())

    sys.exit(app.exec())
