from .task_widgets import *


class TagInputWidget(QWidget):
    """
    A widget that allows users to input and manage tags dynamically.
    Tags can be added from a predefined list or entered manually. Each tag
    is displayed with a delete button for easy removal.
    """

    def __init__(self, tags, tag_list=None):
        """
        Initializes the TagInputWidget.

        :param tags: A list of available tags to suggest in the input field.
        :param tag_list: An optional list of pre-existing tags to initialize the widget with.
        """
        super().__init__()
        if tag_list is None:
            tag_list = []
        self.available_tags = tags
        self.tag_list = tag_list

        self.layout = QVBoxLayout()
        self.input_field = QComboBox(self)
        self.input_field.setEditable(True)
        self.input_field.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.input_field.lineEdit().setPlaceholderText("add a tag...")
        self.input_field.addItems(self.available_tags)
        self.input_field.setCurrentIndex(-1)
        self.input_field.lineEdit().returnPressed.connect(self.add_tag)
        self.input_field.lineEdit().textEdited.connect(self.update_suggestions)

        self.tags_layout = QHBoxLayout()
        self.layout.addLayout(self.tags_layout)
        self.layout.addWidget(self.input_field)
        self.setLayout(self.layout)

        if self.tag_list:
            for tag in self.tag_list:
                self.add_existing_tag(tag)
            self.reset_suggestions()

    def add_tag(self):
        """
        Adds a new tag from the input field to the tag list if it is valid
        and not already present.
        """
        tag_text = self.input_field.currentText().strip()
        if tag_text and tag_text not in self.tag_list:
            self.add_existing_tag(tag_text)
            self.tag_list.append(tag_text)
            self.input_field.setCurrentText("")
            self.reset_suggestions()

    def add_existing_tag(self, tag_text):
        """
        Creates a tag display with the specified text and a delete button.

        :param tag_text: The text of the tag to be added.
        """
        tag_label = QLabel(f"{tag_text} ")
        delete_button = QPushButton("x")
        delete_button.setFixedSize(15, 25)
        delete_button.clicked.connect(lambda _, t=tag_text: self.remove_tag(t))

        tag_layout = QHBoxLayout()
        tag_layout.addWidget(tag_label)
        tag_layout.addWidget(delete_button)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(0)

        tag_widget = QWidget()
        tag_widget.setLayout(tag_layout)
        self.tags_layout.addWidget(tag_widget)
        tag_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def remove_tag(self, tag_text):
        """
        Removes a tag from the tag list and its associated widget from the UI.

        :param tag_text: The text of the tag to be removed.
        """
        for i in reversed(range(self.tags_layout.count())):
            tag_widget = self.tags_layout.itemAt(i).widget()
            tag_label = tag_widget.findChild(QLabel)
            if tag_label and tag_label.text().strip() == f"{tag_text}":
                self.tags_layout.takeAt(i).widget().deleteLater()
                self.tag_list.remove(tag_text)
                self.reset_suggestions()
                break

    def update_suggestions(self, text):
        self.filtered_tags = [tag for tag in self.available_tags if text.lower() in tag.lower()]
        self.input_field.clear()
        self.input_field.addItems(self.filtered_tags)
        self.input_field.setCurrentText(text)

    def reset_suggestions(self):
        self.filtered_tags = [tag for tag in self.available_tags if tag not in self.tag_list]
        self.input_field.clear()
        self.input_field.addItems(self.filtered_tags)
        self.input_field.setCurrentIndex(-1)

    def get_tags(self):
        return self.tag_list


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
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

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

        categories = []
        # if a TaskListDock
        if parent.type == "dock":
            categories = parent.task_list_widget.task_list.get_task_categories()
        elif parent.type == "stack":  # if TaskListStacked
            categories = parent.get_current_task_list_widget().task_list.get_task_categories()

        self.categories_input = TagInputWidget(categories)
        self.basic_layout.addRow("Category:", self.categories_input)

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
        self.recurrence_options_widget.hide()

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
        self.status_combo.setCurrentIndex(-1)
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
        self.deadline_flexibility_combo.setCurrentIndex(-1)  # Initialize to None
        self.advanced_layout.addRow("Deadline Flexibility:", self.deadline_flexibility_combo)

        self.effort_level_combo = QComboBox()
        self.effort_level_combo.addItems(["Easy", "Medium", "Hard"])
        self.effort_level_combo.setCurrentIndex(-1)  # Initialize to None
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

    def focusOutEvent(self, event):
        print("lost focus")
        self.close()

    def keyPressEvent(self, event, **kwargs):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.categories_input.input_field.lineEdit().hasFocus():
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

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
            "categories": self.categories_input.get_tags(),
            "is_important": self.important_checkbox.isChecked(),
            "recurring": self.recurring_checkbox.isChecked(),
            "recur_every": [],  # Calculated below
            # Default Advanced Fields
            "status": self.status_combo.currentText() if self.status_combo.currentText() else None,
            "estimate": self.estimate_spinbox.value(),
            "count_required": self.count_required_spinbox.value(),
            "count_completed": self.count_completed_spinbox.value(),
            "dependencies": [],
            "deadline_flexibility": self.deadline_flexibility_combo.currentText() if self.deadline_flexibility_combo.currentText() else None,
            "effort_level": self.effort_level_combo.currentText() if self.effort_level_combo.currentText() else None,
            "resources": [],
            "notes": self.notes_edit.toPlainText(),
            "time_logged": self.time_logged_spinbox.value()
        }

        # Recurrence Data
        if self.recurring_checkbox.isChecked():
            if self.every_n_days_radio.isChecked():
                task_data["recur_every"] = int(self.every_n_days_spinbox.value())
            elif self.specific_weekdays_radio.isChecked():
                selected_weekdays = []
                for checkbox in self.weekday_checkboxes:
                    if checkbox.isChecked():
                        selected_weekdays.append(checkbox.text())
                task_data["recur_every"] = selected_weekdays
        else:
            task_data["recur_every"] = None

        # Advanced Data
        dependencies_text = self.dependencies_edit.text()
        task_data["dependencies"] = [dep.strip() for dep in dependencies_text.split(",") if dep.strip()]
        resources_text = self.resources_edit.text()
        task_data["resources"] = [res.strip() for res in resources_text.split(",") if res.strip()]

        return task_data
