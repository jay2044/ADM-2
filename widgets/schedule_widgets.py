from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys
from core.schedule_manager import *
from core.signals import *
from core.globals import *
from .task_progress_widgets import *
from .input_widgets import *


class ScheduleSettingsDialog(QDialog):
    def __init__(self, schedule_settings):
        super().__init__()
        self.schedule_settings = schedule_settings
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Configure Schedule Settings")
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.day_start_edit = QTimeEdit(self)
        self.day_start_edit.setTime(
            QTime(self.schedule_settings.day_start.hour, self.schedule_settings.day_start.minute))
        self.day_start_edit.timeChanged.connect(self.auto_calculate_hours)

        self.sleep_duration_spin = QSpinBox(self)
        self.sleep_duration_spin.setMinimum(1)
        self.sleep_duration_spin.setMaximum(24)
        self.sleep_duration_spin.setValue(int(self.schedule_settings.ideal_sleep_duration))
        self.sleep_duration_spin.valueChanged.connect(self.auto_calculate_hours)

        self.hours_available_edit = QLineEdit(self)
        self.hours_available_edit.setText(
            str(self.schedule_settings.hours_of_day_available or self.calculate_hours_available()))
        self.hours_available_edit.setReadOnly(True)
        self.hours_available_custom = QCheckBox("Custom")
        self.hours_available_custom.stateChanged.connect(self.toggle_hours_editable)

        self.overtime_combo = QComboBox(self)
        self.overtime_combo.addItems(["Auto", "Manual"])
        self.overtime_combo.setCurrentText(self.schedule_settings.overtime_flexibility)

        self.peak_start_edit = QTimeEdit(self)
        self.peak_start_edit.setTime(QTime(self.schedule_settings.peak_productivity_hours[0].hour,
                                           self.schedule_settings.peak_productivity_hours[0].minute))

        self.peak_end_edit = QTimeEdit(self)
        self.peak_end_edit.setTime(QTime(self.schedule_settings.peak_productivity_hours[1].hour,
                                         self.schedule_settings.peak_productivity_hours[1].minute))

        self.off_peak_start_edit = QTimeEdit(self)
        self.off_peak_start_edit.setTime(
            QTime(self.schedule_settings.off_peak_hours[0].hour, self.schedule_settings.off_peak_hours[0].minute))

        self.off_peak_end_edit = QTimeEdit(self)
        self.off_peak_end_edit.setTime(
            QTime(self.schedule_settings.off_peak_hours[1].hour, self.schedule_settings.off_peak_hours[1].minute))

        self.task_notifications_check = QCheckBox("Enable Task Notifications", self)
        self.task_notifications_check.setChecked(self.schedule_settings.task_notifications)

        self.popup_frequency_spin = QSpinBox(self)
        self.popup_frequency_spin.setMinimum(1)
        self.popup_frequency_spin.setMaximum(60)
        self.popup_frequency_spin.setValue(self.schedule_settings.task_status_popup_frequency)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_settings)

        form_layout.addRow("Day Start", self.day_start_edit)
        form_layout.addRow("Ideal Sleep Duration (hours)", self.sleep_duration_spin)
        form_layout.addRow("Hours of Day Available", self.hours_available_edit)
        form_layout.addRow("", self.hours_available_custom)
        form_layout.addRow("Overtime Flexibility", self.overtime_combo)
        form_layout.addRow("Peak Productivity Start", self.peak_start_edit)
        form_layout.addRow("Peak Productivity End", self.peak_end_edit)
        form_layout.addRow("Off-Peak Start", self.off_peak_start_edit)
        form_layout.addRow("Off-Peak End", self.off_peak_end_edit)
        form_layout.addRow(self.task_notifications_check)
        form_layout.addRow("Task Status Popup Frequency (minutes)", self.popup_frequency_spin)
        layout.addLayout(form_layout)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def calculate_hours_available(self):
        day_start = self.day_start_edit.time()
        sleep_duration = self.sleep_duration_spin.value()
        available_hours = 24 - sleep_duration
        return max(0, available_hours)

    def auto_calculate_hours(self):
        if not self.hours_available_custom.isChecked():
            self.hours_available_edit.setText(str(self.calculate_hours_available()))

    def toggle_hours_editable(self):
        self.hours_available_edit.setReadOnly(not self.hours_available_custom.isChecked())
        if not self.hours_available_custom.isChecked():
            self.auto_calculate_hours()

    def save_settings(self):
        day_start_time = self.day_start_edit.time()
        self.schedule_settings.set_day_start(day_start_time.toPyTime())
        self.schedule_settings.set_ideal_sleep_duration(self.sleep_duration_spin.value())
        self.schedule_settings.set_overtime_flexibility(self.overtime_combo.currentText())
        if self.hours_available_custom.isChecked():
            try:
                hours_available = int(self.hours_available_edit.text())
                if hours_available > 24 or hours_available < 0:
                    raise ValueError
                self.schedule_settings.set_hours_of_day_available(hours_available)
            except ValueError:
                return
        else:
            self.schedule_settings.set_hours_of_day_available(self.calculate_hours_available())
        self.schedule_settings.set_peak_productivity_hours(
            self.peak_start_edit.time().toPyTime(), self.peak_end_edit.time().toPyTime()
        )
        self.schedule_settings.set_off_peak_hours(
            self.off_peak_start_edit.time().toPyTime(), self.off_peak_end_edit.time().toPyTime()
        )
        self.schedule_settings.set_task_notifications(self.task_notifications_check.isChecked())
        self.schedule_settings.set_task_status_popup_frequency(self.popup_frequency_spin.value())
        self.accept()


