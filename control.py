from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from datetime import datetime
from task_manager import *
from gui import global_signals


class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setObjectName("customDateEdit")

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.date() == QDate(2000, 1, 1):
            self.setDate(QDate.currentDate())


class AddTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")

        # Set dialog properties
        self.resize(500, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Tab widget
        self.tab_widget = QTabWidget(self)
        self.main_layout.addWidget(self.tab_widget)

        # Basic Tab
        self.basic_tab = QWidget()
        self.basic_layout = QFormLayout(self.basic_tab)

        # Basic Fields
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("Enter task title")
        self.basic_layout.addRow("Title*:", self.title_edit)

        self.description_edit = QLineEdit(self)
        self.description_edit.setPlaceholderText("Enter task description")
        self.basic_layout.addRow("Description:", self.description_edit)

        self.due_date_edit = CustomDateEdit(self)
        self.basic_layout.addRow("Due Date:", self.due_date_edit)

        self.due_time_edit = QTimeEdit(self)
        self.basic_layout.addRow("Due Time:", self.due_time_edit)

        self.priority_spinbox = QSpinBox(self)
        self.priority_spinbox.setMinimum(0)
        self.priority_spinbox.setMaximum(10)
        self.priority_spinbox.setValue(0)
        self.basic_layout.addRow("Priority:", self.priority_spinbox)

        self.important_checkbox = QCheckBox("Important", self)
        self.basic_layout.addRow(self.important_checkbox)

        self.recurring_checkbox = QCheckBox("Recurring", self)
        self.basic_layout.addRow(self.recurring_checkbox)

        # Recurrence Options
        self.recurrence_options_widget = QWidget()
        self.recurrence_layout = QVBoxLayout(self.recurrence_options_widget)

        self.recur_type_group = QButtonGroup(self)

        self.every_n_days_radio = QRadioButton("Every N days")
        self.specific_weekdays_radio = QRadioButton("Specific weekdays")

        self.recur_type_group.addButton(self.every_n_days_radio)
        self.recur_type_group.addButton(self.specific_weekdays_radio)

        self.recurrence_layout.addWidget(self.every_n_days_radio)
        self.recurrence_layout.addWidget(self.specific_weekdays_radio)

        # Every N Days Widget
        self.every_n_days_widget = QWidget()
        self.every_n_days_layout = QHBoxLayout(self.every_n_days_widget)

        self.every_n_days_label = QLabel("Every")
        self.every_n_days_spinbox = QSpinBox()
        self.every_n_days_spinbox.setMinimum(1)
        self.every_n_days_spinbox.setMaximum(365)
        self.every_n_days_spinbox.setValue(1)
        self.every_n_days_unit_label = QLabel("day(s)")

        self.every_n_days_layout.addWidget(self.every_n_days_label)
        self.every_n_days_layout.addWidget(self.every_n_days_spinbox)
        self.every_n_days_layout.addWidget(self.every_n_days_unit_label)

        # Specific Weekdays Widget
        self.specific_weekdays_widget = QWidget()
        self.specific_weekdays_layout = QHBoxLayout(self.specific_weekdays_widget)

        self.weekday_checkboxes = []
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day in weekdays:
            checkbox = QCheckBox(day)
            checkbox.setObjectName(f"{day}Checkbox")
            self.weekday_checkboxes.append(checkbox)
            self.specific_weekdays_layout.addWidget(checkbox)

        self.recurrence_layout.addWidget(self.every_n_days_widget)
        self.recurrence_layout.addWidget(self.specific_weekdays_widget)

        # Initially hide recurrence detail widgets
        self.every_n_days_widget.hide()
        self.specific_weekdays_widget.hide()

        # Add recurrence options to basic layout
        self.basic_layout.addRow(self.recurrence_options_widget)

        # Connect signals
        self.recurring_checkbox.stateChanged.connect(self.toggle_recurrence_options)
        self.every_n_days_radio.toggled.connect(self.update_recurrence_detail_widgets)
        self.specific_weekdays_radio.toggled.connect(self.update_recurrence_detail_widgets)

        # Add Basic Tab to Tab Widget
        self.tab_widget.addTab(self.basic_tab, "Basic")

        # Advanced Tab
        self.advanced_tab = QWidget()
        self.advanced_layout = QFormLayout(self.advanced_tab)

        # Advanced Fields
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Not Started", "In Progress", "Completed", "Failed", "On Hold"])
        self.advanced_layout.addRow("Status:", self.status_combo)

        self.estimate_spinbox = QDoubleSpinBox()
        self.estimate_spinbox.setMinimum(0.0)
        self.estimate_spinbox.setMaximum(1000.0)
        self.estimate_spinbox.setDecimals(2)
        self.advanced_layout.addRow("Estimate (hours):", self.estimate_spinbox)

        self.count_required_spinbox = QSpinBox()
        self.count_required_spinbox.setMinimum(0)
        self.count_required_spinbox.setMaximum(1000)
        self.advanced_layout.addRow("Count Required:", self.count_required_spinbox)

        self.count_completed_spinbox = QSpinBox()
        self.count_completed_spinbox.setMinimum(0)
        self.count_completed_spinbox.setMaximum(1000)
        self.advanced_layout.addRow("Count Completed:", self.count_completed_spinbox)

        self.dependencies_edit = QLineEdit()
        self.dependencies_edit.setPlaceholderText("Dependency tasks, separated by commas")
        self.advanced_layout.addRow("Dependencies:", self.dependencies_edit)

        self.deadline_flexibility_combo = QComboBox()
        self.deadline_flexibility_combo.addItems(["Strict", "Flexible"])
        self.advanced_layout.addRow("Deadline Flexibility:", self.deadline_flexibility_combo)

        self.effort_level_combo = QComboBox()
        self.effort_level_combo.addItems(["Easy", "Medium", "Hard"])
        self.advanced_layout.addRow("Effort Level:", self.effort_level_combo)

        self.resources_edit = QLineEdit()
        self.resources_edit.setPlaceholderText("Resources, separated by commas")
        self.advanced_layout.addRow("Resources:", self.resources_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(60)
        self.advanced_layout.addRow("Notes:", self.notes_edit)

        self.time_logged_spinbox = QDoubleSpinBox()
        self.time_logged_spinbox.setMinimum(0.0)
        self.time_logged_spinbox.setMaximum(1000.0)
        self.time_logged_spinbox.setDecimals(2)
        self.advanced_layout.addRow("Time Logged (hours):", self.time_logged_spinbox)

        # Add Advanced Tab to Tab Widget
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        # Dialog Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

        self.title_edit.setFocus()

        # Object Names (for styling or testing)
        self.setObjectName("addTaskDialog")

    def toggle_recurrence_options(self, state):
        if state == Qt.CheckState.Checked.value:
            self.recurrence_options_widget.show()
            self.every_n_days_radio.setChecked(True)
            self.update_recurrence_detail_widgets()
        else:
            self.recurrence_options_widget.hide()

    def update_recurrence_detail_widgets(self):
        if self.every_n_days_radio.isChecked():
            self.every_n_days_widget.show()
            self.specific_weekdays_widget.hide()
        elif self.specific_weekdays_radio.isChecked():
            self.every_n_days_widget.hide()
            self.specific_weekdays_widget.show()
        else:
            self.every_n_days_widget.hide()
            self.specific_weekdays_widget.hide()

    def accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
            return
        super().accept()

    def get_task_data(self):
        task_data = {
            "title": self.title_edit.text(),
            "description": self.description_edit.text(),
            "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
            "due_time": self.due_time_edit.time().toString("HH:mm"),
            "priority": self.priority_spinbox.value(),
            "is_important": self.important_checkbox.isChecked(),
            "recurring": self.recurring_checkbox.isChecked(),
            "recur_every": [],  # Calculated below
            # Default Advanced Fields
            "status": self.status_combo.currentText(),
            "estimate": self.estimate_spinbox.value(),
            "count_required": self.count_required_spinbox.value(),
            "count_completed": self.count_completed_spinbox.value(),
            "dependencies": [],
            "deadline_flexibility": self.deadline_flexibility_combo.currentText(),
            "effort_level": self.effort_level_combo.currentText(),
            "resources": [],
            "notes": self.notes_edit.toPlainText(),
            "time_logged": self.time_logged_spinbox.value()
        }

        # Recurrence Data
        if self.recurring_checkbox.isChecked():
            if self.every_n_days_radio.isChecked():
                task_data["recur_every"] = [self.every_n_days_spinbox.value()]
            elif self.specific_weekdays_radio.isChecked():
                selected_weekdays = []
                weekdays_dict = {
                    "Mon": 1,
                    "Tue": 2,
                    "Wed": 3,
                    "Thu": 4,
                    "Fri": 5,
                    "Sat": 6,
                    "Sun": 7
                }
                for checkbox in self.weekday_checkboxes:
                    if checkbox.isChecked():
                        selected_weekdays.append(weekdays_dict[checkbox.text()])
                task_data["recur_every"] = selected_weekdays
        else:
            task_data["recur_every"] = None

        # Advanced Data
        dependencies_text = self.dependencies_edit.text()
        task_data["dependencies"] = [dep.strip() for dep in dependencies_text.split(",") if dep.strip()]
        resources_text = self.resources_edit.text()
        task_data["resources"] = [res.strip() for res in resources_text.split(",") if res.strip()]

        return task_data


class TaskDetailDialog(QDialog):
    def __init__(self, task, task_list_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Task Details")

        # Set dialog properties
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.task = task
        self.task_list_widget = task_list_widget
        self.is_edit_mode = False

        self.setup_ui()
        self.display_task_details()

    def setup_ui(self):
        # Main layout for the dialog
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        # Container widget for scroll area content
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        # In setup_ui method
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Layout for the scroll widget
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.setSpacing(10)

        # Header Layout: Task Name and Edit Button
        self.header_layout = QHBoxLayout()
        self.task_name_label = QLabel()
        self.task_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.task_name_label)

        self.edit_button = QPushButton()
        self.edit_button.setText("Edit")
        self.edit_button.setFixedSize(60, 24)
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        self.header_layout.addWidget(self.edit_button)
        self.header_layout.addStretch()

        # Close Button
        self.close_button = QPushButton()
        self.close_button.setText("Close")
        self.close_button.setFixedSize(60, 24)
        self.close_button.clicked.connect(self.close)
        self.header_layout.addWidget(self.close_button)

        self.scroll_layout.addLayout(self.header_layout)

        # Separator Line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.scroll_layout.addWidget(separator)

        # Task Details Area
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_widget.setLayout(self.details_layout)
        self.scroll_layout.addWidget(self.details_widget)

        # Buttons Layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addStretch()

        # Save and Cancel Buttons (only in edit mode)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_task_edits)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_edits)

    def display_task_details(self):
        # Clear existing widgets
        self.clear_layout(self.details_layout)

        # Update task name
        self.task_name_label.setText(self.task.title)

        # Description
        if self.task.description:
            description_label = QLabel(self.task.description)
            description_label.setWordWrap(True)
            description_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.details_layout.addWidget(description_label)

        # Due Date and Time
        if self.task.due_date != "2000-01-01" or self.task.due_time != "00:00":
            due_text = ""
            if self.task.due_date != "2000-01-01":
                due_text += f"Due Date: {self.task.due_date}"
            if self.task.due_time != "00:00":
                due_text += f" Due Time: {self.task.due_time}"
            due_label = QLabel(due_text)
            self.details_layout.addWidget(due_label)

        # Priority
        priority_label = QLabel(f"Priority: {self.task.priority}")
        self.details_layout.addWidget(priority_label)

        # Status
        status_label = QLabel(f"Status: {self.task.status}")
        self.details_layout.addWidget(status_label)

        # Progress Bar for Count
        if self.task.count_required > 0:
            progress_layout = QHBoxLayout()
            progress_label = QLabel(f"Progress: {self.task.count_completed}/{self.task.count_required}")
            progress_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            progress_layout.addWidget(progress_label)

            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(self.task.count_required)
            progress_bar.setValue(self.task.count_completed)
            progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            progress_layout.addWidget(progress_bar)

            # Increment/Decrement Buttons
            increment_button = QPushButton("+")
            decrement_button = QPushButton("-")
            increment_button.setFixedSize(30, 30)
            decrement_button.setFixedSize(30, 30)
            increment_button.clicked.connect(self.increment_count)
            decrement_button.clicked.connect(self.decrement_count)
            progress_layout.addWidget(increment_button)
            progress_layout.addWidget(decrement_button)

            self.details_layout.addLayout(progress_layout)

        # Notes
        if self.task.notes:
            notes_label = QLabel("Notes:")
            notes_label.setStyleSheet("font-weight: bold;")
            self.details_layout.addWidget(notes_label)
            notes_content = QLabel(self.task.notes)
            notes_content.setWordWrap(True)
            self.details_layout.addWidget(notes_content)

        # Subtasks (if implemented)
        if hasattr(self.task, 'subtasks') and self.task.subtasks:
            subtasks_label = QLabel("Subtasks:")
            subtasks_label.setStyleSheet("font-weight: bold;")
            self.details_layout.addWidget(subtasks_label)
            for subtask in self.task.subtasks:
                subtask_checkbox = QCheckBox(subtask.title)
                subtask_checkbox.setChecked(subtask.completed)
                # Optionally connect signals to handle subtask completion
                subtask_checkbox.stateChanged.connect(lambda state, st=subtask: self.toggle_subtask(st, state))
                self.details_layout.addWidget(subtask_checkbox)

        # Ensure the buttons layout is not added in view mode
        if self.is_edit_mode:
            self.main_layout.addLayout(self.buttons_layout)
        else:
            if self.buttons_layout.parent() == self.main_layout:
                self.main_layout.removeItem(self.buttons_layout)

    def toggle_edit_mode(self):
        if self.is_edit_mode:
            # Already in edit mode, do nothing
            return
        else:
            self.is_edit_mode = True
            self.switch_to_edit_mode()

    def switch_to_edit_mode(self):
        # Clear existing widgets
        self.clear_layout(self.details_layout)

        # Editable Task Name
        self.task_name_edit = QLineEdit(self.task.title)
        self.header_layout.replaceWidget(self.task_name_label, self.task_name_edit)
        self.task_name_label.hide()

        # Description
        self.description_edit = QTextEdit(self.task.description)
        self.details_layout.addWidget(QLabel("Description:"))
        self.details_layout.addWidget(self.description_edit)

        # Due Date and Time
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        if self.task.due_date != "2000-01-01":
            self.due_date_edit.setDate(QDate.fromString(self.task.due_date, "yyyy-MM-dd"))
        else:
            self.due_date_edit.setDate(QDate.currentDate())
        self.details_layout.addWidget(QLabel("Due Date:"))
        self.details_layout.addWidget(self.due_date_edit)

        self.due_time_edit = QTimeEdit()
        if self.task.due_time != "00:00":
            self.due_time_edit.setTime(QTime.fromString(self.task.due_time, "HH:mm"))
        else:
            self.due_time_edit.setTime(QTime.currentTime())
        self.details_layout.addWidget(QLabel("Due Time:"))
        self.details_layout.addWidget(self.due_time_edit)

        # Priority
        self.priority_spinbox = QSpinBox()
        self.priority_spinbox.setMinimum(0)
        self.priority_spinbox.setMaximum(10)
        self.priority_spinbox.setValue(self.task.priority)
        self.details_layout.addWidget(QLabel("Priority:"))
        self.details_layout.addWidget(self.priority_spinbox)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Not Started", "In Progress", "Completed", "Failed", "On Hold"])
        self.status_combo.setCurrentText(self.task.status)
        self.details_layout.addWidget(QLabel("Status:"))
        self.details_layout.addWidget(self.status_combo)

        # Count Required and Completed
        self.count_required_spinbox = QSpinBox()
        self.count_required_spinbox.setMinimum(0)
        self.count_required_spinbox.setMaximum(1000)
        self.count_required_spinbox.setValue(self.task.count_required)
        self.details_layout.addWidget(QLabel("Count Required:"))
        self.details_layout.addWidget(self.count_required_spinbox)

        self.count_completed_spinbox = QSpinBox()
        self.count_completed_spinbox.setMinimum(0)
        self.count_completed_spinbox.setMaximum(1000)
        self.count_completed_spinbox.setValue(self.task.count_completed)
        self.details_layout.addWidget(QLabel("Count Completed:"))
        self.details_layout.addWidget(self.count_completed_spinbox)

        # Notes
        self.notes_edit = QTextEdit(self.task.notes)
        self.details_layout.addWidget(QLabel("Notes:"))
        self.details_layout.addWidget(self.notes_edit)

        # Subtasks Editing (if applicable)
        if hasattr(self.task, 'subtasks') and self.task.subtasks:
            self.details_layout.addWidget(QLabel("Subtasks:"))
            self.subtask_edits = []
            for subtask in self.task.subtasks:
                subtask_layout = QHBoxLayout()
                subtask_checkbox = QCheckBox()
                subtask_checkbox.setChecked(subtask.completed)
                subtask_title_edit = QLineEdit(subtask.title)
                subtask_layout.addWidget(subtask_checkbox)
                subtask_layout.addWidget(subtask_title_edit)
                self.details_layout.addLayout(subtask_layout)
                self.subtask_edits.append((subtask, subtask_checkbox, subtask_title_edit))

        # Add Save and Cancel buttons
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(self.buttons_layout)

        self.save_button.show()
        self.cancel_button.show()

    def save_task_edits(self):
        if not self.task_name_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
            return

        # Update task with new values
        self.task.title = self.task_name_edit.text()
        self.task.description = self.description_edit.toPlainText()
        self.task.due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        self.task.due_time = self.due_time_edit.time().toString("HH:mm")
        self.task.priority = self.priority_spinbox.value()
        self.task.status = self.status_combo.currentText()
        self.task.count_required = self.count_required_spinbox.value()
        self.task.count_completed = self.count_completed_spinbox.value()
        self.task.notes = self.notes_edit.toPlainText()

        # Update subtasks (if applicable)
        if hasattr(self, 'subtask_edits'):
            updated_subtasks = []
            for subtask, checkbox, title_edit in self.subtask_edits:
                subtask.completed = checkbox.isChecked()
                subtask.title = title_edit.text()
                updated_subtasks.append(subtask)
            self.task.subtasks = updated_subtasks

        # Update task in the task manager
        self.task_list_widget.task_list.update_task(self.task)
        # Emit a signal to update the UI
        global_signals.task_list_updated.emit()

        # Switch back to view mode
        self.is_edit_mode = False
        self.header_layout.replaceWidget(self.task_name_edit, self.task_name_label)
        self.task_name_edit.deleteLater()
        self.task_name_label.show()

        # Remove buttons from layout
        self.buttons_layout.removeWidget(self.save_button)
        self.buttons_layout.removeWidget(self.cancel_button)
        self.save_button.hide()
        self.cancel_button.hide()

        # Refresh the details view
        self.display_task_details()

    def cancel_edits(self):
        # Switch back to view mode without saving
        self.is_edit_mode = False
        self.header_layout.replaceWidget(self.task_name_edit, self.task_name_label)
        self.task_name_edit.deleteLater()
        self.task_name_label.show()

        # Remove buttons from layout
        self.buttons_layout.removeWidget(self.save_button)
        self.buttons_layout.removeWidget(self.cancel_button)
        self.save_button.hide()
        self.cancel_button.hide()

        # Refresh the details view
        self.display_task_details()

    def increment_count(self):
        if self.task.count_completed < self.task.count_required:
            self.task.count_completed += 1
            self.task_list_widget.task_list.update_task(self.task)
            self.display_task_details()
            global_signals.task_list_updated.emit()

    def decrement_count(self):
        if self.task.count_completed > 0:
            self.task.count_completed -= 1
            self.task_list_widget.task_list.update_task(self.task)
            self.display_task_details()
            global_signals.task_list_updated.emit()

    def toggle_subtask(self, subtask, state):
        subtask.completed = (state == Qt.CheckState.Checked.value)
        # Optionally, update the task manager and UI
        self.task_list_widget.task_list.update_task(self.task)
        global_signals.task_list_updated.emit()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout(item.layout())
