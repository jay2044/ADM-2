from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from task_manager import *


class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.date() == QDate(2000, 1, 1):
            self.setDate(QDate.currentDate())


class AddTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        self.layout = QFormLayout(self)

        self.title_edit = QLineEdit(self)
        self.layout.addRow("Title:", self.title_edit)

        self.description_edit = QLineEdit(self)
        self.layout.addRow("Description:", self.description_edit)

        self.due_date_edit = CustomDateEdit(self)  # Use the subclassed QDateEdit
        self.layout.addRow("Due Date:", self.due_date_edit)

        self.due_time_edit = QTimeEdit(self)
        self.layout.addRow("Due Time:", self.due_time_edit)

        # Add priority spinbox
        self.priority_spinbox = QSpinBox(self)
        self.priority_spinbox.setMinimum(0)
        self.priority_spinbox.setMaximum(10)
        self.priority_spinbox.setValue(0)
        self.layout.addRow("Priority:", self.priority_spinbox)

        self.important_checkbox = QCheckBox("Important", self)
        self.layout.addRow(self.important_checkbox)

        self.recurring_checkbox = QCheckBox("Recurring", self)
        self.layout.addRow(self.recurring_checkbox)

        # Create a container widget for recurrence options
        self.recurrence_options_widget = QWidget()
        self.recurrence_layout = QVBoxLayout()
        self.recurrence_options_widget.setLayout(self.recurrence_layout)
        self.layout.addRow(self.recurrence_options_widget)

        # Initially hide the recurrence options
        self.recurrence_options_widget.hide()

        # Radio buttons to choose recurrence type
        self.recur_type_group = QButtonGroup(self)

        self.every_n_days_radio = QRadioButton("Every N days")
        self.specific_weekdays_radio = QRadioButton("Specific weekdays")

        self.recur_type_group.addButton(self.every_n_days_radio)
        self.recur_type_group.addButton(self.specific_weekdays_radio)

        # Add radio buttons to the recurrence layout
        self.recurrence_layout.addWidget(self.every_n_days_radio)
        self.recurrence_layout.addWidget(self.specific_weekdays_radio)

        # Widget for "Every N days"
        self.every_n_days_widget = QWidget()
        self.every_n_days_layout = QHBoxLayout()
        self.every_n_days_widget.setLayout(self.every_n_days_layout)

        self.every_n_days_label = QLabel("Every")
        self.every_n_days_spinbox = QSpinBox()
        self.every_n_days_spinbox.setMinimum(1)
        self.every_n_days_spinbox.setMaximum(365)
        self.every_n_days_spinbox.setValue(1)
        self.every_n_days_unit_label = QLabel("day(s)")

        self.every_n_days_layout.addWidget(self.every_n_days_label)
        self.every_n_days_layout.addWidget(self.every_n_days_spinbox)
        self.every_n_days_layout.addWidget(self.every_n_days_unit_label)

        # Widget for "Specific weekdays"
        self.specific_weekdays_widget = QWidget()
        self.specific_weekdays_layout = QHBoxLayout()
        self.specific_weekdays_widget.setLayout(self.specific_weekdays_layout)

        # Checkboxes for weekdays
        self.weekday_checkboxes = []
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day in weekdays:
            checkbox = QCheckBox(day)
            self.weekday_checkboxes.append(checkbox)
            self.specific_weekdays_layout.addWidget(checkbox)

        # Add recurrence detail widgets to the recurrence layout
        self.recurrence_layout.addWidget(self.every_n_days_widget)
        self.recurrence_layout.addWidget(self.specific_weekdays_widget)

        # Initially, hide the recurrence detail widgets
        self.every_n_days_widget.hide()
        self.specific_weekdays_widget.hide()

        # Connect signals
        self.recurring_checkbox.stateChanged.connect(self.toggle_recurrence_options)
        self.every_n_days_radio.toggled.connect(self.update_recurrence_detail_widgets)
        self.specific_weekdays_radio.toggled.connect(self.update_recurrence_detail_widgets)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

        # Set focus on the title edit when the dialog opens
        self.title_edit.setFocus()

    def toggle_recurrence_options(self, state):
        if state == Qt.CheckState.Checked.value:
            self.recurrence_options_widget.show()
            # Set default selection
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

    def get_task_data(self):
        task_data = {
            "title": self.title_edit.text(),
            "description": self.description_edit.text(),
            "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
            "due_time": self.due_time_edit.time().toString("HH:mm"),
            "priority": self.priority_spinbox.value(),
            "is_important": self.important_checkbox.isChecked(),
            "recurring": self.recurring_checkbox.isChecked(),
            "recur_every": None  # Will be calculated below
        }

        if self.recurring_checkbox.isChecked():
            if self.every_n_days_radio.isChecked():
                task_data["recur_every"] = self.every_n_days_spinbox.value()
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
                # Calculate days until next occurrence based on selected weekdays and current date
                if selected_weekdays:
                    today = QDate.currentDate()
                    today_weekday = today.dayOfWeek()  # PyQt6 dayOfWeek() returns 1 (Monday) to 7 (Sunday)
                    days_ahead_list = [((weekday - today_weekday) % 7 or 7) for weekday in selected_weekdays]
                    task_data["recur_every"] = min(days_ahead_list)
                else:
                    task_data["recur_every"] = 7  # Default to 7 days if no weekdays selected
        else:
            task_data["recur_every"] = None

        return task_data