class DatePickerCalendar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(250)
        self.setMaximumWidth(400)
        self.layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.selectionChanged.connect(self.date_changed)
        self.layout.addWidget(self.calendar)
        self.setLayout(self.layout)

    def get_selected_date(self):
        return self.calendar.selectedDate()

    def date_changed(self):
        print(self.get_selected_date().toString('yyyy-MM-dd'))


class ScheduleTaskWidget(QWidget):
    def __init__(self, task_list_manager: TaskManager, task_or_chunk):
        super().__init__()
        self.task_list_manager = task_list_manager
        if isinstance(task_or_chunk, TaskChunk):
            self.chunk = task_or_chunk
            self.task = task_or_chunk.task
        else:
            self.task = task_or_chunk
            self.chunk = None
        self.is_dragging = False
        self.no_context = False
        self.setup_ui()
        self.setup_timer()
        self.checkbox.setObjectName("taskCheckbox")
        self.radio_button.setObjectName("importantRadioButton")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_ui(self):
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.status == "completed")
        self.checkbox.stateChanged.connect(self.task_checked)
        self.layout.addWidget(self.checkbox)
        self.task_label = QLabel(self.task.title)
        self.task_label.setStyleSheet("font-size: 14px; text-decoration: none;")
        self.task_label.mousePressEvent = self.on_task_label_click
        self.layout.addWidget(self.task_label)
        if self.task.count_required or self.task.estimate or self.task.subtasks:
            self.progress_bar = TaskProgressBar(self.task)
            self.layout.addWidget(self.progress_bar)
        self.layout.addStretch()
        self.due_label = QLabel()
        self.due_label.setStyleSheet("font-size: 14px;")
        self.due_label.mousePressEvent = self.pick_due_date
        self.layout.addWidget(self.due_label)
        self.radio_button = QRadioButton()
        self.radio_button.setChecked(self.task.is_important)
        self.radio_button.toggled.connect(self.mark_important)
        self.layout.addWidget(self.radio_button)
        self.update_due_label()

    def on_task_label_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_task()

    def show_context_menu(self, position):
        if not self.no_context:
            menu = QMenu(self)
            due_today_action = QAction("Due Today", self)
            due_today_action.triggered.connect(self.set_due_today)
            menu.addAction(due_today_action)
            due_tomorrow_action = QAction("Due Tomorrow", self)
            due_tomorrow_action.triggered.connect(self.set_due_tomorrow)
            menu.addAction(due_tomorrow_action)
            pick_date_action = QAction("Pick a Date", self)
            pick_date_action.triggered.connect(self.pick_due_date)
            menu.addAction(pick_date_action)
            remove_due_date_action = QAction("Remove Due Date", self)
            remove_due_date_action.triggered.connect(self.remove_due_date)
            menu.addAction(remove_due_date_action)
            menu.addSeparator()
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_task)
            menu.addAction(delete_action)
            menu.exec(self.mapToGlobal(position))

    def set_due_today(self):
        pass

    def set_due_tomorrow(self):
        tomorrow = datetime.now() + timedelta(days=1)
        self.task.due_date = tomorrow.strftime("%Y-%m-%d")
        self.update_due_label()

    def pick_due_date(self, event):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(dialog)
        dialog.setLayout(layout)
        calendar = QCalendarWidget(dialog)
        current_due_date = QDate.fromString(self.task.due_date, "yyyy-MM-dd")
        if current_due_date.toString("yyyy-MM-dd") != "2000-01-01":
            calendar.setSelectedDate(current_due_date)
        calendar.selectionChanged.connect(lambda: self.update_due_date_from_calendar(calendar))
        layout.addWidget(calendar)
        time_edit = QTimeEdit(dialog)
        time_edit.setTime(QTime.fromString(self.task.due_time, "HH:mm"))
        time_edit.setDisplayFormat("h:mm AP")
        time_edit.timeChanged.connect(lambda: self.update_due_time_from_time_edit(time_edit))
        layout.addWidget(time_edit)
        button_layout = QHBoxLayout()
        clear_date_button = QPushButton("Clear Date", dialog)
        clear_date_button.clicked.connect(lambda: self.clear_due_date(calendar))
        button_layout.addWidget(clear_date_button)
        clear_time_button = QPushButton("Clear Time", dialog)
        clear_time_button.clicked.connect(lambda: self.clear_due_time(time_edit))
        button_layout.addWidget(clear_time_button)
        layout.addLayout(button_layout)
        dialog.move(
            self.due_label.mapToGlobal(QPoint(self.due_label.width() // 2, self.due_label.height() // 2)) - QPoint(
                dialog.width() // 2, dialog.height() // 2))
        dialog.exec()

    def update_task_due_date(self, due_date):
        self.task.due_date = due_date
        self.task_list_manager.update_task(self.task)

    def update_task_due_time(self, due_time):
        self.task.due_time = due_time
        self.task_list_manager.update_task(self.task)

    def update_due_date_from_calendar(self, calendar):
        self.update_task_due_date(calendar.selectedDate().toString("yyyy-MM-dd"))
        self.update_due_label()

    def update_due_time_from_time_edit(self, time_edit):
        self.update_task_due_time(time_edit.time().toString("HH:mm"))
        self.update_due_label()

    def clear_due_date(self, calendar):
        self.update_task_due_date("2000-01-01")
        calendar.clearFocus()
        self.update_due_label()

    def clear_due_time(self, time_edit):
        self.update_task_due_time("00:00")
        time_edit.setTime(QTime(0, 0))
        self.update_due_label()

    def remove_due_date(self):
        self.task.due_date = "2000-01-01"
        self.task.due_time = "00:00"
        self.update_due_label()

    def delete_task(self):
        self.task_list_manager.delete_task(self.task)

    def update_due_label(self):
        due_date = QDate.fromString(self.task.due_date, "yyyy-MM-dd")
        if due_date != QDate(2000, 1, 1):
            due_date_obj = datetime.strptime(self.task.due_date, "%Y-%m-%d")
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            end_of_week = today + timedelta(days=(6 - today.weekday()))
            is_this_year = due_date_obj.year == today.year
            formatted_date = ""
            color = DEFAULT_COLOR
            if due_date_obj.date() == today:
                formatted_date = "Today"
                color = DUE_TODAY_COLOR
            elif due_date_obj.date() == tomorrow:
                formatted_date = "Tomorrow"
                color = DUE_TOMORROW_COLOR
            elif due_date_obj.date() < today:
                day = due_date_obj.day
                suffix = "th" if 11 <= day <= 13 else ["st", "nd", "rd"][day % 10 - 1] if day % 10 in [1, 2,
                                                                                                       3] else "th"
                month_abbr = due_date_obj.strftime("%b")
                year = f" {due_date_obj.year}" if not is_this_year else ""
                formatted_date = f"{day}{suffix} {month_abbr}{year}"
                color = PAST_DUE_COLOR
            elif today < due_date_obj.date() <= end_of_week:
                short_weekday = due_date_obj.strftime("%a")
                formatted_date = short_weekday
                color = DUE_THIS_WEEK_COLOR
            else:
                day = due_date_obj.day
                suffix = "th" if 11 <= day <= 13 else ["st", "nd", "rd"][day % 10 - 1] if day % 10 in [1, 2,
                                                                                                       3] else "th"
                month_abbr = due_date_obj.strftime("%b")
                year = f" {due_date_obj.year}" if not is_this_year else ""
                formatted_date = f"{day}{suffix} {month_abbr}{year}"
            if self.task.due_time != "00:00":
                due_time_obj = datetime.strptime(self.task.due_time, "%H:%M")
                formatted_time = due_time_obj.strftime("%I:%M %p").lstrip("0")
                formatted_date += f" at {formatted_time}"
            self.due_label.setText(formatted_date)
            self.due_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        else:
            self.due_label.setText("")
            self.due_label.setStyleSheet("")
        self.task_list_manager.update_task(self.task)

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.edit_task)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.timer.start(250)
            self.start_pos = event.pos()
        if event.button() == Qt.MouseButton.RightButton:
            self.no_context = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.RightButton:
            self.no_context = True
            return
        if not self.is_dragging and (event.pos() - self.start_pos).manhattanLength() > QApplication.startDragDistance():
            self.is_dragging = True
            self.timer.stop()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.timer.isActive():
                    self.timer.stop()
                    self.edit_task()
            super().mouseReleaseEvent(event)
        except Exception as e:
            print(e)

    def edit_task(self):
        get_main_window().add_task_detail_dock(self.task)

    def task_checked(self, state):
        try:
            self.task.completed = not self.task.completed
            self.task_list_manager.update_task(self.task)
            global_signals.task_list_updated.emit()
        except Exception as e:
            print(f"Error in task_checked: {e}")

    def mark_important(self):
        try:
            if self.radio_button.isChecked():
                self.task.mark_as_important()
                self.task.priority = 7
            else:
                self.task.unmark_as_important()
                self.task.priority = 0
            self.task_list_manager.update_task(self.task)
            global_signals.task_list_updated.emit()
        except Exception as e:
            print(f"Error in mark_important: {e}")


class ScheduleTaskChunkWidget(QWidget):
    def __init__(self, task_list_manager, chunk):
        super().__init__()
        self.task_list_manager = task_list_manager
        self.chunk = chunk
        self.task = chunk.task
        self.is_dragging = False
        self.no_context = False
        self.setup_ui()
        self.setup_timer()
        self.checkbox.setObjectName("chunkCheckbox")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # Top layout for checkbox, task name, and recurrence indicator
        top_layout = QHBoxLayout()

        # Checkbox for task chunk status
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.chunk.status == "completed")
        self.checkbox.stateChanged.connect(self.chunk_checked)
        top_layout.addWidget(self.checkbox)

        # Task name label
        self.task_name_label = QLabel(self.task.name)
        task_name_font = QFont()
        task_name_font.setPointSize(14)
        self.task_name_label.setFont(task_name_font)
        self.task_name_label.mousePressEvent = self.on_chunk_label_click
        top_layout.addWidget(self.task_name_label)

        # Stretch to push the recurrence indicator to the right
        top_layout.addStretch()

        # Recurrence indicator ('R') if the chunk is recurring
        if self.chunk.is_recurring:
            self.recurrence_label = QLabel('R')
            recurrence_font = QFont()
            recurrence_font.setPointSize(10)  # Small font for subtlety
            self.recurrence_label.setFont(recurrence_font)
            palette = self.recurrence_label.palette()
            palette.setColor(QPalette.WindowText, QColor(128, 128, 128))  # Light gray color
            self.recurrence_label.setPalette(palette)
            top_layout.addWidget(self.recurrence_label)

        # Add the top layout to the main layout
        self.layout.addLayout(top_layout)

        # Details label below the top layout
        details = self.get_details_text()
        self.details_label = QLabel(details)
        details_font = QFont()
        details_font.setPointSize(10)
        self.details_label.setFont(details_font)
        self.layout.addWidget(self.details_label)

    def get_details_text(self):
        chunk_type = self.chunk.chunk_type.capitalize()
        unit_display = "hours" if self.chunk.unit == "time" else "units"
        if self.chunk.unit == "time":
            total_size = self.task.time_estimate
        elif self.chunk.unit == "count":
            total_size = self.task.count_required
        else:
            total_size = None
        if total_size is not None and total_size > 0:
            size_str = f"{self.chunk.size:.1f} / {total_size:.1f} {unit_display}"
        else:
            size_str = f"{self.chunk.size:.1f} {unit_display}"
        due_str = self.get_formatted_due_date()
        return f"{chunk_type} ({size_str}) {due_str}"

    def get_formatted_due_date(self):
        due_datetime = self.task.due_datetime
        if due_datetime is None:
            return ""
        if isinstance(due_datetime, int):  # Convert epoch timestamp to datetime.
            due_datetime = datetime.fromtimestamp(due_datetime)
        if isinstance(due_datetime, datetime):
            due_date = due_datetime.date()
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            end_of_week = today + timedelta(days=(6 - today.weekday()))
            is_this_year = due_date.year == today.year

            if due_date == today:
                formatted_date = "Today"
            elif due_date == tomorrow:
                formatted_date = "Tomorrow"
            elif due_date < today:
                day = due_date.day
                suffix = "th" if 11 <= day <= 13 else ["st", "nd", "rd"][day % 10 - 1] if day % 10 in [1, 2,
                                                                                                       3] else "th"
                month_abbr = due_date.strftime("%b")
                year = f" {due_date.year}" if not is_this_year else ""
                formatted_date = f"{day}{suffix} {month_abbr}{year}"
            elif today < due_date <= end_of_week:
                formatted_date = due_date.strftime("%a")
            else:
                day = due_date.day
                suffix = "th" if 11 <= day <= 13 else ["st", "nd", "rd"][day % 10 - 1] if day % 10 in [1, 2,
                                                                                                       3] else "th"
                month_abbr = due_date.strftime("%b")
                year = f" {due_date.year}" if not is_this_year else ""
                formatted_date = f"{day}{suffix} {month_abbr}{year}"

            if due_datetime.time() != datetime.min.time():
                formatted_time = due_datetime.strftime("%I:%M %p").lstrip("0")
                formatted_date += f" at {formatted_time}"
            return f"Due: {formatted_date}"
        return ""

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.edit_task)

    def on_chunk_label_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_task()

    def show_context_menu(self, position):
        if not self.no_context:
            menu = QMenu(self)
            delete_action = QAction("Delete Chunk", self)
            delete_action.triggered.connect(self.delete_chunk)
            menu.exec(self.mapToGlobal(position))

    def chunk_checked(self, state):
        if state == Qt.CheckState.Checked.value:
            self.chunk.status = "completed"
        else:
            self.chunk.status = "active"
        self.task.update_chunk_obj(self.chunk)

    def delete_chunk(self):
        self.task.delete_chunk(self.chunk)
        self.task_list_manager.update_task(self.task)
        self.setParent(None)
        self.deleteLater()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.timer.start(250)
            self.start_pos = event.pos()
        if event.button() == Qt.MouseButton.RightButton:
            self.no_context = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.RightButton:
            self.no_context = True
            return
        if not self.is_dragging and (event.pos() - self.start_pos).manhattanLength() > QApplication.startDragDistance():
            self.is_dragging = True
            self.timer.stop()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.timer.isActive():
                    self.timer.stop()
                    self.edit_task()
            super().mouseReleaseEvent(event)
        except Exception as e:
            print(e)

    def edit_task(self):
        get_main_window().add_task_detail_dock(self.task)


