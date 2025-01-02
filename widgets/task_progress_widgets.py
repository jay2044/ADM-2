from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from core.task_manager import *


class TaskProgressBar(QWidget):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet("QProgressBar { text-align: center; font-size: 12px; }")
        self.update_progress()
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def update_progress(self):
        progress = self.calculate_progress()
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{progress}%")

    def calculate_progress(self):
        total_weight = 0
        progress = 0

        if self.task.count_required > 0:
            count_progress = (self.task.count_completed / self.task.count_required) * 100
            progress += count_progress
            total_weight += 1

        if self.task.time_estimate > 0:
            time_progress = (self.task.time_logged / self.task.time_estimate) * 100
            progress += time_progress
            total_weight += 1

        if self.task.subtasks:
            completed_subtasks = sum(subtask["completed"] for subtask in self.task.subtasks)
            subtask_progress = (completed_subtasks / len(self.task.subtasks)) * 100
            progress += subtask_progress
            total_weight += 1

        return int(progress / total_weight) if total_weight > 0 else 0


class CountProgressWidget(QWidget):
    def __init__(self, task, task_list_widget, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.task = task
        self.task_list_widget = task_list_widget
        self.count_required = self.task.count_required
        self.count_completed = self.task.count_completed

        self.progress_layout = QHBoxLayout(self)
        self.progress_layout.setContentsMargins(10, 5, 10, 5)
        self.progress_layout.setSpacing(5)

        self.decrement_button = QPushButton("−", self)
        self.decrement_button.setFixedSize(30, 30)
        self.decrement_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.decrement_button.clicked.connect(self.decrement_count)
        self.progress_layout.addWidget(self.decrement_button)

        self.progress_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(self.count_required)
        self.progress_bar.setValue(self.count_completed)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_layout.addWidget(self.progress_bar)

        self.progress_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.count_label = QLabel(self)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_layout.addWidget(self.count_label)

        self.progress_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.increment_button = QPushButton("+", self)
        self.increment_button.setFixedSize(30, 30)
        self.increment_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.increment_button.clicked.connect(self.increment_count)
        self.progress_layout.addWidget(self.increment_button)

        self.update_progress()

    def increment_count(self):
        if self.count_completed < self.count_required:
            self.count_completed += 1
            self.task.count_completed = self.count_completed
            self.update_task()
            self.update_progress()

    def decrement_count(self):
        if self.count_completed > 0:
            self.count_completed -= 1
            self.task.count_completed = self.count_completed
            self.update_task()
            self.update_progress()

    def update_progress(self):
        self.progress_bar.setValue(self.count_completed)
        percentage = (self.count_completed / self.count_required) * 100 if self.count_required > 0 else 0
        self.progress_bar.setFormat(f"{percentage:.0f}%")
        self.count_label.setText(f"{self.count_completed}/{self.count_required}")
        if hasattr(self.parent, 'progress_bar') and hasattr(self.parent.progress_bar, 'update_progress'):
            self.parent.progress_bar.update_progress()

    def update_task(self):
        self.task_list_widget.manager.update_task(self.task)
        global_signals.task_list_updated.emit()


class TimeProgressWidget(QWidget):
    def __init__(self, task, task_list_widget, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.task = task
        self.task_list_widget = task_list_widget
        self.estimate = self.task.time_estimate
        self.time_logged = self.task.time_logged

        self.time_layout = QHBoxLayout(self)
        self.time_layout.setContentsMargins(10, 5, 10, 5)
        self.time_layout.setSpacing(5)

        self.decrement_time_button = QPushButton("−", self)
        self.decrement_time_button.setFixedSize(30, 30)
        self.decrement_time_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.decrement_time_button.clicked.connect(self.decrement_time_logged)
        self.time_layout.addWidget(self.decrement_time_button)

        self.time_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.time_progress_bar = QProgressBar(self)
        self.time_progress_bar.setMinimum(0)
        self.time_progress_bar.setMaximum(int(self.estimate))
        self.time_progress_bar.setValue(int(self.time_logged))
        self.time_progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_layout.addWidget(self.time_progress_bar)

        self.time_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_layout.addWidget(self.time_label)

        self.time_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.increment_time_button = QPushButton("+", self)
        self.increment_time_button.setFixedSize(30, 30)
        self.increment_time_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.increment_time_button.clicked.connect(self.increment_time_logged)
        self.time_layout.addWidget(self.increment_time_button)

        self.record_time_button = QPushButton("⏱", self)
        self.record_time_button.setFixedSize(30, 30)
        self.record_time_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.record_time_button.clicked.connect(self.record_time)
        self.time_layout.addWidget(self.record_time_button)

        self.update_progress()

    def increment_time_logged(self):
        if self.time_logged < self.estimate:
            self.time_logged += 1
            self.task.time_logged = self.time_logged
            self.update_task()
            self.update_progress()

    def decrement_time_logged(self):
        if self.time_logged > 0:
            self.time_logged -= 1
            self.task.time_logged = self.time_logged
            self.update_task()
            self.update_progress()

    def record_time(self):
        pass

    def update_progress(self):
        self.time_progress_bar.setValue(int(self.time_logged))
        percentage = (self.time_logged / self.estimate) * 100 if self.estimate > 0 else 0
        self.time_progress_bar.setFormat(f"{percentage:.0f}%")
        time_logged_display = f"{self.time_logged:.2f}".rstrip("0").rstrip(".")
        estimate_display = f"{self.estimate:.2f}".rstrip("0").rstrip(".")
        self.time_label.setText(f"Hr: {time_logged_display}/{estimate_display}")
        if hasattr(self.parent, 'progress_bar') and hasattr(self.parent.progress_bar, 'update_progress'):
            self.parent.progress_bar.update_progress()

    def update_task(self):
        self.task_list_widget.manager.update_task(self.task)
        global_signals.task_list_updated.emit()

