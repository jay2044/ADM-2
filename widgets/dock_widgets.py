from .task_widgets import *
from .toolbar_widgets import *
from .container_widgets import *
from .input_widgets import *
from .schedule_widgets import *


class TaskDetailDock(QDockWidget):
    def __init__(self, task, task_list_widget, parent=None):
        super().__init__(parent)

        self.setWindowTitle(task.name)

        # main window
        self.parent = parent

        self.task = task
        self.task_list_widget = task_list_widget
        self.is_edit_mode = False

        self.set_allowed_areas()
        self.setup_ui()
        self.display_task_details()
        self.setup_due_date_display()
        self.installEventFilter(self)

    def closeEvent(self, event):
        self.deleteLater()
        super().closeEvent(event)

    def set_allowed_areas(self):
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                         QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                         QDockWidget.DockWidgetFeature.DockWidgetClosable)

    def setup_ui(self):
        self.widget = QWidget()
        self.setWidget(self.widget)
        # Main layout for the dialog
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.widget.setLayout(self.main_layout)

        # Container widget for the content
        self.content_widget = QWidget()
        self.main_layout.addWidget(self.content_widget)

        # Layout for the content widget
        self.content_layout = QVBoxLayout(self.content_widget)

        self.content_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # Header Layout: Task Name, Due Date, Edit, and Close Buttons
        self.header_layout = QHBoxLayout()

        # Initialize the Task Name Label as a QLabel initially
        self.task_name_label = QLabel()
        self.task_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.task_name_label.setText(self.task.name)
        self.task_name_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.task_name_label.mousePressEvent = self.edit_task_name
        self.header_layout.addWidget(self.task_name_label)

        # Due Date Label
        self.due_date_label = QLabel()
        self.due_date_label.setStyleSheet("font-size: 14px; color: gray;")
        self.due_date_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.due_date_label.mousePressEvent = self.open_due_date_picker
        self.header_layout.addWidget(self.due_date_label)

        if self.task.count_required or self.task.time_estimate or self.task.subtasks:
            self.progress_bar = TaskProgressBar(self.task)
            self.header_layout.addWidget(self.progress_bar)
        else:
            self.header_layout.addStretch()
            self.progress_bar = None

        # Edit Button
        self.edit_button = QPushButton("Edit")
        self.edit_button.setFixedSize(60, 24)
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        self.header_layout.addWidget(self.edit_button)

        # Close Button
        self.close_button = QPushButton("Close")
        self.close_button.setFixedSize(60, 24)
        self.close_button.clicked.connect(self.close)
        self.header_layout.addWidget(self.close_button)

        self.content_layout.addLayout(self.header_layout)

        # Separator Line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.content_layout.addWidget(separator)

        # Task Details Area with white background and reduced spacing
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_layout.setSpacing(2)  # Adjust spacing between widgets

        self.details_widget.setLayout(self.details_layout)
        self.content_layout.addWidget(self.details_widget)

        # Buttons Layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addStretch()

        # Save and Cancel Buttons (only in edit mode)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_task_edits)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_edits)

        # Add buttons to the buttons_layout
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)

        # Initially hide the buttons
        self.save_button.hide()
        self.cancel_button.hide()

        # Add the buttons_layout to the main_layout
        self.main_layout.addLayout(self.buttons_layout)

    def display_task_details(self):
        # Clear existing widgets
        self.clear_layout(self.details_layout)
        self.details_layout.setContentsMargins(0, 0, 0, 0)

        # Update task name
        self.task_name_label.setText(self.task.name)

        # If task is recurring, show when it is recurring
        if self.task.recurring:
            recurring_list = self.task.recur_every
            if all(isinstance(item, str) for item in recurring_list):
                # Convert each item in the list to a string before joining
                str_recurring_list = ", ".join(map(str, recurring_list))
                str_recurring_list = "Due every " + str_recurring_list
            else:
                str_recurring_list = str(recurring_list[0])

                if self.task.last_completed_date is not None:
                    days_due_in = (self.task.last_completed_date + timedelta(
                        days=int(recurring_list[0])) - datetime.now()).days
                    str_recurring_list = f"Due every {str_recurring_list} days, next in {days_due_in} days."
                else:
                    str_recurring_list = f"Due every {str_recurring_list} days."

            recurring_label = QLabel(str_recurring_list)
            recurring_label.setStyleSheet("font-size: 12px; color: gray;")
            recurring_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            self.details_layout.addWidget(recurring_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.dropdowns = TaskDropdownsWidget(task=self.task, parent=self)
        self.dropdowns.connect_dropdown_signals(
            lambda value: self.update_task_attribute('status', value),
            lambda value: self.update_task_attribute('flexibility', value),
            lambda value: self.update_task_attribute('effort_level', value)
        )
        self.details_layout.addWidget(self.dropdowns)

        # Check if task has a description
        if self.task.description:
            description_container = DescriptionContainer(self.task.description)
            self.details_layout.addWidget(description_container, stretch=0)

        sub_task_window = SubtaskWindow(self.task, parent=self)
        self.details_layout.addWidget(sub_task_window)

        # Resources
        self.resources_widget = ResourcesWidget(self.task, self.task_list_widget, parent=self)
        self.details_layout.addWidget(self.resources_widget)

        # Progress Bar for Count
        # Progress Bar for Count
        if self.task.count_required > 0:
            progress_bar = CountProgressWidget(task=self.task, task_list_widget=self.task_list_widget, parent=self)
            self.details_layout.addWidget(progress_bar)

        # Progress Bar for Time Logged
        if self.task.time_estimate > 0:
            time_bar = TimeProgressWidget(task=self.task, task_list_widget=self.task_list_widget, parent=self)
            self.details_layout.addWidget(time_bar)

        # Notes
        if self.task.notes:
            notes_label = QLabel("Note:")
            notes_label.setStyleSheet("font-weight: bold;")
            self.details_layout.addWidget(notes_label)
            notes_content = QLabel(self.task.notes)
            notes_content.setWordWrap(True)
            self.details_layout.addWidget(notes_content)

        # Create the tag layout
        tag_layout = QHBoxLayout()
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(5)  # Adds spacing between tags
        tag_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align tags within the layout

        # Set up the tag widget
        tag_widget = QWidget()
        tag_widget.setLayout(tag_layout)
        tag_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Allow the widget to expand

        # Style each tag label with centered alignment, shadow, translucent background, and inverted text color
        for tag in self.task.tags:
            tag_label = QLabel(f"{tag} ")
            tag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align text within the label

            # Add shadow effect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setOffset(2, 2)
            shadow.setColor(QColor(0, 0, 0, 120))  # Light shadow with some transparency
            tag_label.setGraphicsEffect(shadow)

            # Translucent background color with inverted text color
            tag_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(211, 211, 211, 0.8);  /* Light gray with 80% opacity */
                    color: black;  /* Inverted text color for better contrast on light background */
                    border-radius: 10px;
                    padding: 5px 10px;
                }
            """)

            # Add the styled label to the layout
            tag_layout.addWidget(tag_label)

        # Add the tag widget to the main layout with center alignment
        self.details_layout.addWidget(tag_widget, alignment=Qt.AlignmentFlag.AlignCenter)

    def update_task_attribute(self, attribute, value):
        self.task.set_attribute(attribute, value)
        self.parent.task_manager.update_task(self.task)
        global_signals.task_list_updated.emit()

    def edit_task_name(self, event):
        # Replace QLabel with QLineEdit for editing
        self.task_name_edit = QLineEdit(self.task_name_label.text())
        self.task_name_edit.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.task_name_edit.setFocus()
        self.task_name_edit.selectAll()

        # Connect both finishing events for saving
        self.task_name_edit.editingFinished.connect(self.finish_editing_task_name)
        self.header_layout.replaceWidget(self.task_name_label, self.task_name_edit)
        self.task_name_label.hide()

    def finish_editing_task_name(self):
        # Update task title with the new text and replace QLineEdit with QLabel
        self.task.name = self.task_name_edit.text()  # Update task with new name
        self.task_name_label.setText(self.task.name)

        # Replace QLineEdit back with QLabel
        self.header_layout.replaceWidget(self.task_name_edit, self.task_name_label)
        self.task_name_edit.deleteLater()  # Clean up QLineEdit
        self.task_name_label.show()
        global_signals.task_list_updated.emit()

    def keyPressEvent(self, event, **kwargs):
        try:
            # Check if Enter was pressed to finish editing
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                focus_widget = self.focusWidget()
                # If the focused widget is a QLineEdit, finish editing
                if isinstance(focus_widget, QLineEdit):
                    focus_widget.clearFocus()
                    event.accept()
                else:
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        except Exception as e:
            print(f"Error in keyPressEvent: {e}")

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            try:
                if hasattr(self, 'task_name_edit') and self.task_name_edit.isVisible():
                    if not self.task_name_edit.geometry().contains(event.pos()):
                        self.finish_editing_task_name()
                        return True
            except RuntimeError:
                pass
        return super().eventFilter(source, event)

    def setup_due_date_display(self):
        """
        Displays the task's due date/time in self.due_date_label
        based on the single self.task.due_datetime attribute.
        """
        if not self.task.due_datetime:
            self.due_date_label.setText("")  # No due date set
            return

        # Convert Python datetime to QDateTime
        qdt = QDateTime(
            self.task.due_datetime.year,
            self.task.due_datetime.month,
            self.task.due_datetime.day,
            self.task.due_datetime.hour,
            self.task.due_datetime.minute,
        )

        # Calculate how many days until due
        today = QDate.currentDate()
        days_to_due = today.daysTo(qdt.date())

        # Simple formatting examples
        if days_to_due == 0:
            self.due_date_label.setText("due today")
        elif days_to_due > 0 and days_to_due <= 7:
            # Show day of week if within 7 days
            self.due_date_label.setText(qdt.date().toString("ddd h:mm AP"))
        else:
            # Show date plus year if it differs
            display_str = qdt.date().toString("dd MMM")
            if qdt.date().year() != today.year():
                display_str += f" {qdt.date().year()}"
            display_str += " " + qdt.time().toString("h:mm AP")
            self.due_date_label.setText(display_str)

    def open_due_date_picker(self, event):
        """
        Opens a dialog with a QCalendarWidget for selecting the date
        and a QTimeEdit for setting the time.
        """
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(dialog)
        dialog.setLayout(layout)

        # Calendar for date selection
        calendar = QCalendarWidget(dialog)
        if self.task.due_datetime:
            calendar.setSelectedDate(self.task.due_datetime.date())
        layout.addWidget(calendar)

        # Time selection
        time_edit = QTimeEdit(dialog)
        time_edit.setDisplayFormat("h:mm AP")
        if self.task.due_datetime:
            time_edit.setTime(self.task.due_datetime.time())
        else:
            time_edit.setTime(QTime(0, 0))  # Default to midnight
        layout.addWidget(time_edit)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", dialog)
        ok_button.clicked.connect(
            lambda: self.set_task_due_datetime(calendar.selectedDate(), time_edit.time(), dialog)
        )
        button_layout.addWidget(ok_button)

        clear_button = QPushButton("Clear", dialog)
        clear_button.clicked.connect(lambda: self.clear_due_datetime(dialog))
        button_layout.addWidget(clear_button)

        layout.addLayout(button_layout)

        # Position the dialog near the label
        label_pos = self.due_date_label.mapToGlobal(
            QPoint(self.due_date_label.width() // 2, self.due_date_label.height() // 2)
        )
        dialog.move(label_pos - QPoint(dialog.width() // 2, dialog.height() // 2))

        dialog.exec()

    def set_task_due_datetime(self, qdate, qtime, dialog):
        """
        Sets the task's due_datetime using the selected QDate and QTime.
        """
        self.task.due_datetime = datetime(
            qdate.year(), qdate.month(), qdate.day(), qtime.hour(), qtime.minute()
        )
        self.parent.task_manager.update_task(self.task)
        self.setup_due_date_display()
        dialog.accept()

    def clear_due_datetime(self, dialog):
        """
        Clears the task's due_datetime (sets it to None).
        """
        self.task.due_datetime = None
        self.parent.task_manager.update_task(self.task)
        self.setup_due_date_display()
        dialog.accept()

    def toggle_edit_mode(self):
        if self.is_edit_mode:
            # Already in edit mode, do nothing
            return
        else:
            self.is_edit_mode = True
            self.edit_button.hide()
            self.switch_to_edit_mode()

    def add_labeled_widget(self, label_text, widget):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addWidget(widget)
        self.details_layout.addLayout(layout)

    def switch_to_edit_mode(self):
        # Clear existing widgets
        self.clear_layout(self.details_layout)

        # Editable Task Name
        self.task_name_edit = QLineEdit(self.task.name)
        self.header_layout.replaceWidget(self.task_name_label, self.task_name_edit)
        self.task_name_label.hide()

        # Description
        self.description_edit = QTextEdit(self.task.description)
        self.add_labeled_widget("Description:", self.description_edit)

        # Priority
        self.priority_spinbox = QSpinBox()
        self.priority_spinbox.setRange(0, 10)
        self.priority_spinbox.setValue(self.task.priority)
        self.add_labeled_widget("Priority:", self.priority_spinbox)

        # Categories
        self.categories_input = TagInputWidget(
            self.task_list_widget.task_list.get_task_tags(), self.task.tags)
        self.add_labeled_widget("Categories:", self.categories_input)

        # Recurring
        self.recurring_checkbox = QCheckBox("Recurring", self)
        self.details_layout.addWidget(self.recurring_checkbox)

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

        self.specific_weekdays_layout.setSpacing(0)
        self.specific_weekdays_layout.setContentsMargins(0, 0, 0, 0)

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
        if not self.task.recurring:
            self.every_n_days_widget.hide()
            self.specific_weekdays_widget.hide()
            self.recurrence_options_widget.hide()
        else:
            self.recurring_checkbox.setChecked(self.task.recurring)
            if isinstance(self.task.recur_every, list) and len(self.task.recur_every) == 1 and isinstance(
                    self.task.recur_every[0], int):
                # Set "Every N days" option
                self.every_n_days_radio.setChecked(True)
                self.every_n_days_spinbox.setValue(self.task.recur_every[0])
                self.update_recurrence_detail_widgets()
            elif isinstance(self.task.recur_every, list) and all(isinstance(day, str) for day in self.task.recur_every):
                # Set specific weekdays
                self.specific_weekdays_radio.setChecked(True)
                for checkbox in self.weekday_checkboxes:
                    if checkbox.text() in self.task.recur_every:
                        checkbox.setChecked(True)
                self.update_recurrence_detail_widgets()

        # Add recurrence options to basic layout
        self.details_layout.addWidget(self.recurrence_options_widget)

        # Connect signals
        self.recurring_checkbox.stateChanged.connect(self.toggle_recurrence_options)
        self.every_n_days_radio.toggled.connect(self.update_recurrence_detail_widgets)
        self.specific_weekdays_radio.toggled.connect(self.update_recurrence_detail_widgets)

        # Estimate
        self.estimate_spinbox = QDoubleSpinBox()
        self.estimate_spinbox.setRange(0, 10000)
        self.estimate_spinbox.setDecimals(2)
        self.estimate_spinbox.setValue(self.task.time_estimate)
        self.add_labeled_widget("Estimate (hours):", self.estimate_spinbox)

        # Time Logged
        self.time_logged_spinbox = QDoubleSpinBox()
        self.time_logged_spinbox.setRange(0, 10000)
        self.time_logged_spinbox.setDecimals(2)
        self.time_logged_spinbox.setValue(self.task.time_logged)
        self.add_labeled_widget("Time Logged (hours):", self.time_logged_spinbox)

        # Count Required
        self.count_required_spinbox = QSpinBox()
        self.count_required_spinbox.setRange(0, 1000)
        self.count_required_spinbox.setValue(self.task.count_required)
        self.add_labeled_widget("Count Required:", self.count_required_spinbox)

        # Count Completed (Initialized with current count)
        self.count_completed_spinbox = QSpinBox()
        self.count_completed_spinbox.setRange(0, 1000)
        self.count_completed_spinbox.setValue(self.task.count_completed)
        self.add_labeled_widget("Count Completed:", self.count_completed_spinbox)

        # Notes
        self.notes_edit = QTextEdit(self.task.notes)
        self.add_labeled_widget("Notes:", self.notes_edit)

        # Show Save and Cancel buttons
        self.save_button.show()
        self.cancel_button.show()

    def save_task_edits(self):
        # Validate title
        try:
            title = self.task_name_edit.text().strip()
            if not title:
                QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
                return
            # Update task attributes
            self.task.name = name
        except Exception as e:
            print(e)

        # Update other task attributes
        self.task.description = self.description_edit.toPlainText()
        self.task.priority = self.priority_spinbox.value()
        self.task.tags = self.categories_input.get_tags()
        self.task.recurring = self.recurring_checkbox.isChecked()

        # Recur Every
        if self.recurring_checkbox.isChecked():
            if self.every_n_days_radio.isChecked():
                self.task.recur_every = [int(self.every_n_days_spinbox.value())]
            elif self.specific_weekdays_radio.isChecked():
                selected_weekdays = []
                for checkbox in self.weekday_checkboxes:
                    if checkbox.isChecked():
                        selected_weekdays.append(checkbox.text())
                self.task.recur_every = selected_weekdays
        else:
            self.task.recur_every = None

        self.task.time_estimate = self.estimate_spinbox.value()
        self.task.time_logged = self.time_logged_spinbox.value()
        self.task.count_required = self.count_required_spinbox.value()
        self.task.count_completed = self.count_completed_spinbox.value()
        self.task.notes = self.notes_edit.toPlainText()

        # Update task and refresh UI
        self.parent.task_manager.update_task(self.task)
        global_signals.task_list_updated.emit()
        self.exit_edit_mode()

    def cancel_edits(self):
        # Exit edit mode without saving changes
        self.exit_edit_mode()

    def exit_edit_mode(self):
        self.is_edit_mode = False
        self.edit_button.show()
        try:
            # Replace QLineEdit with QLabel for task name
            self.header_layout.replaceWidget(self.task_name_edit, self.task_name_label)
            self.task_name_edit.deleteLater()
            self.task_name_label.show()
        except Exception as e:
            print(e)

        # Hide the Save and Cancel buttons
        self.save_button.hide()
        self.cancel_button.hide()

        # Refresh the task details view
        self.display_task_details()

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

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout(item.layout())


class NavigationSidebarDock(QDockWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)
        self.parent = parent
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)

        self.setup_ui()

    def setup_ui(self):
        self.widget = QWidget()
        self.widget.setObjectName("widget")
        self.layout = QVBoxLayout()
        self.layout.setObjectName("leftLayout")
        self.widget.setLayout(self.layout)

        self.setWidget(self.widget)

        self.widget.setFixedWidth(200)

        self.task_list_collection = TaskListCollection(self.parent)
        self.task_list_collection.setObjectName("taskListCollection")
        self.left_top_toolbar = TaskListManagerToolbar(self)
        self.left_top_toolbar.setObjectName("leftTopToolbar")
        self.layout.addWidget(self.left_top_toolbar)
        self.layout.addWidget(self.task_list_collection)
        self.info_bar = InfoBar(self.parent)
        self.info_bar.setObjectName("infoBar")
        self.layout.addWidget(self.info_bar)
        self.layout.setContentsMargins(0, 0, 0, 0)


class TaskListDockStacked(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Tasks", parent)
        self.type = "stack"
        self.priority_filter = False
        self.multi_select_mode_toggle_bool = False
        self.moving = False
        self.parent = parent
        self.task_manager = self.parent.task_manager
        self.set_allowed_areas()
        self.setup_ui()
        self.setObjectName("taskListDockStacked")
        self.toolbar.setObjectName("taskListToolbar")
        self.stack_widget.setObjectName("stackWidget")

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Monitor focus changes and handle multi-select mode toggling.
        """
        if event.type() == QEvent.Type.FocusOut and self.multi_select_mode_toggle_bool:
            print("FocusOut detected by event filter.")
            if not self.isAncestorOf(QApplication.focusWidget()) and not self.underMouse():
                print("Focus moved outside TaskListDockStacked. Exiting multi-select mode.")
                self.toggle_multi_select()
                return True
        return super().eventFilter(obj, event)

    def filter_current_task_list(self, text):
        current_task_list_widget = self.get_current_task_list_widget()
        if current_task_list_widget:
            current_task_list_widget.filter_tasks(text)

    def show_task_list(self, task_list_name):
        hash_key = hash(task_list_name)
        if hash_key in self.parent.hash_to_task_list_widgets:
            task_list_widget = self.parent.hash_to_task_list_widgets[hash_key]
            self.stack_widget.setCurrentWidget(task_list_widget)
            self.update_toolbar()
            search_text = self.parent.navigation_sidebar_dock.task_list_collection.search_bar.text()
            task_list_widget.filter_tasks(search_text)

    def set_allowed_areas(self):
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

    def setup_ui(self):
        self.widget = QWidget()
        self.widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWidget(self.widget)
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.setup_toolbar()
        self.setup_stack_widget()

    def setup_toolbar(self):
        self.toolbar = TaskListToolbar(self)
        self.layout.addWidget(self.toolbar)

    def update_toolbar(self):
        try:
            current_task_list_widget = self.stack_widget.currentWidget()
            current_task_list = current_task_list_widget.task_list
            self.toolbar.actions()[1].setCheckable(True)
            self.toolbar.actions()[1].setChecked(current_task_list.sort_by_queue)
            self.toolbar.actions()[2].setCheckable(True)
            self.toolbar.actions()[2].setChecked(current_task_list.sort_by_stack)
            self.toolbar.actions()[3].setCheckable(True)
            self.toolbar.actions()[3].setChecked(current_task_list.sort_by_priority)
        except Exception as e:
            print(e)

    def setup_stack_widget(self):
        self.stack_widget = QStackedWidget()
        self.layout.addWidget(self.stack_widget)

    def add_task(self):
        current_task_list_widget = self.get_current_task_list_widget()
        self.show_add_task_dialog(current_task_list_widget)

    def show_add_task_dialog(self, task_list_widget):
        # try:
        dialog = AddTaskDialog(self, task_list_widget)
        button_pos = self.toolbar.mapToGlobal(self.toolbar.rect().bottomRight())
        dialog.adjustSize()
        dialog.move(button_pos.x() - dialog.width(), button_pos.y())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            task = Task(**task_data)
            self.task_manager.add_task(task)
            global_signals.task_list_updated.emit()
        # except Exception as e:
        #     print(f"An error occurred while adding a task: {e}")

    def set_queue(self):
        try:
            current_task_list_widget = self.stack_widget.currentWidget()
            if not isinstance(current_task_list_widget, TaskListWidget):
                return
            current_task_list = current_task_list_widget.task_list
            current_task_list.sort_by_queue = not current_task_list.sort_by_queue
            if current_task_list.sort_by_stack:
                current_task_list.sort_by_stack = False
            self.toolbar.actions()[1].setCheckable(True if current_task_list.sort_by_queue else False)
            self.toolbar.actions()[1].setChecked(current_task_list.sort_by_queue)
            self.toolbar.actions()[2].setCheckable(False)
            self.toolbar.actions()[3].setCheckable(False)
            self.priority_filter = False
            current_task_list_widget.load_tasks()
            self.task_manager.update_task_list(current_task_list)
        except Exception as e:
            print(f"Error in set_queue: {e}")

    def set_stack(self):
        try:
            current_task_list_widget = self.stack_widget.currentWidget()
            if not isinstance(current_task_list_widget, TaskListWidget):
                return
            current_task_list = current_task_list_widget.task_list
            current_task_list.sort_by_stack = not current_task_list.sort_by_stack
            if current_task_list.sort_by_queue:
                current_task_list.sort_by_queue = False
            self.toolbar.actions()[2].setCheckable(True if current_task_list.sort_by_stack else False)
            self.toolbar.actions()[2].setChecked(current_task_list.sort_by_stack)
            self.toolbar.actions()[1].setCheckable(False)
            self.toolbar.actions()[3].setCheckable(False)
            self.priority_filter = False
            current_task_list.sort_by_queue = False
            current_task_list_widget.load_tasks()
            self.task_manager.update_task_list(current_task_list)
        except Exception as e:
            print(f"Error in set_stack: {e}")

    def priority_sort(self):
        try:
            current_task_list_widget = self.stack_widget.currentWidget()
            if not isinstance(current_task_list_widget, TaskListWidget):
                return
            current_task_list = current_task_list_widget.task_list

            # Toggle the priority filter
            self.priority_filter = not self.priority_filter
            current_task_list.sort_by_priority = self.priority_filter

            # Update toolbar states
            self.toolbar.actions()[3].setCheckable(self.priority_filter)
            self.toolbar.actions()[3].setChecked(self.priority_filter)

            # Ensure other sorting options are disabled
            current_task_list.sort_by_stack = False
            current_task_list.sort_by_queue = False
            self.toolbar.actions()[2].setCheckable(False)
            self.toolbar.actions()[2].setChecked(False)
            self.toolbar.actions()[1].setCheckable(False)
            self.toolbar.actions()[1].setChecked(False)

            # Reload tasks in the current task list widget
            current_task_list_widget.load_tasks()

            # Update the backend with the new sorting state
            self.task_manager.update_task_list(current_task_list)

        except Exception as e:
            print(f"Error in priority_sort: {e}")

    def toggle_multi_select(self):
        current_task_list_widget = self.get_current_task_list_widget()

        if not current_task_list_widget or current_task_list_widget.count() == 0:
            if not self.multi_select_mode_toggle_bool:
                print("No tasks available or invalid task list widget.")
                self.multi_select_mode_toggle_bool = False
                self.toolbar.actions()[4].setCheckable(False)
                self.toolbar.actions()[4].setChecked(False)
                return

        self.multi_select_mode_toggle_bool = not self.multi_select_mode_toggle_bool
        print(f"Multi-select mode toggled: {self.multi_select_mode_toggle_bool}")  # Debug

        self.toolbar.actions()[4].setCheckable(self.multi_select_mode_toggle_bool)
        self.toolbar.actions()[4].setChecked(self.multi_select_mode_toggle_bool)

        if self.multi_select_mode_toggle_bool:
            self.multi_selection_tool_bar = QToolBar(self)
            self.multi_selection_tool_bar.addAction("Select All", current_task_list_widget.select_all_items)
            self.multi_selection_tool_bar.addAction("Clear Selection",
                                                    current_task_list_widget.clear_selection_all_items)
            self.multi_selection_tool_bar.addAction("Delete", current_task_list_widget.delete_selected_items)
            self.multi_selection_tool_bar.addAction("Move To", self.move_action)

            self.layout.insertWidget(1, self.multi_selection_tool_bar)
            current_task_list_widget.multi_selection_mode()
        else:
            if hasattr(self, "multi_selection_tool_bar"):
                self.multi_selection_tool_bar.hide()
            current_task_list_widget.load_tasks()  # Ensure tasks reload in normal mode
            global_signals.task_list_updated.emit()

    def move_action(self):
        self.moving = True
        self.get_current_task_list_widget().move_selected_items()
        self.moving = False

    def focusOutEvent(self, event):
        """
        Handle focus out event for TaskListDockStacked.
        """
        super().focusOutEvent(event)
        print("TaskListDockStacked lost focus")

        # Prevent exiting multi-select when clicking inside the widget or on its child widgets
        if self.multi_select_mode_toggle_bool:
            if self.underMouse():
                print("Focus still within widget or child. Ignoring focus out.")
                return

            if not self.isAncestorOf(QApplication.focusWidget()):
                print("Focus moved outside TaskListDockStacked. Exiting multi-select mode.")
                self.toggle_multi_select()

    def get_current_task_list_widget(self):
        current_widget = self.stack_widget.currentWidget()
        return current_widget if isinstance(current_widget, TaskListWidget) else None

    def get_task_list_widget_by_task(self, task_id):
        """
        Finds the TaskListWidget containing a task with the specified task_id.

        :param task_id: The ID of the task to find.
        :return: The TaskListWidget containing the task, or None if not found.
        """
        for i in range(self.stack_widget.count()):
            task_list_widget = self.stack_widget.widget(i)
            if isinstance(task_list_widget, TaskListWidget):
                task_list = task_list_widget.task_list
                if any(task.id == task_id for task in task_list.tasks):
                    return task_list_widget
        return None


