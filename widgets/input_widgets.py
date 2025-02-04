from .task_widgets import *
import uuid
from datetime import time


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


class PeriodSelectionCalendar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.added_date_time = None
        self.due_date_time = None
        self._state = 0
        self.startLineEdit = QLineEdit("None")
        self.endLineEdit = QLineEdit("None")
        self.startLineEdit.setReadOnly(True)
        self.endLineEdit.setReadOnly(True)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._handleDateClicked)
        timeLayout = QHBoxLayout()
        self.dueTimeEdit = QTimeEdit()
        self.dueTimeEdit.setDisplayFormat("hh:mm AP")
        self.dueTimeEdit.setTime(QTime(12, 0))
        self.clearTimeButton = QPushButton("Clear Time")
        timeLayout.addWidget(self.dueTimeEdit)
        timeLayout.addWidget(self.clearTimeButton)
        self.dueTimeEdit.timeChanged.connect(self._onDueTimeChanged)
        self.clearTimeButton.clicked.connect(self._onClearDueTime)
        self._last_highlight_start = None
        self._last_highlight_end = None
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.startLineEdit)
        topLayout.addWidget(self.endLineEdit)
        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.calendar)
        mainLayout.addLayout(timeLayout)
        self._refreshDisplay()

    def _handleDateClicked(self, date: QDate):
        if self._state == 0:
            self.due_date_time = date;
            self._state = 1
        elif self._state == 1:
            if date == self.due_date_time:
                self.added_date_time = date;
                self._state = 2
            else:
                self.due_date_time = date
        else:
            if date == self.added_date_time:
                self._clearDates();
                return
            else:
                self.due_date_time = date
        self._refreshDisplay()

    def _refreshDisplay(self):
        if self.added_date_time is None:
            self.startLineEdit.setText("None")
        else:
            self.startLineEdit.setText(self.added_date_time.toString("yyyy-MM-dd"))
        if self.due_date_time is None:
            self.endLineEdit.setText("None")
        else:
            self.endLineEdit.setText(self.due_date_time.toString("yyyy-MM-dd"))
        if self.due_date_time is None:
            self.dueTimeEdit.setEnabled(False);
            self.clearTimeButton.setEnabled(False)
        else:
            self.dueTimeEdit.setEnabled(True);
            self.clearTimeButton.setEnabled(True)
            if isinstance(self.due_date_time, QDate):
                self.dueTimeEdit.setTime(QTime(12, 0))
            else:
                self.dueTimeEdit.setTime(self.due_date_time.time())
        if self.added_date_time:
            self.calendar.setMinimumDate(self.added_date_time)
        else:
            self.calendar.setMinimumDate(QDate(1900, 1, 1))
        self._highlightSelection()

    def _highlightSelection(self):
        default_fmt = QTextCharFormat()
        if self._last_highlight_start and self._last_highlight_end:
            cur = self._last_highlight_start
            while cur <= self._last_highlight_end:
                self.calendar.setDateTextFormat(cur, default_fmt);
                cur = cur.addDays(1)
        if not self.due_date_time:
            self._last_highlight_start = None;
            self._last_highlight_end = None;
            return
        highlight_fmt = QTextCharFormat();
        highlight_fmt.setBackground(QBrush(QColor("lightblue")))
        if self.added_date_time and self.due_date_time:
            start = min(self.added_date_time, self.due_date_time)
            end = max(self.added_date_time, self.due_date_time)
            cur = start
            while cur <= end:
                self.calendar.setDateTextFormat(cur, highlight_fmt);
                cur = cur.addDays(1)
            self._last_highlight_start = start;
            self._last_highlight_end = end
        elif self.due_date_time:
            self.calendar.setDateTextFormat(self.due_date_time, highlight_fmt)
            self._last_highlight_start = self.due_date_time;
            self._last_highlight_end = self.due_date_time

    def _clearDates(self):
        self.added_date_time = None;
        self.due_date_time = None;
        self._state = 0
        self.calendar.setMinimumDate(QDate(1900, 1, 1));
        self._refreshDisplay()

    def getSelectedDates(self):
        return self.added_date_time, self.due_date_time

    def getDateStates(self):
        added_state = "none" if self.added_date_time is None else "added"
        due_state = "none" if self.due_date_time is None else "due"
        return {"added_date_time": self.added_date_time, "added_state": added_state,
                "due_date_time": self.due_date_time, "due_state": due_state}

    def _onDueTimeChanged(self, time):
        if isinstance(self.due_date_time, QDate):
            self.due_date_time = QDateTime(self.due_date_time, time)
        elif self.due_date_time is None:
            self.due_date_time = QDateTime(QDate.currentDate(), time)
        else:
            self.due_date_time.setTime(time)

    def _onClearDueTime(self):
        self.dueTimeEdit.setTime(QTime(12, 0))
        if isinstance(self.due_date_time, QDateTime):
            self.due_date_time.setTime(QTime(12, 0))


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


