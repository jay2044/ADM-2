from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys
from core.schedule_manager import *
from core.signals import *
from core.globals import *
from .task_progress_widgets import *


class ScheduleTaskWidget(QWidget):
    def __init__(self, task_list_manager: TaskListManager, task):
        super().__init__()
        self.task_list_manager = task_list_manager
        self.task = task
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
        self.checkbox.setChecked(self.task.completed)
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
        self.task.due_date = datetime.now().strftime("%Y-%m-%d")
        self.update_due_label()

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
        self.hours = [
            f"{hour % 12 or 12} {'AM' if hour % 24 < 12 else 'PM'}"
            for hour in range(4, 29)
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
        """Set the height of a specific range of intervals based on pixels."""
        height = int(height / (max(start_index, end_index) - min(start_index, end_index)))
        for index in range(start_index, end_index + 1):
            if 0 <= index < len(self.hours):
                self.custom_heights[index] = height
                # self.layout.itemAt(index).widget().setFixedHeight(height)
                widget = self.layout.itemAt(index).widget()
                self.layout.setStretchFactor(widget, height)

    def set_height_by_widget(self, start_hour, end_hour, widget):
        """Set the height of intervals to match the height of another widget."""
        hours = self.hours
        start_index = hours.index(start_hour)
        end_index = hours.index(end_hour)
        widget_height = widget.height()
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
                print(f"Task '{dragged_task_widget.task.title}' "
                      f"moved from {source_list_widget.parent_time_block_widget.name} "
                      f"to {self.parent_time_block_widget.name}")
                event.ignore()
                source_list_widget.parent_time_block_widget.remove_task(dragged_task_widget.task)
                self.parent_time_block_widget.add_task(dragged_task_widget.task)
        else:
            super().dropEvent(event)

    def on_rows_moved(self, parent, start, end, destination, row):
        """
        Optional: React to reordering within the same list.
        'parent', 'destination' are model indexes, while 'start', 'end', 'row' are row indices.
        """
        print("Rows moved internally in DraggableListWidget")
        # Implement reorder logic if needed.


class TimeBlockWidget(QWidget):
    def __init__(self, parent, time_block: TimeBlock):
        super().__init__(parent)

        self.time_block = time_block
        self.name = self.time_block.name
        self.color = self.time_block.color

        # Convert start_time and end_time from time objects to strings ("HH:MM")
        self.start_time = self.time_block.start_time.strftime("%H:%M") if self.time_block.start_time else "00:00"
        self.end_time = self.time_block.end_time.strftime("%H:%M") if self.time_block.end_time else "00:00"

        empty = (self.time_block.block_type == "empty")
        unavailable = (self.time_block.block_type == "unavailable")

        self.start_hour = int(self.start_time.split(':')[0])
        self.end_hour = int(self.end_time.split(':')[0])
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
        # self.frame.setFixedHeight(self.base_height)

        self.schedule_manager = parent.schedule_manager if parent and hasattr(parent, 'schedule_manager') else None
        self.tasks = self.time_block.tasks

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
        self.setup_frame("No tasks", (47, 47, 47))

    def init_ui_unavailable(self):
        self.setup_frame("Unavailable", (231, 131, 97))

    def load_tasks(self):
        for task in self.tasks:
            self.add_task(task)

    def add_task(self, task):
        # TODO: convert this task item to a TaskWidget if needed
        task_widget = ScheduleTaskWidget(self.schedule_manager.task_manager, task)
        item = QListWidgetItem()
        item.setSizeHint(task_widget.sizeHint())
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, task_widget)
        self.resize_frame_and_hour_cells()

    def remove_task(self, task):
        """
        Removes the specified task from both the widget's internal list (self.tasks)
        and the QListWidget display.
        """
        # 1) Locate the matching item in the QListWidget
        item_to_remove = None
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            task_widget = self.task_list.itemWidget(item)
            if task_widget and task_widget.task == task:
                item_to_remove = item
                break

        # 2) remove from the QListWidget and from self.tasks if found
        if item_to_remove is not None:
            row = self.task_list.row(item_to_remove)
            self.task_list.takeItem(row)  # Removes from UI
            if task in self.tasks:
                self.tasks.remove(task)  # Remove from internal list

            # 3) Adjust minimum height if block to shrink
            self.resize_frame_and_hour_cells()

    def resize_frame_and_hour_cells(self):
        """
        1) Recalculate the widget's minimum height based on the
           current tasks in the QListWidget.
        2) Update the corresponding hour cells in the parent
           ScheduleViewWidget's HourScaleWidget.
        """
        # --- 1) Recalculate the minimum height ---
        if self.task_list.count() == 0:
            new_height = self.base_height
        else:
            task_height = self.name_label.height() + sum(
                self.task_list.sizeHintForRow(i) for i in range(self.task_list.count()))+15
            if self.base_height >= task_height:
                new_height = max(task_height, max(45 * (self.end_hour - self.start_hour), 45))
            else:
                new_height = max(task_height, self.base_height)

        self.base_height = new_height + (self.task_list.frameWidth()*2)
        self.setMinimumHeight(self.base_height)
        self.task_list.adjustSize()

        # --- 2) Update hour cells in the parent (if available) ---
        p = self.parent()
        if isinstance(p, ScheduleViewWidget):
            QTimer.singleShot(0, p.update_time_cell_heights)

    def on_rows_moved(self, row):
        # TODO: implement reorder logic. (probably by changing weights)
        pass


