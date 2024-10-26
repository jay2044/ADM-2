from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from task_manager import *


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
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
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


class EditTaskDialog(QDialog):
    def __init__(self, task, task_list_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")

        # Set dialog properties
        self.resize(500, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

        self.task = task
        self.task_list_widget = task_list_widget

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
        self.title_edit.setText(task.title)
        self.title_edit.setPlaceholderText("Enter task title")
        self.basic_layout.addRow("Title*:", self.title_edit)

        self.description_edit = QLineEdit(self)
        self.description_edit.setText(task.description)
        self.description_edit.setPlaceholderText("Enter task description")
        self.basic_layout.addRow("Description:", self.description_edit)

        self.due_date_edit = CustomDateEdit(self)
        if task.due_date and task.due_date != "2000-01-01":
            self.due_date_edit.setDate(QDate.fromString(task.due_date, "yyyy-MM-dd"))
        else:
            self.due_date_edit.setDate(QDate.currentDate())
        self.basic_layout.addRow("Due Date:", self.due_date_edit)

        self.due_time_edit = QTimeEdit(self)
        if task.due_time and task.due_time != "00:00":
            self.due_time_edit.setTime(QTime.fromString(task.due_time, "HH:mm"))
        else:
            self.due_time_edit.setTime(QTime.currentTime())
        self.basic_layout.addRow("Due Time:", self.due_time_edit)

        self.priority_spinbox = QSpinBox(self)
        self.priority_spinbox.setMinimum(0)
        self.priority_spinbox.setMaximum(10)
        self.priority_spinbox.setValue(task.priority)
        self.basic_layout.addRow("Priority:", self.priority_spinbox)

        self.important_checkbox = QCheckBox("Important", self)
        self.important_checkbox.setChecked(task.is_important)
        self.basic_layout.addRow(self.important_checkbox)

        # Recurring Checkbox
        self.recurring_checkbox = QCheckBox("Recurring", self)
        self.recurring_checkbox.setChecked(task.recurring)
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
        self.every_n_days_unit_label = QLabel("day(s)")

        self.every_n_days_layout.addWidget(self.every_n_days_label)
        self.every_n_days_layout.addWidget(self.every_n_days_spinbox)
        self.every_n_days_layout.addWidget(self.every_n_days_unit_label)

        # Specific Weekdays Widget
        self.specific_weekdays_widget = QWidget()
        self.specific_weekdays_layout = QHBoxLayout(self.specific_weekdays_widget)

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

        # Set initial recurrence options
        if task.recurring:
            self.recurring_checkbox.setChecked(True)
            self.recurrence_options_widget.show()
            if task.recur_every and len(task.recur_every) == 1:
                self.every_n_days_radio.setChecked(True)
                self.every_n_days_widget.show()
                self.every_n_days_spinbox.setValue(task.recur_every[0])
            elif task.recur_every and len(task.recur_every) > 1:
                self.specific_weekdays_radio.setChecked(True)
                self.specific_weekdays_widget.show()
                for checkbox in self.weekday_checkboxes:
                    day_num = weekdays_dict[checkbox.text()]
                    if day_num in task.recur_every:
                        checkbox.setChecked(True)
        else:
            self.recurrence_options_widget.hide()

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
        self.status_combo.setCurrentText(task.status)
        self.advanced_layout.addRow("Status:", self.status_combo)

        self.estimate_spinbox = QDoubleSpinBox()
        self.estimate_spinbox.setMinimum(0.0)
        self.estimate_spinbox.setMaximum(1000.0)
        self.estimate_spinbox.setDecimals(2)
        self.estimate_spinbox.setValue(task.estimate)
        self.advanced_layout.addRow("Estimate (hours):", self.estimate_spinbox)

        self.count_required_spinbox = QSpinBox()
        self.count_required_spinbox.setMinimum(0)
        self.count_required_spinbox.setMaximum(1000)
        self.count_required_spinbox.setValue(task.count_required)
        self.advanced_layout.addRow("Count Required:", self.count_required_spinbox)

        self.count_completed_spinbox = QSpinBox()
        self.count_completed_spinbox.setMinimum(0)
        self.count_completed_spinbox.setMaximum(1000)
        self.count_completed_spinbox.setValue(task.count_completed)
        self.advanced_layout.addRow("Count Completed:", self.count_completed_spinbox)

        self.dependencies_edit = QLineEdit()
        self.dependencies_edit.setText(", ".join(task.dependencies))
        self.dependencies_edit.setPlaceholderText("Dependency tasks, separated by commas")
        self.advanced_layout.addRow("Dependencies:", self.dependencies_edit)

        self.deadline_flexibility_combo = QComboBox()
        self.deadline_flexibility_combo.addItems(["Strict", "Flexible"])
        self.deadline_flexibility_combo.setCurrentText(task.deadline_flexibility)
        self.advanced_layout.addRow("Deadline Flexibility:", self.deadline_flexibility_combo)

        self.effort_level_combo = QComboBox()
        self.effort_level_combo.addItems(["Easy", "Medium", "Hard"])
        self.effort_level_combo.setCurrentText(task.effort_level)
        self.advanced_layout.addRow("Effort Level:", self.effort_level_combo)

        self.resources_edit = QLineEdit()
        self.resources_edit.setText(", ".join(task.resources))
        self.resources_edit.setPlaceholderText("Resources, separated by commas")
        self.advanced_layout.addRow("Resources:", self.resources_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(60)
        self.notes_edit.setText(task.notes)
        self.advanced_layout.addRow("Notes:", self.notes_edit)

        self.time_logged_spinbox = QDoubleSpinBox()
        self.time_logged_spinbox.setMinimum(0.0)
        self.time_logged_spinbox.setMaximum(1000.0)
        self.time_logged_spinbox.setDecimals(2)
        self.time_logged_spinbox.setValue(task.time_logged)
        self.advanced_layout.addRow("Time Logged (hours):", self.time_logged_spinbox)

        # Add Advanced Tab to Tab Widget
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        # Delete Button
        hbox_layout = QHBoxLayout()
        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.delete_task_button_action)
        hbox_layout.addStretch(1)
        hbox_layout.addWidget(self.delete_button)
        self.main_layout.addLayout(hbox_layout)

        # Dialog Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

        # Object Names
        self.setObjectName("editTaskDialog")

    def toggle_recurrence_options(self, state):
        if state == Qt.CheckState.Checked.value:
            self.recurrence_options_widget.show()
            if not self.every_n_days_radio.isChecked() and not self.specific_weekdays_radio.isChecked():
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
            "recur_every": None,  # Will be calculated below
            # Advanced Fields
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
                task_data["recur_every"] = selected_weekdays if selected_weekdays else [0]
        else:
            task_data["recur_every"] = None

        # Advanced Data
        dependencies_text = self.dependencies_edit.text()
        task_data["dependencies"] = [dep.strip() for dep in dependencies_text.split(",") if dep.strip()]
        resources_text = self.resources_edit.text()
        task_data["resources"] = [res.strip() for res in resources_text.split(",") if res.strip()]

        return task_data

    def delete_task_button_action(self):
        reply = QMessageBox.question(self, 'Delete Task', 'Are you sure you want to delete this task?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.task_list_widget.delete_task(self.task)
            self.accept()