class TaskListDock(QDockWidget):
    def __init__(self, task_list_name, parent=None):
        super().__init__(task_list_name, parent)
        self.type = "dock"
        self.parent = parent
        self.task_manager = self.parent.task_manager
        self.task_list_name = task_list_name
        self.setWindowTitle(task_list_name)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFloating(True)
        self.setMouseTracking(True)
        self.dragging = False

        self.multi_select_mode_toggle_bool = False
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        task_list = next((tl for tl in self.task_manager.task_lists if tl.name == task_list_name), None)
        self.task_list_widget = TaskListWidget(task_list, self.parent)
        self.priority_filter = False
        self.set_allowed_areas()
        self.setup_ui()

        self.setObjectName(f"TaskListDock_{self.task_list_name}")
        self.toolbar.setObjectName("taskListToolbarDock")
        self.task_list_widget.setObjectName("taskListWidgetDock")

    def set_allowed_areas(self):
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                         QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                         QDockWidget.DockWidgetFeature.DockWidgetClosable)

    def setup_ui(self):
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.setup_toolbar()
        self.layout.addWidget(self.task_list_widget)

    def closeEvent(self, event):
        self.deleteLater()
        super().closeEvent(event)

    def setup_toolbar(self):
        self.toolbar = TaskListToolbar(self)
        self.layout.addWidget(self.toolbar)

    def add_task(self):
        self.show_add_task_dialog(self.task_list_widget)

    def show_add_task_dialog(self, task_list_widget):
        dialog = AddTaskDialog(self, task_list_widget)
        button_pos = self.toolbar.mapToGlobal(self.toolbar.rect().bottomRight())
        dialog.adjustSize()
        dialog.move(button_pos.x() - dialog.width(), button_pos.y())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            task = Task(**task_data)
            self.task_manager.add_task(task)
            global_signals.task_list_updated.emit()

    def set_queue(self):
        try:
            task_list = self.task_list_widget.task_list
            task_list.sort_by_queue = not task_list.sort_by_queue
            self.toolbar.actions()[1].setCheckable(task_list.sort_by_queue)
            self.toolbar.actions()[1].setChecked(task_list.sort_by_queue)
            task_list.sort_by_stack = False
            self.toolbar.actions()[2].setCheckable(False)
            self.toolbar.actions()[3].setCheckable(False)
            self.priority_filter = False
            self.task_list_widget.load_tasks()
            self.task_manager.update_task_list(task_list)
        except Exception as e:
            print(f"Error in set_queue: {e}")

    def set_stack(self):
        try:
            task_list = self.task_list_widget.task_list
            task_list.sort_by_stack = not task_list.sort_by_stack
            self.toolbar.actions()[2].setCheckable(task_list.sort_by_stack)
            self.toolbar.actions()[2].setChecked(task_list.sort_by_stack)
            self.toolbar.actions()[1].setCheckable(False)
            self.toolbar.actions()[3].setCheckable(False)
            self.priority_filter = False
            task_list.sort_by_queue = False
            self.task_list_widget.load_tasks()
            self.task_manager.update_task_list(task_list)
        except Exception as e:
            print(f"Error in set_stack: {e}")

    def priority_sort(self):
        try:
            task_list = self.task_list_widget.task_list
            task_list.sort_by_priority = not task_list.sort_by_priority
            self.toolbar.actions()[3].setCheckable(not self.priority_filter)
            self.toolbar.actions()[3].setChecked(not self.priority_filter)
            self.toolbar.actions()[2].setCheckable(False)
            self.toolbar.actions()[1].setCheckable(False)
            self.priority_filter = not self.priority_filter
            self.task_list_widget.load_tasks()
            self.task_manager.update_task_list(task_list)
        except Exception as e:
            print(f"Error in priority_sort: {e}")

    def start_drag(self):
        self.dragging = True
        self.grabMouse()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - QPoint(self.width() // 2, self.height() // 2))

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.releaseMouse()

    def toggle_multi_select(self):
        current_task_list_widget = self.task_list_widget

        if not current_task_list_widget or current_task_list_widget.count() == 0:
            if not self.multi_select_mode_toggle_bool:
                print("No tasks available or invalid task list widget.")
                self.multi_select_mode_toggle_bool = False
                self.toolbar.actions()[4].setCheckable(False)
                self.toolbar.actions()[4].setChecked(False)
                return

        self.multi_select_mode_toggle_bool = not self.multi_select_mode_toggle_bool
        self.toolbar.actions()[4].setCheckable(True if self.multi_select_mode_toggle_bool else False)
        self.toolbar.actions()[4].setChecked(True if self.multi_select_mode_toggle_bool else False)

        if self.multi_select_mode_toggle_bool:
            self.multi_selection_tool_bar = QToolBar(self)
            self.multi_selection_tool_bar.addAction("Select All", current_task_list_widget.select_all_items)
            self.multi_selection_tool_bar.addAction("Clear Selection",
                                                    current_task_list_widget.clear_selection_all_items)
            self.multi_selection_tool_bar.addAction("Delete", current_task_list_widget.delete_selected_items)
            self.multi_selection_tool_bar.addAction("Move To", self.move_action)

            self.layout.insertWidget(1, self.multi_selection_tool_bar)
            current_task_list_widget.multi_selection_mode()
        else:
            if hasattr(self, "multi_selection_tool_bar"):
                self.multi_selection_tool_bar.hide()
            current_task_list_widget.load_tasks()
            global_signals.task_list_updated.emit()

    def move_action(self):
        self.moving = True
        self.task_list_widget.move_selected_items()
        self.moving = False

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        print("TaskListDock lost focus")
        if self.multi_select_mode_toggle_bool and not self.moving:
            self.toggle_multi_select()


class HistoryDock(QDockWidget):
    def __init__(self, parent):
        super().__init__("History", parent)
        self.parent = parent
        self.set_allowed_areas()
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search completed tasks...")
        self.search_bar.textChanged.connect(self.update_history)
        self.history_layout.addWidget(self.search_bar)

        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Task", "Completed On", "Due Date", "Priority"])
        self.history_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_tree.itemDoubleClicked.connect(self.view_task_details)

        self.history_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_tree.customContextMenuRequested.connect(self.show_context_menu)

        self.history_layout.addWidget(self.history_tree)
        self.setWidget(self.history_widget)

        self.setObjectName("historyDock")
        self.search_bar.setObjectName("historySearchBar")
        self.history_tree.setObjectName("historyTree")

        global_signals.task_list_updated.connect(self.update_history)
        self.update_history()

    def set_allowed_areas(self):
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                         QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                         QDockWidget.DockWidgetFeature.DockWidgetClosable)

    def toggle_history(self):
        self.setVisible(not self.isVisible())
        if self.isVisible():
            self.update_history()

    def update_history(self):
        self.history_tree.clear()
        search_text = self.search_bar.text().lower()

        for task_list in self.parent.task_manager.task_lists:
            completed_tasks = [task for task in task_list.tasks if task.status == "Completed"]

            if search_text:
                completed_tasks = [task for task in completed_tasks if search_text in task.name.lower() or
                                   search_text in (task.description.lower() if task.description else "")]

            if completed_tasks:
                task_list_item = QTreeWidgetItem(self.history_tree)
                task_list_item.setText(0, task_list.name)
                task_list_item.setFirstColumnSpanned(True)
                self.history_tree.addTopLevelItem(task_list_item)

                tasks_by_date = {}
                for task in completed_tasks:
                    completed_date = task.last_completed_date.strftime(
                        '%Y-%m-%d') if task.last_completed_date else 'Unknown'
                    if completed_date not in tasks_by_date:
                        tasks_by_date[completed_date] = []
                    tasks_by_date[completed_date].append(task)

                for date, tasks in sorted(tasks_by_date.items(), reverse=True):
                    date_item = QTreeWidgetItem(task_list_item)
                    date_item.setText(0, f"Completed on {date}")
                    date_item.setFirstColumnSpanned(True)
                    task_list_item.addChild(date_item)

                    for task in tasks:
                        task_item = QTreeWidgetItem(date_item)
                        task_item.setText(0, task.name)
                        task_item.setText(1, task.last_completed_date.strftime(
                            '%Y-%m-%d %H:%M') if task.last_completed_date else '')
                        task_item.setText(2, task.due_datetime.strftime('%Y-%m-%d %H:%M') if task.due_datetime else '')
                        task_item.setText(3, str(task.priority))
                        task_item.setData(0, Qt.ItemDataRole.UserRole, task)
                        date_item.addChild(task_item)

                task_list_item.setExpanded(True)

        self.history_tree.expandAll()

    def show_context_menu(self, position):
        item = self.history_tree.itemAt(position)
        if item and item.parent() and item.parent().parent():
            task = item.data(0, Qt.ItemDataRole.UserRole)
            if task:
                menu = QMenu()
                view_details_action = QAction("View Details", self)
                restore_task_action = QAction("Restore Task", self)

                view_details_action.triggered.connect(lambda: self.view_task_details(item))
                restore_task_action.triggered.connect(lambda: self.restore_task(task))

                menu.addAction(view_details_action)
                menu.addAction(restore_task_action)

                menu.exec(self.history_tree.viewport().mapToGlobal(position))

    def view_task_details(self, item):
        task = item.data(0, Qt.ItemDataRole.UserRole)
        if task:
            self.open_task_detail(task)

    def open_task_detail(self, task):
        task_list_name = task.list_name
        task_list = next((tl for tl in self.parent.task_manager.task_lists if tl.name == task_list_name), None)
        if task_list:
            task_list_widget = self.parent.hash_to_task_list_widgets.get(task_list_name)
            if not task_list_widget:
                task_list_widget = TaskListWidget(task_list, self.parent)
                self.parent.hash_to_task_list_widgets[task_list_name] = task_list_widget

            task_list_widget.parent.add_task_detail_dock(task, task_list_widget)

    def restore_task(self, task):
        reply = QMessageBox.question(self, 'Restore Task', 'Are you sure you want to restore this task?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            task.status = "Not Started"
            task.last_completed_date = None
            self.parent.task_manager.update_task(task)
            global_signals.task_list_updated.emit()


class CalendarDock(QDockWidget):
    def __init__(self, parent):
        super().__init__("Calendar", parent)
        self.type = "calendar"
        self.parent = parent
        self.task_manager = self.parent.task_manager
        self.set_allowed_areas()
        self.setup_ui()
        self.setObjectName("calendarDock")
        self.calendar.setObjectName("calendarWidget")
        self.task_list_widget.setObjectName("calendarTaskListWidget")
        global_signals.task_list_updated.connect(self.update_calendar)

    def set_allowed_areas(self):
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

    def setup_ui(self):
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.layout = QVBoxLayout(self.widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.setup_filters()
        self.layout.addLayout(self.filter_layout)
        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.on_date_clicked)
        self.layout.addWidget(self.calendar)
        self.task_list_widget = QListWidget()
        self.task_list_widget.itemClicked.connect(self.on_task_clicked)
        self.layout.addWidget(self.task_list_widget)
        self.highlight_tasks_on_calendar()
        self.load_tasks_for_selected_date()

    def setup_filters(self):
        self.filter_layout = QHBoxLayout()
        self.filter_label = QLabel("Priority:")
        self.filter_priority_combo = QComboBox()
        self.filter_priority_combo.addItem("All")
        self.filter_priority_combo.addItems([str(i) for i in range(1, 11)])
        self.filter_priority_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.filter_layout.addWidget(self.filter_label)
        self.filter_layout.addWidget(self.filter_priority_combo)

        self.status_filter_label = QLabel("Status:")
        self.filter_status_combo = QComboBox()
        self.filter_status_combo.addItem("All")
        self.filter_status_combo.addItem("Completed")
        self.filter_status_combo.addItem("Not Completed")
        self.filter_status_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.filter_layout.addWidget(self.status_filter_label)
        self.filter_layout.addWidget(self.filter_status_combo)

        self.category_filter_label = QLabel("Category:")
        self.filter_category_combo = QComboBox()
        self.filter_category_combo.addItem("All")
        self.categories = self.get_all_categories()
        self.filter_category_combo.addItems(self.categories)
        self.filter_category_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.filter_layout.addWidget(self.category_filter_label)
        self.filter_layout.addWidget(self.filter_category_combo)

        self.filter_layout.addStretch()

    def get_all_categories(self):
        categories = set()
        for task_list_info in self.task_manager.get_task_lists():
            task_list = TaskList(task_list_info["list_name"], self.task_manager,
                                 task_list_info["queue"], task_list_info["stack"])
            for task in task_list.tasks:
                categories.update(task.categories)
        return sorted(categories)

    def highlight_tasks_on_calendar(self):
        tasks_by_date = self.get_tasks_grouped_by_date()
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        highlight_format = QTextCharFormat()
        highlight_format.setFontWeight(QFont.Weight.Bold)
        for date_str, tasks in tasks_by_date.items():
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            highlight_format.setToolTip(f"{len(tasks)} tasks due")
            self.calendar.setDateTextFormat(date, highlight_format)

    def get_tasks_grouped_by_date(self):
        tasks_by_date = {}
        for task_list_info in self.task_manager.get_task_lists():
            task_list = TaskList(task_list_info["list_name"], self.task_manager,
                                 task_list_info["queue"], task_list_info["stack"])
            for task in task_list.tasks:
                if task.due_date and task.due_date != "2000-01-01" and self.apply_filters(task):
                    date_str = task.due_date
                    if date_str not in tasks_by_date:
                        tasks_by_date[date_str] = []
                    tasks_by_date[date_str].append(task)
        return tasks_by_date

    def apply_filters(self, task):
        if self.filter_priority_combo.currentText() != "All" and str(
                task.priority) != self.filter_priority_combo.currentText():
            return False
        if self.filter_status_combo.currentText() == "Completed" and not task.completed:
            return False
        if self.filter_status_combo.currentText() == "Not Completed" and task.completed:
            return False
        if self.filter_category_combo.currentText() != "All" and self.filter_category_combo.currentText() not in task.categories:
            return False
        return True

    def on_date_clicked(self, date):
        self.load_tasks_for_selected_date()

    def load_tasks_for_selected_date(self):
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString("yyyy-MM-dd")
        tasks_by_date = self.get_tasks_grouped_by_date()
        self.task_list_widget.clear()
        if date_str in tasks_by_date:
            tasks = tasks_by_date[date_str]
            tasks.sort(key=lambda x: x.priority, reverse=True)
            for task in tasks:
                item = QListWidgetItem()
                task_widget = self.create_task_item_widget(task)
                item.setSizeHint(task_widget.sizeHint())
                self.task_list_widget.addItem(item)
                self.task_list_widget.setItemWidget(item, task_widget)
        else:
            self.task_list_widget.addItem("No tasks due on this date.")

    def create_task_item_widget(self, task):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        title_label = QLabel(task.title)
        title_font = QFont()
        title_font.setPointSize(10)
        if task.completed:
            title_font.setStrikeOut(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        layout.addStretch()
        if task.due_time and task.due_time != "00:00":
            due_time_label = QLabel(f"{task.due_time}")
            due_time_label.setStyleSheet("color: gray; font-size: 9px;")
            layout.addWidget(due_time_label)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task.completed)
        self.checkbox.stateChanged.connect(lambda state, t=task: self.mark_task_completed(t, state))
        layout.addWidget(self.checkbox)
        widget.setLayout(layout)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.mousePressEvent = lambda event, t=task: self.open_task_detail(t)
        return widget

    def mark_task_completed(self, task, state):
        task.completed = bool(state)
        self.task_manager.update_task(task)
        global_signals.task_list_updated.emit()

    def open_task_detail(self, task):
        if task.list_name in self.parent.task_lists:
            task_list = self.parent.task_lists[task.list_name]
        else:
            task_list = TaskList(task.list_name, self.task_manager, False, False, False)
            self.parent.task_lists[task.list_name] = task_list

        task_list_widget = self.parent.hash_to_task_list_widgets.get(task.list_name)
        if not task_list_widget:
            task_list_widget = TaskListWidget(task_list, self.parent)
            self.parent.hash_to_task_list_widgets[task.list_name] = task_list_widget

        task_list_widget.parent.add_task_detail_dock(task, task_list_widget)

    def on_task_clicked(self, item):
        pass

    def on_filter_changed(self, index):
        self.highlight_tasks_on_calendar()
        self.load_tasks_for_selected_date()

    def update_calendar(self):
        self.highlight_tasks_on_calendar()
        self.load_tasks_for_selected_date()


class ScheduleViewDock(QDockWidget):
    def __init__(self, parent):
        super(ScheduleViewDock, self).__init__(parent)
        self.type = "schedule"
        self.parent = parent
        self.task_manager = self.parent.task_manager
        self.schedule_manager = ScheduleManager(self.task_manager)
        self.set_allowed_areas()
        self.setup_ui()
        self.setObjectName("scheduleDock")

    def set_allowed_areas(self):
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

    from datetime import datetime

    def setup_ui(self):
        # start_time = datetime.strptime("12:00", "%H:%M").time()
        # end_time = datetime.strptime("16:00", "%H:%M").time()
        #
        # self.schedule_manager.add_timeblock(TimeBlock(
        #     task_manager_instance=self.task_manager,
        #     start_time=start_time,
        #     end_time=end_time,
        #     name="test3",
        #     include_categories=["test3"],
        #     block_type="user"
        # ))

        self.widget = ScheduleViewWidget(self.schedule_manager)
        self.setWidget(self.widget)
        # QTimer.singleShot(2000, self.widget.print_time_block_heights)