class AddTaskDialog(QDialog):
    def __init__(self, parent=None, task_list_widget=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")
        self.resize(500, 400)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

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
            categories = parent.task_list_widget.task_list.get_task_tags()
        elif parent.type == "stack":  # if TaskListStacked
            categories = parent.get_current_task_list_widget().task_list.get_task_tags()

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
        self.deadline_flexibility_combo.addItems(["Strict", "Flexible", "Very Flexible"])
        self.deadline_flexibility_combo.setCurrentIndex(-1)  # Initialize to None
        self.advanced_layout.addRow("Deadline Flexibility:", self.deadline_flexibility_combo)

        self.effort_level_combo = QComboBox()
        self.effort_level_combo.addItems(["Low", "Medium", "High"])
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
        due_date = self.due_date_edit.date()
        due_time = self.due_time_edit.time()
        due_datetime = None
        if due_date and not due_date.isNull():
            if due_date != QDate(2000, 1, 1):
                py_date = due_date.toPyDate()
                py_time = due_time.toPyTime()
                due_datetime = datetime.combine(py_date, py_time)

        task_data = {
            "name": self.title_edit.text(),
            "description": self.description_edit.text(),
            "notes": self.notes_edit.toPlainText(),
            "tags": self.categories_input.get_tags(),
            "resources": [res.strip() for res in self.resources_edit.text().split(",") if res.strip()],
            "start_date": None,  # Missing in the method
            "due_datetime": due_datetime,
            "added_date_time": None,  # Missing in the method
            "last_completed_date": None,  # Missing in the method
            "list_order": 0,  # Default value, missing in the method
            "list_name": self.task_list_widget.task_list_name,
            "recurring": self.recurring_checkbox.isChecked(),
            "recur_every": int(self.every_n_days_spinbox.value()) if self.every_n_days_radio.isChecked() else [
                checkbox.text() for checkbox in self.weekday_checkboxes if checkbox.isChecked()
            ] if self.specific_weekdays_radio.isChecked() else None,
            "recurrences": 0,  # Default value, missing in the method
            "time_estimate": self.estimate_spinbox.value(),
            "time_chunk_size": None,  # Missing in the method
            "time_of_day_preference": None,  # Missing in the method
            "time_logged": self.time_logged_spinbox.value(),
            "count_required": self.count_required_spinbox.value(),
            "count_chunk_size": 1,  # Default value, missing in the method
            "count_completed": self.count_completed_spinbox.value(),
            "subtasks": None,  # Missing in the method
            "dependencies": [dep.strip() for dep in self.dependencies_edit.text().split(",") if dep.strip()],
            "status": self.status_combo.currentText() if self.status_combo.currentText() else 'Not Started',
            "flexibility": self.deadline_flexibility_combo.currentText() if self.deadline_flexibility_combo.currentText() else 'Flexible',
            "effort_level": self.effort_level_combo.currentText() if self.effort_level_combo.currentText() else 'Medium',
            "priority": self.priority_spinbox.value(),
            "previous_priority": 0,  # Default value, missing in the method
            "preferred_work_days": None,  # Missing in the method
            "progress": 0.0,  # Default value, missing in the method
            "urgency": 0.0,  # Default value, missing in the method
            "milestones": None,  # Missing in the method
            "global_weight": None,  # Missing in the method
            "schedule_weight": None,  # Missing in the method
            "behind_schedule": False,  # Default value, missing in the method
        }

        return task_data


class DraggableBlockTimeScaleWidget(QWidget):
    def __init__(self, parent, day_start_time, duration_hours, from_time=None, color=None, from_time_edit=None,
                 to_time_edit=None, fixed_height=480):
        super().__init__()
        self.parent = parent
        self.day_start_time = day_start_time
        self.duration_hours = duration_hours
        self.color = color
        self.fixed_height = fixed_height
        if from_time is None:
            self.from_time = self.day_start_time
        else:
            self.from_time = from_time
        self.to_time = self.from_time + timedelta(hours=self.duration_hours)
        self.init_ui()

        self.from_time_edit = from_time_edit
        self.from_time_edit.setDisplayFormat("hh:mm ap")
        self.from_time_edit.setTime(QTime(self.from_time.hour, self.from_time.minute))
        self.from_time_edit.timeChanged.connect(self.on_from_time_edit_changed)
        self.to_time_edit = to_time_edit
        self.to_time_edit.setDisplayFormat("hh:mm ap")
        self.to_time_edit.setTime(QTime(self.to_time.hour, self.to_time.minute))
        self.to_time_edit.timeChanged.connect(self.on_to_time_edit_changed)

        self.just_dragged = False

    def init_ui(self):
        self.setFixedHeight(self.fixed_height)
        self.setMinimumWidth(150)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.scale_labels = QWidget(self)
        self.scale_labels.setFixedHeight(self.fixed_height)
        self.scale_labels.setFixedWidth(60)
        self.scale_layout = QVBoxLayout(self.scale_labels)
        self.scale_layout.setContentsMargins(0, 0, 0, 0)
        self.scale_layout.setSpacing(0)

        self.populate_time_scale()
        self.pixels_per_minute = self.fixed_height / (24.0 * 60.0)
        self.duration_minutes = self.duration_hours * 60

        self.draggable_block = QFrame(self)
        if self.color:
            self.draggable_block.setStyleSheet(f"background-color: {self.color};")
        self.draggable_block.setFrameShape(QFrame.Shape.StyledPanel)
        self.draggable_block.setCursor(Qt.CursorShape.OpenHandCursor)
        self.draggable_block.setFixedHeight(int(self.duration_minutes * self.pixels_per_minute))

        self.is_dragging = False
        self.offset = QPoint()
        self.block_start_time = max(0.0, (self.from_time - self.day_start_time).total_seconds() / 60)
        self.draggable_block.move(40, int(self.block_start_time * self.pixels_per_minute))

        self.draggable_block.mousePressEvent = self.block_mouse_press
        self.draggable_block.mouseMoveEvent = self.block_mouse_move
        self.draggable_block.mouseReleaseEvent = self.block_mouse_release

        self.layout.addWidget(self.scale_labels)

    def populate_time_scale(self):
        for hour in range(24):
            current_time = self.day_start_time + timedelta(hours=hour)
            display_hour = current_time.strftime("%I %p").lstrip("0")
            label = QLabel(display_hour if hour % 4 == 0 else "·")
            if hour % 4 == 0:
                label.setStyleSheet("font-weight: bold; font-size: 8pt;")
                label.setFixedHeight(22)
            else:
                label.setStyleSheet("color: lightgray; font-size: 6pt;")
                label.setFixedHeight(12)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.scale_layout.addWidget(label)

    def on_from_time_edit_changed(self, time):
        new_from = time.toPyTime()
        base_date = self.day_start_time.date()
        dt_from = datetime.combine(base_date, new_from)
        dt_to = self.get_to_time()
        diff = (dt_to - dt_from).total_seconds() / 60
        if diff < 1:
            dt_from = dt_to - timedelta(minutes=1)

        self.block_start_time = max(0, (dt_from - self.day_start_time).total_seconds() / 60)
        self.block_start_time = min(self.block_start_time, (24 * 60 - self.duration_minutes))  # Ensure within bounds

        self.duration_minutes = (dt_to - dt_from).total_seconds() / 60
        self.draggable_block.move(self.draggable_block.x(), int(self.block_start_time * self.pixels_per_minute))
        self.draggable_block.setFixedHeight(int(self.duration_minutes * self.pixels_per_minute))

        self.from_time_edit.blockSignals(True)
        self.from_time_edit.setTime(QTime(dt_from.hour, dt_from.minute))
        self.from_time_edit.blockSignals(False)

        if not self.just_dragged:
            self.just_dragged = False
        else:
            self.parent.sync(self)

    def on_to_time_edit_changed(self, time):
        new_to = time.toPyTime()
        base_date = self.day_start_time.date()
        dt_to = datetime.combine(base_date, new_to)
        dt_from = self.get_from_time()
        diff = (dt_to - dt_from).total_seconds() / 60
        if diff < 1:
            dt_to = dt_from + timedelta(minutes=1)
        self.block_start_time = max(0, (dt_from - self.day_start_time).total_seconds() / 60)
        self.duration_minutes = (dt_to - dt_from).total_seconds() / 60
        self.draggable_block.move(self.draggable_block.x(), int(self.block_start_time * self.pixels_per_minute))
        self.draggable_block.setFixedHeight(int(self.duration_minutes * self.pixels_per_minute))
        self.to_time_edit.blockSignals(True)
        self.to_time_edit.setTime(QTime(dt_to.hour, dt_to.minute))
        self.to_time_edit.blockSignals(False)

        if not self.just_dragged:
            self.just_dragged = False
        else:
            self.parent.sync(self)

    def block_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.draggable_block.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.offset = event.pos()

    def block_mouse_move(self, event):
        if self.is_dragging:
            new_pos = self.draggable_block.mapToParent(event.pos() - self.offset)
            new_y = max(0, min(new_pos.y(), self.height() - self.draggable_block.height()))
            self.draggable_block.move(self.draggable_block.x(), new_y)

            # Update block_start_time within bounds
            self.block_start_time = new_y / self.pixels_per_minute
            self.block_start_time = min(self.block_start_time,
                                        (24 * 60 - self.duration_minutes))  # Ensure block doesn't exceed 24 hours

            # Update time edits
            from_time = self.get_from_time()
            to_time = self.get_to_time()
            self.from_time_edit.blockSignals(True)
            self.to_time_edit.blockSignals(True)
            self.from_time_edit.setTime(QTime(from_time.hour, from_time.minute))
            self.to_time_edit.setTime(QTime(to_time.hour, to_time.minute))
            self.from_time_edit.blockSignals(False)
            self.to_time_edit.blockSignals(False)

    def block_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.just_dragged = True
            self.is_dragging = False
            self.draggable_block.setCursor(Qt.CursorShape.OpenHandCursor)
            self.block_start_time = round(self.block_start_time / 5) * 5
            self.draggable_block.move(self.draggable_block.x(), int(self.block_start_time * self.pixels_per_minute))
            from_time = self.get_from_time()
            to_time = self.get_to_time()
            if (to_time - from_time).total_seconds() < 60:
                to_time = from_time + timedelta(minutes=1)
            self.from_time_edit.blockSignals(True)
            self.to_time_edit.blockSignals(True)
            self.from_time_edit.setTime(QTime(from_time.hour, from_time.minute))
            self.to_time_edit.setTime(QTime(to_time.hour, to_time.minute))
            self.from_time_edit.blockSignals(False)
            self.to_time_edit.blockSignals(False)

            self.parent.sync(self)

    def get_from_time(self):
        return self.day_start_time + timedelta(minutes=self.block_start_time)

    def get_to_time(self):
        return self.day_start_time + timedelta(minutes=self.block_start_time + self.duration_minutes)

    def update_duration(self, new_duration_hours):
        self.duration_hours = new_duration_hours
        new_minutes = self.duration_hours * 60
        if new_minutes < 1:
            new_minutes = 1
        old_from = self.get_from_time()
        old_to = old_from + timedelta(minutes=new_minutes)
        self.block_start_time = max(0, (old_from - self.day_start_time).total_seconds() / 60)
        self.duration_minutes = new_minutes
        new_height = int(self.duration_minutes * self.pixels_per_minute)
        self.draggable_block.setFixedHeight(new_height)
        current_y = self.draggable_block.y()
        max_y = self.height() - new_height
        if current_y > max_y:
            self.draggable_block.move(self.draggable_block.x(), max_y)
        self.from_time_edit.setTime(QTime(old_from.hour, old_from.minute))
        self.to_time_edit.setTime(QTime(old_to.hour, old_to.minute))

    def set_color(self, color):
        if isinstance(color, tuple) and len(color) == 3:
            self.color = f"rgb({color[0]}, {color[1]}, {color[2]})"
        else:
            self.color = color
        self.draggable_block.setStyleSheet(f"background-color: {self.color};")

    def sync_with_widget(self, other_widget):
        # Sync attributes
        self.day_start_time = other_widget.day_start_time
        self.duration_hours = other_widget.duration_hours
        self.color = other_widget.color
        self.from_time = other_widget.from_time
        self.to_time = other_widget.to_time

        # Update the draggable block's size and position
        self.duration_minutes = other_widget.duration_minutes
        self.block_start_time = other_widget.block_start_time
        self.draggable_block.setFixedHeight(int(self.duration_minutes * self.pixels_per_minute))
        self.draggable_block.move(
            self.draggable_block.x(),  # Keep the same X position
            int(self.block_start_time * self.pixels_per_minute)
        )

        # Update time edits
        self.from_time_edit.blockSignals(True)
        self.from_time_edit.setTime(QTime(self.from_time.hour, self.from_time.minute))
        self.from_time_edit.blockSignals(False)

        self.to_time_edit.blockSignals(True)
        self.to_time_edit.setTime(QTime(self.to_time.hour, self.to_time.minute))
        self.to_time_edit.blockSignals(False)

    def set_schedule(self, from_time: time, to_time: time):
        """
        Update the draggable block to use the given from_time and to_time.
        """
        # Compute datetime objects based on the base date from day_start_time
        base_date = self.day_start_time.date()
        dt_from = datetime.combine(base_date, from_time)
        dt_to = datetime.combine(base_date, to_time)
        if dt_to <= dt_from:
            dt_to += timedelta(days=1)  # allow over-midnight ranges

        # Update attributes
        self.from_time = from_time
        self.duration_hours = (dt_to - dt_from).total_seconds() / 3600.0
        self.duration_minutes = self.duration_hours * 60

        # Calculate block_start_time relative to day_start_time (in minutes)
        self.block_start_time = max(0, (dt_from - self.day_start_time).total_seconds() / 60)

        # Reposition and resize the draggable block
        self.draggable_block.move(self.draggable_block.x(), int(self.block_start_time * self.pixels_per_minute))
        self.draggable_block.setFixedHeight(int(self.duration_minutes * self.pixels_per_minute))

        # Update the time edits (blocking signals to avoid loops)
        self.from_time_edit.blockSignals(True)
        self.to_time_edit.blockSignals(True)
        self.from_time_edit.setTime(QTime(from_time.hour, from_time.minute))
        self.to_time_edit.setTime(QTime(to_time.hour, to_time.minute))
        self.from_time_edit.blockSignals(False)
        self.to_time_edit.blockSignals(False)


class SchedulePicker(QWidget):
    def __init__(self, color=None,
                 day_start_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)):
        super().__init__()
        self.day_start_time = day_start_time
        self.color = color
        self.duration_hours = 0
        self.from_time = self.day_start_time.time()  # Add this line
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.day_widgets = {}
        self.init_ui()

        self.initial_batched = True
        self.last_interacted_widget = None

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        duration_layout = QVBoxLayout()
        self.duration_label = QLabel("Duration: ")
        small_font = QFont()
        small_font.setPointSize(8)
        self.duration_label.setFont(small_font)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.duration_input = QTimeEdit()
        self.duration_input.setDisplayFormat("hh:mm")
        self.duration_input.timeChanged.connect(self.on_duration_changed)

        # Add label and input to vertical layout
        duration_layout.addWidget(self.duration_label)
        duration_layout.addWidget(self.duration_input)

        # Add duration layout to the top layout
        top_layout.addLayout(duration_layout)

        # Add quick buttons
        self.quick_buttons = [
            ("30 min", 0.5),
            ("1 hr", 1),
            ("2 hr", 2),
            ("3 hr", 3)
        ]
        for label, hrs in self.quick_buttons:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, h=hrs: self.set_quick_duration(h))
            btn.setFixedWidth(80)
            btn.setFixedHeight(30)
            top_layout.addWidget(btn)

        main_layout.addLayout(top_layout)

        self.all_days_checkbox = QCheckBox("All")
        self.all_days_checkbox.stateChanged.connect(self.on_all_days_checked)
        self.direct_click = True

        main_layout.addWidget(self.all_days_checkbox)

        days_layout = QHBoxLayout()
        for day in self.days:
            day_layout = QVBoxLayout()
            day_checkbox = QCheckBox(day)
            day_checkbox.stateChanged.connect(lambda state, d=day: self.toggle_day(d, state))
            day_layout.addWidget(day_checkbox)
            self.from_time_edit = QTimeEdit()
            self.to_time_edit = QTimeEdit()
            block_widget = DraggableBlockTimeScaleWidget(self, self.day_start_time, self.duration_hours, None,
                                                         self.color, from_time_edit=self.from_time_edit,
                                                         to_time_edit=self.to_time_edit)
            block_widget.setDisabled(True)
            day_layout.addWidget(block_widget)
            day_layout.addWidget(self.from_time_edit)
            day_layout.addWidget(self.to_time_edit)
            self.day_widgets[day] = {
                "checkbox": day_checkbox,
                "block_widget": block_widget
            }
            days_layout.addLayout(day_layout)
        main_layout.addLayout(days_layout)
        self.setLayout(main_layout)

    def on_duration_changed(self, time):
        total_minutes = time.hour() * 60 + time.minute()
        if total_minutes < 1:
            total_minutes = 1
        self.duration_hours = round(total_minutes / 60, 2)
        for day, widgets in self.day_widgets.items():
            widgets["block_widget"].update_duration(self.duration_hours)

    def set_quick_duration(self, hours):
        mins = int(hours * 60)
        if mins < 1:
            mins = 1
        self.duration_input.setTime(QTime(mins // 60, mins % 60))

    def toggle_day(self, day, state):
        widgets = self.day_widgets[day]
        is_enabled = (Qt.CheckState(state) == Qt.CheckState.Checked)
        if self.all_days_checkbox.isChecked() and not is_enabled:
            self.direct_click = False
            self.all_days_checkbox.setChecked(False)
        widgets["block_widget"].setDisabled(not is_enabled)

    def on_all_days_checked(self, state):
        if self.direct_click:
            if Qt.CheckState(state) == Qt.CheckState.Checked:
                for day, widgets in self.day_widgets.items():
                    widgets["checkbox"].setChecked(True)
            else:
                for day, widgets in self.day_widgets.items():
                    widgets["checkbox"].setChecked(False)
        else:
            self.direct_click = True

    def get_schedule(self):
        schedule = {}
        for day, widgets in self.day_widgets.items():
            checkbox = widgets["checkbox"]
            block_widget = widgets["block_widget"]

            if checkbox.isChecked():
                from_time = block_widget.get_from_time().time()
                to_time = block_widget.get_to_time().time()
                schedule[day.lower()] = (from_time, to_time)

        return schedule

    def refresh_color(self, color):
        css_color = f"rgb({color[0]}, {color[1]}, {color[2]})" if isinstance(color, tuple) else color
        for day, widgets in self.day_widgets.items():
            widgets["block_widget"].set_color(css_color)

    def sync(self, widget):
        if self.initial_batched and (self.last_interacted_widget is None or self.last_interacted_widget == widget):
            self.last_interacted_widget = widget
            for day, widgets in self.day_widgets.items():
                if widgets["block_widget"] != widget:
                    widgets["block_widget"].sync_with_widget(widget)
        else:
            self.initial_batched = False

    def set_day_schedule(self, day: str, from_time: time, to_time: time):
        """
        For a given day (e.g., "monday" in lowercase), update the corresponding draggable block
        with the provided from_time and to_time.
        """
        day = day.capitalize()
        if day in self.day_widgets:
            widgets = self.day_widgets[day]
            widgets["checkbox"].setChecked(True)
            widgets["block_widget"].setDisabled(False)
            widgets["block_widget"].set_schedule(from_time, to_time)


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
        self.category_items = []
        self.tag_items = []

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # Left side (Categories)
        cat_layout = QVBoxLayout()
        cat_label = QLabel("Task List Categories:")
        cat_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cat_label.setStyleSheet("font-weight: bold;")
        cat_layout.addWidget(cat_label)

        cat_grid = QGridLayout()
        cat_layout.addLayout(cat_grid)
        self._populate_grid(cat_grid, categories, self.category_items)

        # Left container
        cat_container = QWidget()
        cat_container.setLayout(cat_layout)
        cat_container.setMinimumWidth(200)

        # Center divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setFixedWidth(2)

        # Right side (Tags)
        tag_layout = QVBoxLayout()
        tag_label = QLabel("Task Tags:")
        tag_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tag_label.setStyleSheet("font-weight: bold;")
        tag_layout.addWidget(tag_label)

        tag_grid = QGridLayout()
        tag_layout.addLayout(tag_grid)
        self._populate_grid(tag_grid, tags, self.tag_items)

        # Right container
        tag_container = QWidget()
        tag_container.setLayout(tag_layout)
        tag_container.setMinimumWidth(200)

        main_layout.addWidget(cat_container, 1)
        main_layout.addWidget(divider)
        main_layout.addWidget(tag_container, 1)

    def _populate_grid(self, grid, items, item_list):
        max_columns = 3
        for idx, item in enumerate(items):
            row, col = divmod(idx, max_columns)
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


class AddTimeBlockDialog(QDialog):
    def __init__(self, parent=None, day_start_time=None):
        super().__init__(parent)
        self.setWindowTitle("Add Time Block")
        self.resize(500, 400)

        self.parent = parent
        self.day_start_time = day_start_time

        self.unavailable = False

        self.main_layout = QVBoxLayout(self)

        self.name_color_availability_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Time Block Name...")
        self.name_color_availability_layout.addWidget(self.name_input)
        self.picked_color = tuple(random.randint(0, 255) for _ in range(3))
        self.color_picker_button = QPushButton("Color Picker")
        self.color_picker_button.setStyleSheet(f"background-color: rgb{self.picked_color};")
        self.color_picker_button.clicked.connect(self.pick_color)
        self.name_color_availability_layout.addWidget(self.color_picker_button)
        self.unavailable_button = QPushButton("Unavailable")
        self.unavailable_button.clicked.connect(self.toggle_unavailable)
        self.name_color_availability_layout.addWidget(self.unavailable_button)

        self.main_layout.addLayout(self.name_color_availability_layout)

        self.schedule_picker = SchedulePicker(day_start_time=day_start_time, color=f"rgb{self.picked_color}")
        self.main_layout.addWidget(self.schedule_picker)

        categories = self.parent.schedule_manager.task_manager_instance.get_task_list_categories()
        tags = self.parent.schedule_manager.task_manager_instance.get_all_active_task_tags()
        self.category_tag_picker = CategoryTagPicker(categories, tags)
        self.main_layout.addWidget(self.category_tag_picker)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.picked_color = color.getRgb()[:3]
            self.color_picker_button.setStyleSheet(f"background-color: rgb{self.picked_color};")
            self.schedule_picker.refresh_color(self.picked_color)

    def toggle_unavailable(self):
        self.unavailable = not self.unavailable
        if self.unavailable:
            self.unavailable_button.setStyleSheet("background: rgb(204, 97, 65);")
        else:
            self.unavailable_button.setStyleSheet("background: none;")
        # self.schedule_picker.setDisabled(self.unavailable)
        self.category_tag_picker.setDisabled(self.unavailable)

    def get_time_block_data(self):
        name = self.name_input.text().strip()

        if self.unavailable:
            return {
                'unavailable': True,
                'name': name,
                'schedule': self.schedule_picker.get_schedule(),
                'color': self.picked_color
            }

        choices = self.category_tag_picker.get_choices()

        list_categories = choices['categories']
        task_tags = choices['tags']

        return {
            'unavailable': False,
            'name': name,
            'schedule': self.schedule_picker.get_schedule(),
            'list_categories': list_categories,
            'task_tags': task_tags,
            'color': self.picked_color
        }

    def validate_schedule(self, schedule):
        """
        Validates the schedule to ensure it contains valid time ranges.
        """
        for day, (from_time, to_time) in schedule.items():
            if from_time == to_time:
                return f"Invalid time range on {day.title()}: From {from_time} to {to_time}."
            if from_time > to_time:
                return f"Invalid time range on {day.title()}: From time ({from_time}) is after To time ({to_time})."
        return None

    def validate_and_accept(self):
        data = self.get_time_block_data()

        # Validate name
        if not data['name']:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return

        # Validate schedule
        if not data['schedule']:
            QMessageBox.warning(self, "Validation Error", "A schedule is required.")
            return

        # Validate schedule ranges
        schedule_error = self.validate_schedule(data['schedule'])
        if schedule_error:
            QMessageBox.warning(self, "Validation Error", schedule_error)
            return

        if not self.unavailable:

            # Validate categories or tags
            if not (data['list_categories']['include'] or data['task_tags']['include']):
                QMessageBox.warning(self, "Validation Error", "At least one tag or category is required.")
                return

        # If all validations pass
        self.accept()

    def edit_mode(self, block):
        # Set the name
        self.name_input.setText(block["name"])

        # Handle "unavailable" state
        self.unavailable = bool(block["unavailable"])
        if self.unavailable:
            self.unavailable_button.setStyleSheet("background: rgb(204, 97, 65);")
            self.category_tag_picker.setDisabled(True)
        else:
            self.unavailable_button.setStyleSheet("background: none;")
            self.category_tag_picker.setDisabled(False)

        # Set the color
        self.picked_color = block["color"]  # tuple like (r, g, b)
        self.color_picker_button.setStyleSheet(f"background-color: rgb{self.picked_color};")
        self.schedule_picker.refresh_color(self.picked_color)

        # Populate each day's schedule using the new set_day_schedule() helper.
        # Here we assume block["schedule"] is a dictionary with keys as day names in lowercase
        # and values as a tuple/list of two strings, e.g., ("09:00", "10:00").
        for day, widgets in self.schedule_picker.day_widgets.items():
            day = day.lower()
            if day in block["schedule"]:
                # Parse the stored strings into time objects
                from_str, to_str = block["schedule"][day]
                try:
                    from_time = datetime.strptime(from_str, "%H:%M").time()
                    to_time = datetime.strptime(to_str, "%H:%M").time()
                except Exception as e:
                    print(f"Error parsing time for {day}: {e}")
                    continue
                # Use the new helper to set this day's schedule
                self.schedule_picker.set_day_schedule(day, from_time, to_time)
            else:
                # If no schedule is stored for this day, uncheck and disable the widget.
                widgets["checkbox"].setChecked(False)
                widgets["block_widget"].setDisabled(True)
        if not self.unavailable:
            # Set categories and tags as before...
            for item in self.category_tag_picker.category_items:
                if item.text() in block["list_categories"]["include"]:
                    item._state = 1
                elif item.text() in block["list_categories"]["exclude"]:
                    item._state = 2
                else:
                    item._state = 0
                item._update_style()

            for item in self.category_tag_picker.tag_items:
                if item.text() in block["task_tags"]["include"]:
                    item._state = 1
                elif item.text() in block["task_tags"]["exclude"]:
                    item._state = 2
                else:
                    item._state = 0
                item._update_style()