class HourCell(QWidget):
    """Custom widget for hour cells."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(label)


class HourScaleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.day_start_time = parent.schedule_manager.schedule_settings.day_start
        self.hours = [
            f"{(self.day_start_time.hour + i) % 12 or 12} {'AM' if (self.day_start_time.hour + i) % 24 < 12 else 'PM'}"
            for i in range(25)  # Covers a full 24-hour cycle plus 1 extra for visual continuity
        ]

        self.custom_heights = {i: 20 for i in range(len(self.hours))}

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.populate_cells()
        self.start_auto_update()

    def populate_cells(self):
        """Populate the widget with hour widgets."""
        for i, hour in enumerate(self.hours):
            cell_text = hour if i % 2 == 0 else "-"
            cell_widget = HourCell(cell_text, self)
            # cell_widget.setFixedHeight(self.custom_heights.get(i, 20))
            self.layout.addWidget(cell_widget, stretch=20)

    def set_height(self, start_index, end_index, height):
        range_size = (max(start_index, end_index) - min(start_index, end_index))
        if range_size == 0:
            # The block is effectively zero length or same hour => do nothing or pick a default
            return

        height_per_cell = int(height / range_size)
        for index in range(start_index, end_index + 1):
            if 0 <= index < len(self.hours):
                self.custom_heights[index] = height_per_cell
                widget = self.layout.itemAt(index).widget()
                widget.resize(widget.width(), height_per_cell)
                self.layout.setStretchFactor(widget, height_per_cell)

    def set_height_by_widget(self, start_hour, end_hour, widget):
        """Set the height of intervals to match the height of another widget."""
        hours = self.hours
        start_index = hours.index(start_hour)
        end_index = hours.index(end_hour)
        widget_height = widget.base_height
        self.set_height(start_index, end_index, widget_height)

    def highlight_current_hour(self):
        current_time = QTime.currentTime()
        current_hour = current_time.hour()
        start_hour = 4
        hour_index = current_hour - start_hour if current_hour >= start_hour else (current_hour + 24 - start_hour)

        for i in range(len(self.hours)):
            widget = self.layout.itemAt(i).widget()
            if i < hour_index:
                widget.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
            elif i == hour_index:
                widget.setStyleSheet("background-color: rgba(3, 204, 163, 128); font-weight: bold;")

    def start_auto_update(self):
        timer = QTimer(self)
        timer.timeout.connect(self.highlight_current_hour)
        timer.start(3600000)
        self.highlight_current_hour()


class DraggableListWidget(QListWidget):
    def __init__(self, parent_time_block_widget):
        """
        :param parent_time_block_widget: The TimeBlockWidget that owns this list.
        """
        super().__init__(parent_time_block_widget.frame)
        self.parent_time_block_widget = parent_time_block_widget
        self.dragged_task_widget = None

        # Basic list settings for drag and drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizeAdjustPolicy(QAbstractItemView.SizeAdjustPolicy.AdjustToContents)
        self.adjustSize()

        # If you want to react to reordering within the list:
        self.model().rowsMoved.connect(self.on_rows_moved)

    def startDrag(self, supportedActions):
        """Called when the user begins dragging an item."""
        item = self.currentItem()
        if item:
            task_widget = self.itemWidget(item)
            if task_widget:
                self.dragged_task_widget = task_widget
        super().startDrag(supportedActions)

    def dropEvent(self, event):
        """Called when a dragged item is dropped onto this list."""
        source_list_widget = event.source()
        if source_list_widget and source_list_widget is not self:
            # If the drop comes from another DraggableListWidget
            dragged_task_widget = getattr(source_list_widget, "dragged_task_widget", None)
            if dragged_task_widget:
                # Using the chunk attribute instead of task.
                chunk = dragged_task_widget.chunk
                print(
                    f"Chunk for task '{chunk.task.name}' moved from "
                    f"{source_list_widget.parent_time_block_widget.name} to {self.parent_time_block_widget.name}"
                )
                event.ignore()
                source_list_widget.parent_time_block_widget.remove_chunk(chunk)
                self.parent_time_block_widget.add_chunk(chunk)
        else:
            super().dropEvent(event)

    def on_rows_moved(self, parent, start, end, destination, row):
        """
        React to reordering within the same list.
        'parent' and 'destination' are model indexes, while 'start', 'end', and 'row' are row indices.
        """
        print("Rows moved internally in DraggableListWidget")
        # TODO: implement reorder logic if needed.


class TimeBlockWidget(QWidget):
    def __init__(self, parent, time_block: TimeBlock):
        super().__init__(parent)

        self.setMinimumWidth(300)

        self.time_block = time_block
        self.name = self.time_block.name
        self.color = self.time_block.color

        # Convert start_time and end_time from time objects to strings ("HH:MM")
        self.start_time = (
            self.time_block.start_time.strftime("%H:%M")
            if self.time_block.start_time
            else "00:00"
        )
        self.end_time = (
            self.time_block.end_time.strftime("%H:%M")
            if self.time_block.end_time
            else "00:00"
        )

        self.start_hour = int(self.start_time.split(":")[0])
        self.end_hour = int(self.end_time.split(":")[0])
        # Adjust if end hour is on the next day
        if self.end_hour < self.start_hour:
            self.end_hour += 24
        self.base_height = max(45 * (self.end_hour - self.start_hour), 45)
        self.setMinimumHeight(self.base_height)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0)

        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)

        self.schedule_manager = (
            parent.schedule_manager
            if parent and hasattr(parent, "schedule_manager")
            else None
        )

        if self.time_block.block_type != "unavailable":
            self.init_ui_time_block_with_tasks()
        else:
            self.init_ui_unavailable()

        # Use only task chunk logic to build the internal chunk list.
        self.chunks = (
            [entry["chunk"] for entry in self.time_block.task_chunks.values()]
            if hasattr(self.time_block, "task_chunks")
            else []
        )

        if self.chunks:
            self.load_tasks()

    def setup_frame(self, name, color):
        self.name = name
        color_rgba = QColor(color[0], color[1], color[2], 128)
        palette = self.frame.palette()
        palette.setColor(QPalette.ColorRole.Window, color_rgba)
        self.frame.setAutoFillBackground(True)
        self.frame.setPalette(palette)

        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_layout.setSpacing(0)

        self.name_label = QLabel(self.name, self.frame)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.frame_layout.addWidget(self.name_label)

        self.layout.addWidget(self.frame)

    def init_ui_time_block_with_tasks(self):
        self.setup_frame(self.name, self.color)
        self.task_list = DraggableListWidget(self)
        self.frame_layout.addWidget(self.task_list)

    def init_ui_empty(self):
        self.setup_frame("No chunks", (47, 47, 47))

    def init_ui_unavailable(self):
        self.setup_frame("Unavailable", (231, 131, 97))

    def load_tasks(self):
        for chunk in self.chunks:
            # Create the ScheduleTaskChunkWidget using the chunk.
            task_widget = ScheduleTaskChunkWidget(
                self.schedule_manager.task_manager_instance, chunk
            )
            item = QListWidgetItem()
            item.setSizeHint(task_widget.sizeHint())
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, task_widget)
        self.resize_frame_and_hour_cells()

    def add_chunk(self, chunk: TaskChunk):
        """
        Adds a TaskChunk to the time block and updates the UI.
        """
        self.time_block.add_chunk(chunk, rating=9999)  # or appropriate rating
        self.chunks.append(chunk)
        task_widget = ScheduleTaskChunkWidget(
            self.schedule_manager.task_manager_instance, chunk
        )
        item = QListWidgetItem()
        item.setSizeHint(task_widget.sizeHint())
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, task_widget)
        self.resize_frame_and_hour_cells()

    def remove_chunk(self, chunk: TaskChunk):
        """
        Removes the specified TaskChunk from both the widget's internal list (self.chunks)
        and the QListWidget display.
        """
        item_to_remove = None
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            task_widget = self.task_list.itemWidget(item)
            # Assuming the ScheduleTaskChunkWidget stores the chunk as `chunk`
            if task_widget and task_widget.chunk == chunk:
                item_to_remove = item
                break

        if item_to_remove is not None:
            row = self.task_list.row(item_to_remove)
            self.task_list.takeItem(row)  # Removes from UI
            if chunk in self.chunks:
                self.chunks.remove(chunk)
            self.resize_frame_and_hour_cells()

    def resize_frame_and_hour_cells(self):
        """
        Recalculates the widget's minimum height based on the current TaskChunk items in the QListWidget
        and updates the corresponding hour cells in the parent ScheduleViewWidget's HourScaleWidget.
        """
        if self.task_list.count() == 0:
            new_height = self.base_height
        else:
            task_height = self.name_label.height() + sum(
                self.task_list.sizeHintForRow(i) for i in range(self.task_list.count())
            ) + 15
            if self.base_height >= task_height:
                new_height = max(task_height, max(45 * (self.end_hour - self.start_hour), 45))
            else:
                new_height = max(task_height, self.base_height)

        self.base_height = new_height + (self.task_list.frameWidth() * 2)
        self.setMinimumHeight(self.base_height)
        self.task_list.adjustSize()

        p = self.parent()
        if isinstance(p, ScheduleViewWidget):
            QTimer.singleShot(0, p.update_time_cell_heights)
            p.timeBlocksLayout.setStretchFactor(self, self.base_height)


class TimeBlockManagerWidget(QWidget):
    def __init__(self, parent, schedule_manager):
        super().__init__()
        self.setMaximumWidth(400)
        self.parent = parent
        self.schedule_manager = schedule_manager
        self.initUI()

    def initUI(self):
        self.mainLayout = QVBoxLayout(self)

        topLayout = QHBoxLayout()
        self.addTimeBlockButton = QPushButton("Add Time Block")
        self.addTimeBlockButton.clicked.connect(self.open_add_time_block_dialogue)
        topLayout.addStretch()
        topLayout.addWidget(self.addTimeBlockButton)

        self.mainLayout.addLayout(topLayout)

        self.timeBlockList = QListWidget(self)
        self.populate_time_blocks()
        self.timeBlockList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.timeBlockList.customContextMenuRequested.connect(self.show_context_menu)

        self.mainLayout.addWidget(self.timeBlockList)

    def populate_time_blocks(self):
        self.timeBlockList.clear()
        for time_block in self.schedule_manager.time_blocks:
            item = QListWidgetItem(time_block.get("name"))
            self.timeBlockList.addItem(item)

    def show_context_menu(self, position):
        item = self.timeBlockList.itemAt(position)
        if item:
            menu = QMenu(self)
            edit_action = menu.addAction("Edit")
            delete_action = menu.addAction("Delete")
            action = menu.exec(self.timeBlockList.viewport().mapToGlobal(position))
            if action == edit_action:
                self.open_edit_time_block_dialogue(item.text())
            elif action == delete_action:
                self.delete_time_block(item.text())

    def open_add_time_block_dialogue(self):
        day_start_datetime = datetime.combine(datetime.now().date(), self.schedule_manager.schedule_settings.day_start)

        dialog = AddTimeBlockDialog(self, day_start_time=day_start_datetime)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            time_block_data = dialog.get_time_block_data()

            if not time_block_data['name']:
                QMessageBox.warning(self, "Invalid Input", "Name cannot be empty.")
                return

            if time_block_data['unavailable']:
                new_time_block = {
                    "name": time_block_data['name'],
                    "schedule": time_block_data['schedule'],
                    "color": time_block_data['color'],
                    "unavailable": 1
                }
            else:
                new_time_block = {
                    "name": time_block_data['name'],
                    "schedule": time_block_data['schedule'],
                    "list_categories": time_block_data['list_categories'],
                    "task_tags": time_block_data['task_tags'],
                    "color": time_block_data['color'],
                    "unavailable": 0
                }

            self.schedule_manager.add_time_block(new_time_block)
            self.populate_time_blocks()

            QMessageBox.information(self, "Success", "Time block added successfully!")
            global_signals.refresh_schedule_signal.emit()

    def open_edit_time_block_dialogue(self, time_block_name):
        for block in self.schedule_manager.time_blocks:
            if time_block_name == block.get("name"):
                day_start_datetime = datetime.combine(datetime.now().date(),
                                                      self.schedule_manager.schedule_settings.day_start)

                dialog = AddTimeBlockDialog(self, day_start_time=day_start_datetime)
                dialog.edit_mode(block)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    time_block_data = dialog.get_time_block_data()

                    if not time_block_data['name']:
                        QMessageBox.warning(self, "Invalid Input", "Name cannot be empty.")
                        return

                    if time_block_data['unavailable']:
                        new_time_block = {
                            "name": time_block_data['name'],
                            "schedule": time_block_data['schedule'],
                            "color": time_block_data['color'],
                            "unavailable": 1
                        }
                    else:
                        new_time_block = {
                            "name": time_block_data['name'],
                            "schedule": time_block_data['schedule'],
                            "list_categories": time_block_data['list_categories'],
                            "task_tags": time_block_data['task_tags'],
                            "color": time_block_data['color'],
                            "unavailable": 0
                        }

                    self.schedule_manager.update_time_block(new_time_block)
                    self.populate_time_blocks()

                    QMessageBox.information(self, "Success", "Time block updated successfully!")
                    global_signals.refresh_schedule_signal.emit()

    def delete_time_block(self, time_block_name):
        self.schedule_manager.remove_time_block(time_block_name)
        self.populate_time_blocks()
        global_signals.refresh_schedule_signal.emit()


class SuggestionPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(400)
        main_layout = QVBoxLayout(self)

        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("QToolBar { border: none; }")

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        add_action = QAction("Configure", self)
        add_action.triggered.connect(self.configure_weights)

        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(add_action)

        self.list_widget = QListWidget()

        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.list_widget)

    def configure_weights(self):
        print("configure bruh")


# ----------------------------------
# SCHEDULE VIEW LOGIC MAIN
# ----------------------------------


class ScheduleViewWidget(QWidget):
    def __init__(self, schedule_manager=None):
        super().__init__()
        self.schedule_manager = schedule_manager
        self.expanded_ui_visible = False
        self.current_view_mode = "Day"  # "Day" or "Week"
        self.initUI()
        self.load_time_blocks()
        self.load_suggestion_panel()
        # Optionally: global_signals.refresh_schedule_signal.connect(self.load_time_blocks)

    def initUI(self):
        self.mainLayout = QHBoxLayout(self)
        self.setLayout(self.mainLayout)

        # Expanded UI container
        self.expandedContainer = QWidget()
        self.expandedUI()
        self.expandedContainer.setVisible(False)
        self.mainLayout.addWidget(self.expandedContainer)

        self.scheduleViewUI()

    def scheduleViewUI(self):
        self.scheduleViewOnlyLayout = QVBoxLayout()

        # --- Toolbar Section ---
        toolbarContainer = QWidget()
        toolbarLayout = QVBoxLayout(toolbarContainer)
        toolbarLayout.setContentsMargins(0, 0, 0, 0)
        toolbar = QToolBar("Schedule Toolbar")
        self.expandAction = QAction("<<", self)
        self.expandAction.triggered.connect(self.toggle_expanded_ui)
        toolbar.addAction(self.expandAction)
        self.scheduleSettingsAction = QAction("Schedule Settings", self)
        self.scheduleSettingsAction.triggered.connect(self.open_settings_dialogue)
        toolbar.addAction(self.scheduleSettingsAction)
        toolbar.addSeparator()

        # Toggle actions for Day and Week views
        self.dayViewAction = QAction("Day", self)
        self.dayViewAction.setCheckable(True)
        self.weekViewAction = QAction("Week", self)
        self.weekViewAction.setCheckable(True)
        self.dayViewAction.triggered.connect(self.set_day_view_mode)
        self.weekViewAction.triggered.connect(self.set_week_view_mode)
        if self.current_view_mode == "Day":
            self.dayViewAction.setChecked(True)
        else:
            self.weekViewAction.setChecked(True)
        viewActionGroup = QActionGroup(self)
        viewActionGroup.addAction(self.dayViewAction)
        viewActionGroup.addAction(self.weekViewAction)
        viewActionGroup.setExclusive(True)
        toolbar.addAction(self.dayViewAction)
        toolbar.addAction(self.weekViewAction)
        toolbar.addSeparator()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self.quickTaskAction = QAction("Add Quick Task", self)
        toolbar.addAction(self.quickTaskAction)
        toolbarLayout.addWidget(toolbar)
        self.scheduleViewOnlyLayout.addWidget(toolbarContainer)

        # --- Main Content Section ---
        # Create one scroll area that contains both the HourScaleWidget and the schedule views.
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.container = QWidget()
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        # Add the HourScaleWidget on the left.
        self.timeScaleWidget = HourScaleWidget(self)
        container_layout.addWidget(self.timeScaleWidget)
        # Create a widget to hold the schedule blocks (day/week) with a stacked layout.
        self.scheduleBlocksWidget = QWidget()
        self.stackLayout = QStackedLayout(self.scheduleBlocksWidget)
        # Day view container
        self.dayViewWidget = QWidget()
        self.dayLayout = QVBoxLayout(self.dayViewWidget)
        self.dayLayout.setSpacing(5)
        self.dayLayout.setContentsMargins(0, 0, 0, 0)
        self.stackLayout.addWidget(self.dayViewWidget)
        # Week view container
        self.weekViewWidget = QWidget()
        self.weekLayout = QHBoxLayout(self.weekViewWidget)
        self.weekLayout.setSpacing(2)  # Reduced spacing between columns
        self.weekLayout.setContentsMargins(0, 0, 0, 0)
        self.stackLayout.addWidget(self.weekViewWidget)
        container_layout.addWidget(self.scheduleBlocksWidget)
        scroll_area.setWidget(self.container)
        self.scheduleViewOnlyLayout.addWidget(scroll_area)
        self.mainLayout.addLayout(self.scheduleViewOnlyLayout)

    def expandedUI(self):
        self.expandedLayout = QGridLayout(self.expandedContainer)
        # Use the custom DatePickerCalendar.
        self.date_picker = DatePickerCalendar()
        # When the date selection changes, update the schedule's starting day.
        self.date_picker.calendar.selectionChanged.connect(self.date_changed_handler)
        self.date_label = QLabel("Selected Date: ")
        self.time_block_manager = TimeBlockManagerWidget(self, self.schedule_manager)
        self.suggestion_panel = SuggestionPanel()
        self.expandedLayout.addWidget(self.date_picker, 0, 0)
        self.expandedLayout.addWidget(self.time_block_manager, 1, 0)
        self.expandedLayout.addWidget(self.suggestion_panel, 0, 1, 2, 1)

    def toggle_expanded_ui(self):
        self.expanded_ui_visible = not self.expanded_ui_visible
        self.expandedContainer.setVisible(self.expanded_ui_visible)

    def date_changed_handler(self):
        self.update_date_label()
        self.load_time_blocks()

    def update_date_label(self):
        selected_date = self.date_picker.get_selected_date().toString('yyyy-MM-dd')
        self.date_label.setText(f"Selected Date: {selected_date}")

    def clearLayout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clearLayout(item.layout())

    def load_time_blocks(self):
        # Refresh schedule from the schedule manager.
        self.schedule_manager.refresh_schedule()
        self.clearLayout(self.dayLayout)
        self.clearLayout(self.weekLayout)
        # Use the date selected in the DatePickerCalendar as the starting date.
        selected_date = self.date_picker.get_selected_date().toPyDate()
        if self.current_view_mode == "Day":
            day_schedule = self.schedule_manager.get_day_schedule(selected_date)
            time_blocks = day_schedule.time_blocks if day_schedule else []
            for block in time_blocks:
                tb_widget = TimeBlockWidget(self, block)
                self.dayLayout.addWidget(tb_widget)
            self.stackLayout.setCurrentWidget(self.dayViewWidget)
        elif self.current_view_mode == "Week":
            # In week view, the selected date is the first column followed by the next six days.
            for i in range(7):
                current_day = selected_date + timedelta(days=i)
                day_container = QWidget()
                day_layout = QVBoxLayout(day_container)
                day_layout.setSpacing(2)
                day_layout.setContentsMargins(2, 2, 2, 2)
                day_label = QLabel(current_day.strftime("%A %Y-%m-%d"))
                day_layout.addWidget(day_label)
                day_schedule = self.schedule_manager.get_day_schedule(current_day)
                time_blocks = day_schedule.time_blocks if day_schedule else []
                for block in time_blocks:
                    tb_widget = TimeBlockWidget(self, block)
                    day_layout.addWidget(tb_widget)
                self.weekLayout.addWidget(day_container)
            self.stackLayout.setCurrentWidget(self.weekViewWidget)
        QTimer.singleShot(0, self.update_time_cell_heights)

    def update_time_cell_heights(self):
        self.updateGeometry()
        QApplication.processEvents()
        day_start_hour = self.schedule_manager.schedule_settings.day_start.hour
        if self.current_view_mode == "Day":
            for i in range(self.dayLayout.count()):
                tb_widget = self.dayLayout.itemAt(i).widget()
                if tb_widget and hasattr(tb_widget, "start_time") and hasattr(tb_widget, "end_time"):
                    block_start_dt = datetime.strptime(tb_widget.start_time, "%H:%M")
                    block_end_dt = datetime.strptime(tb_widget.end_time, "%H:%M")
                    start_hour = block_start_dt.hour
                    end_hour = block_end_dt.hour
                    if end_hour < start_hour:
                        end_hour += 24
                    relative_start = start_hour - day_start_hour if start_hour >= day_start_hour else start_hour + (
                            24 - day_start_hour)
                    relative_end = end_hour - day_start_hour if end_hour >= day_start_hour else end_hour + (
                            24 - day_start_hour)
                    start_str = f"{(day_start_hour + relative_start) % 12 or 12} {'AM' if (day_start_hour + relative_start) % 24 < 12 else 'PM'}"
                    end_str = f"{(day_start_hour + relative_end) % 12 or 12} {'AM' if (day_start_hour + relative_end) % 24 < 12 else 'PM'}"
                    self.timeScaleWidget.set_height_by_widget(start_str, end_str, tb_widget)
        elif self.current_view_mode == "Week":
            for i in range(self.weekLayout.count()):
                day_container = self.weekLayout.itemAt(i).widget()
                if day_container:
                    day_layout = day_container.layout()
                    for j in range(day_layout.count()):
                        child = day_layout.itemAt(j).widget()
                        if child and hasattr(child, "start_time") and hasattr(child, "end_time") and isinstance(child,
                                                                                                                TimeBlockWidget):
                            block_start_dt = datetime.strptime(child.start_time, "%H:%M")
                            block_end_dt = datetime.strptime(child.end_time, "%H:%M")
                            start_hour = block_start_dt.hour
                            end_hour = block_end_dt.hour
                            if end_hour < start_hour:
                                end_hour += 24
                            relative_start = start_hour - day_start_hour if start_hour >= day_start_hour else start_hour + (
                                    24 - day_start_hour)
                            relative_end = end_hour - day_start_hour if end_hour >= day_start_hour else end_hour + (
                                    24 - day_start_hour)
                            start_str = f"{(day_start_hour + relative_start) % 12 or 12} {'AM' if (day_start_hour + relative_start) % 24 < 12 else 'PM'}"
                            end_str = f"{(day_start_hour + relative_end) % 12 or 12} {'AM' if (day_start_hour + relative_end) % 24 < 12 else 'PM'}"
                            self.timeScaleWidget.set_height_by_widget(start_str, end_str, child)

    def set_day_view_mode(self):
        self.current_view_mode = "Day"
        self.load_time_blocks()

    def set_week_view_mode(self):
        self.current_view_mode = "Week"
        self.load_time_blocks()

    def open_settings_dialogue(self):
        dialog = ScheduleSettingsDialog(self.schedule_manager.schedule_settings)
        if dialog.exec():
            pass

    def get_displayed_chunk_ids(self):
        displayed_ids = set()
        if self.current_view_mode == "Day":
            for i in range(self.dayLayout.count()):
                tb_widget = self.dayLayout.itemAt(i).widget()
                if hasattr(tb_widget, "chunks"):
                    for chunk in tb_widget.chunks:
                        displayed_ids.add(chunk.id)
        elif self.current_view_mode == "Week":
            for i in range(self.weekLayout.count()):
                day_container = self.weekLayout.itemAt(i).widget()
                day_layout = day_container.layout()
                for j in range(day_layout.count()):
                    child = day_layout.itemAt(j).widget()
                    if isinstance(child, TimeBlockWidget):
                        for chunk in child.chunks:
                            displayed_ids.add(chunk.id)
        return displayed_ids

    def load_suggestion_panel(self):
        # Clear any previous suggestions
        self.suggestion_panel.list_widget.clear()
        displayed_ids = self.get_displayed_chunk_ids()
        if hasattr(self, "suggestion_panel"):
            for chunk in self.schedule_manager.chunks:
                # Skip chunks already shown in the schedule view
                if chunk.id in displayed_ids:
                    continue
                task_widget = ScheduleTaskChunkWidget(self.schedule_manager.task_manager_instance, chunk)
                item = QListWidgetItem()
                item.setSizeHint(task_widget.sizeHint())
                self.suggestion_panel.list_widget.addItem(item)
                self.suggestion_panel.list_widget.setItemWidget(item, task_widget)

    @property
    def timeBlocksLayout(self):
        # Returns the currently active layout (for compatibility)
        if self.current_view_mode == "Day":
            return self.dayLayout
        elif self.current_view_mode == "Week":
            return self.weekLayout
        return None