class ScheduleViewWidget(QWidget):
    def __init__(self, schedule_manager=None):
        super().__init__()
        self.schedule_manager = schedule_manager
        self.time_blocks = self.schedule_manager.get_day_schedule(
            "2024-12-20").get_full_day_schedule() if self.schedule_manager else []
        self.initUI()
        self.load_time_blocks()

    def initUI(self):
        self.setFixedWidth(300)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        topLayout = QHBoxLayout()

        self.expandBtn = QPushButton("Expand")
        self.quickTaskBtn = QPushButton("Add Quick Task")
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        topLayout.addWidget(self.expandBtn)
        topLayout.addItem(spacer)
        topLayout.addWidget(self.quickTaskBtn)
        self.mainLayout.addLayout(topLayout)

        viewSelectorLayout = QHBoxLayout()
        self.prevBtn = QPushButton("<")
        self.viewLabel = QLabel("Day")
        self.nextBtn = QPushButton(">")
        viewSelectorLayout.addWidget(self.prevBtn)
        viewSelectorLayout.addWidget(self.viewLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        viewSelectorLayout.addWidget(self.nextBtn)
        self.mainLayout.addLayout(viewSelectorLayout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.container = QWidget()
        self.timeAndTasksLayout = QHBoxLayout(self.container)
        self.timeAndTasksLayout.setContentsMargins(0, 0, 0, 0)
        self.timeAndTasksLayout.setSpacing(0)

        self.timeScaleWidget = HourScaleWidget()
        self.timeBlocksLayout = QVBoxLayout()
        self.timeBlocksLayout.setContentsMargins(0, 0, 0, 0)
        self.timeBlocksLayout.setSpacing(0)

        self.timeAndTasksLayout.addWidget(self.timeScaleWidget)
        self.timeAndTasksLayout.addLayout(self.timeBlocksLayout)
        scroll_area.setWidget(self.container)

        self.mainLayout.addWidget(scroll_area)
        self.setLayout(self.mainLayout)

    def load_time_blocks(self):
        if not self.time_blocks:
            return

        for block in self.time_blocks:
            tb_widget = TimeBlockWidget(self, block)
            stretch_factor = tb_widget.base_height
            # TODO: If total_base is large scale it
            # stretch_factor = int((block.base_height / total_base) * 100) or smn
            self.timeBlocksLayout.addWidget(tb_widget, stretch=stretch_factor)

        QTimer.singleShot(0, self.update_time_cell_heights)

    def update_time_cell_heights(self):
        self.updateGeometry()
        QApplication.processEvents()
        for i in range(self.timeBlocksLayout.count()):
            tb_widget = self.timeBlocksLayout.itemAt(i).widget()
            if tb_widget:
                start_hour = int(tb_widget.start_time.split(':')[0])
                end_hour = int(tb_widget.end_time.split(':')[0])

                self.timeScaleWidget.set_height_by_widget(
                    f"{start_hour - 12 if start_hour > 12 else start_hour} {"AM" if start_hour < 12 else "PM"}",
                    f"{end_hour - 12 if end_hour > 12 else end_hour} {"AM" if end_hour < 12 else "PM"}", tb_widget)

    def print_time_block_heights(self):
        for i in range(self.timeBlocksLayout.count()):
            tb_widget = self.timeBlocksLayout.itemAt(i).widget()

    def add_time_block(self, time_block_widget):
        self.timeBlocksLayout.addWidget(time_block_widget)
