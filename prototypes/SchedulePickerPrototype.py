import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QPoint, QTime
from PyQt6.QtGui import *
from pandas.core.tools.times import to_time


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


class SchedulePickerPrototype(QWidget):
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SchedulePickerPrototype()
    window.show()
    sys.exit(app.exec())