class EditTaskDialog(QDialog):
    def __init__(self, task, task_list_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        self.task = task
        self.task_list_widget = task_list_widget

        self.layout = QFormLayout(self)

        self.title_edit = QLineEdit(self)
        self.title_edit.setText(task.title)
        self.layout.addRow("Title:", self.title_edit)

        self.description_edit = QLineEdit(self)
        self.description_edit.setText(task.description)
        self.layout.addRow("Description:", self.description_edit)

        self.due_date_edit = CustomDateEdit(self)
        if task.due_date:
            self.due_date_edit.setDate(QDate.fromString(task.due_date, "yyyy-MM-dd"))
        else:
            self.due_date_edit.setDate(QDate(2000, 1, 1))
        self.layout.addRow("Due Date:", self.due_date_edit)

        self.due_time_edit = QTimeEdit(self)
        if task.due_time:
            self.due_time_edit.setTime(QTime.fromString(task.due_time, "HH:mm"))
        else:
            self.due_time_edit.setTime(QTime(0, 0))
        self.layout.addRow("Due Time:", self.due_time_edit)

        self.priority_spinbox = QSpinBox(self)
        self.priority_spinbox.setMinimum(0)
        self.priority_spinbox.setMaximum(10)
        self.priority_spinbox.setValue(task.priority)
        self.layout.addRow("Priority:", self.priority_spinbox)

        self.important_checkbox = QCheckBox("Important", self)
        self.important_checkbox.setChecked(task.is_important)
        self.layout.addRow(self.important_checkbox)

        # Add recurring checkbox
        self.recurring_checkbox = QCheckBox("Recurring", self)
        self.recurring_checkbox.setChecked(task.recurring)
        self.layout.addRow(self.recurring_checkbox)

        # Create a container widget for recurrence options
        self.recurrence_options_widget = QWidget()
        self.recurrence_layout = QVBoxLayout()
        self.recurrence_options_widget.setLayout(self.recurrence_layout)
        self.layout.addRow(self.recurrence_options_widget)

        # Initially hide or show the recurrence options
        if self.recurring_checkbox.isChecked():
            self.recurrence_options_widget.show()
        else:
            self.recurrence_options_widget.hide()

        # Radio buttons to choose recurrence type
        self.recur_type_group = QButtonGroup(self)

        self.every_n_days_radio = QRadioButton("Every N days")
        self.specific_weekdays_radio = QRadioButton("Specific weekdays")

        self.recur_type_group.addButton(self.every_n_days_radio)
        self.recur_type_group.addButton(self.specific_weekdays_radio)

        # Add radio buttons to the recurrence layout
        self.recurrence_layout.addWidget(self.every_n_days_radio)
        self.recurrence_layout.addWidget(self.specific_weekdays_radio)

        # Widget for "Every N days"
        self.every_n_days_widget = QWidget()
        self.every_n_days_layout = QHBoxLayout()
        self.every_n_days_widget.setLayout(self.every_n_days_layout)

        self.every_n_days_label = QLabel("Every")
        self.every_n_days_spinbox = QSpinBox()
        self.every_n_days_spinbox.setMinimum(1)
        self.every_n_days_spinbox.setMaximum(365)
        self.every_n_days_spinbox.setValue(task.recur_every if task.recur_every else 1)
        self.every_n_days_unit_label = QLabel("day(s)")

        self.every_n_days_layout.addWidget(self.every_n_days_label)
        self.every_n_days_layout.addWidget(self.every_n_days_spinbox)
        self.every_n_days_layout.addWidget(self.every_n_days_unit_label)

        # Widget for "Specific weekdays"
        self.specific_weekdays_widget = QWidget()
        self.specific_weekdays_layout = QHBoxLayout()
        self.specific_weekdays_widget.setLayout(self.specific_weekdays_layout)

        # Checkboxes for weekdays
        self.weekday_checkboxes = []
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekdays_dict = {
            "Mon": 1,
            "Tue": 2,
            "Wed": 3,
            "Thu": 4,
            "Fri": 5,
            "Sat": 6,
            "Sun": 7
        }
        for day in weekdays:
            checkbox = QCheckBox(day)
            self.weekday_checkboxes.append(checkbox)
            self.specific_weekdays_layout.addWidget(checkbox)

        # Add recurrence detail widgets to the recurrence layout
        self.recurrence_layout.addWidget(self.every_n_days_widget)
        self.recurrence_layout.addWidget(self.specific_weekdays_widget)

        # Initially, hide the recurrence detail widgets
        self.every_n_days_widget.hide()
        self.specific_weekdays_widget.hide()

        # Connect signals
        self.recurring_checkbox.stateChanged.connect(self.toggle_recurrence_options)
        self.every_n_days_radio.toggled.connect(self.update_recurrence_detail_widgets)
        self.specific_weekdays_radio.toggled.connect(self.update_recurrence_detail_widgets)

        # Set the initial recurrence type based on the task data
        if task.recurring:
            # Assuming you have stored the recurrence pattern somewhere in the task
            # For simplicity, we'll default to "Every N days"
            self.every_n_days_radio.setChecked(True)
            self.update_recurrence_detail_widgets()
        else:
            self.recurrence_options_widget.hide()

        # Delete button
        hbox_layout = QHBoxLayout()
        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.delete_task_button_action)
        hbox_layout.addStretch(1)
        hbox_layout.addWidget(self.delete_button)
        self.layout.addRow(hbox_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def toggle_recurrence_options(self, state):
        if state == Qt.CheckState.Checked.value:
            self.recurrence_options_widget.show()
            # Set default selection
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

    def get_task_data(self):
        task_data = {
            "title": self.title_edit.text(),
            "description": self.description_edit.text(),
            "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
            "due_time": self.due_time_edit.time().toString("HH:mm"),
            "priority": self.priority_spinbox.value(),
            "is_important": self.important_checkbox.isChecked(),
            "recurring": self.recurring_checkbox.isChecked(),
            "recur_every": None  # Will be calculated below
        }

        if self.recurring_checkbox.isChecked():
            if self.every_n_days_radio.isChecked():
                task_data["recur_every"] = self.every_n_days_spinbox.value()
            elif self.specific_weekdays_radio.isChecked():
                selected_weekdays = []
                for checkbox in self.weekday_checkboxes:
                    if checkbox.isChecked():
                        selected_weekdays.append(weekdays_dict[checkbox.text()])
                # Calculate days until next occurrence based on selected weekdays and current date
                if selected_weekdays:
                    today = QDate.currentDate()
                    today_weekday = today.dayOfWeek()  # PyQt6 dayOfWeek() returns 1 (Monday) to 7 (Sunday)
                    days_ahead_list = [((weekday - today_weekday) % 7 or 7) for weekday in selected_weekdays]
                    task_data["recur_every"] = min(days_ahead_list)
                else:
                    task_data["recur_every"] = 7  # Default to 7 days if no weekdays selected
        else:
            task_data["recur_every"] = None

        return task_data

    def delete_task_button_action(self):
        self.task_list_widget.delete_task(self.task)
        self.accept()

