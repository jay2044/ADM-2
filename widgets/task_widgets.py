from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from core.task_manager import *
from core.globals import *
from .task_progress_widgets import *
import random
from datetime import datetime, time


class TaskListWidget(QListWidget):
    def __init__(self, task_list, parent):
        super().__init__()
        self.task_list = task_list
        self.task_list_name = task_list.name
        self.parent = parent
        self.manager = self.parent.task_manager
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.load_tasks()
        global_signals.task_list_updated.connect(self.load_tasks)
        self.model().rowsMoved.connect(self.on_rows_moved)

    def multi_selection_mode(self):
        self.clear()

        # Determine if any sorting filter is active
        filtered = any([
            self.task_list.sort_by_queue,
            self.task_list.sort_by_stack,
            self.task_list.sort_by_priority,
            self.task_list.sort_by_due_datetime,
            self.task_list.sort_by_time_estimate,
        ])
        priority_filter = self.task_list.sort_by_priority

        try:
            if not filtered:
                tasks = sorted(self.task_list.get_tasks(), key=lambda task: task.list_order)
            else:
                tasks = self.task_list.get_tasks()

            if priority_filter:
                tasks = sorted(tasks, key=lambda task: task.priority, reverse=True)

            for task in tasks:
                print(f"Loading task in multi-select mode: {task.name}")  # Debug
                item = QListWidgetItem(task.name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.addItem(item)
        except Exception as e:
            print(f"Error in multi_selection_mode: {e}")

    def get_selected_items(self):
        selected_items = []
        for index in range(self.count()):
            item = self.item(index)
            if item and item.checkState() == Qt.CheckState.Checked:
                selected_items.append(item.text())
        return selected_items

    def select_all_items(self):
        for index in range(self.count()):
            item = self.item(index)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def clear_selection_all_items(self):
        for index in range(self.count()):
            item = self.item(index)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def delete_selected_items(self):
        tasks_to_delete = self.get_selected_items()
        tasks = self.task_list.get_tasks()
        for index in reversed(range(self.count())):
            item = self.item(index)
            if item and item.text() in tasks_to_delete:
                for task in tasks:
                    if task.name == item.text():
                        self.delete_task(task)
                        print(f"Deleted {item.text()}")
                        self.takeItem(index)
        global_signals.task_list_updated.emit()

    def move_selected_items(self):
        tasks_to_move = self.get_selected_items()
        tasks = self.task_list.get_tasks()

        # Create a context menu for selecting the destination list
        move_to_menu = QMenu("Move To", self)
        categories_tasklists = self.manager.get_category_tasklist_names()

        # Populate the menu with categories and task lists
        for category, task_lists in categories_tasklists.items():
            if task_lists:
                category_menu = QMenu(category, self)
                for list_name in task_lists:
                    if list_name != self.task_list_name:  # Exclude current list
                        move_to_action = QAction(list_name, self)
                        move_to_action.triggered.connect(
                            lambda _, name=list_name: self.perform_move(tasks_to_move, name))
                        category_menu.addAction(move_to_action)
                if not category_menu.isEmpty():
                    move_to_menu.addMenu(category_menu)

        # Display the menu
        cursor_position = self.cursor().pos()  # Get the current cursor position
        move_to_menu.exec(cursor_position)

    def perform_move(self, tasks_to_move, new_list_name):
        tasks = self.task_list.get_tasks()
        for index in reversed(range(self.count())):
            item = self.item(index)
            if item and item.text() in tasks_to_move:
                for task in tasks:
                    if task.name == item.text():
                        task.list_name = new_list_name
                        self.manager.update_task(task)
                        print(f"Moved {item.text()} to {new_list_name}")
                        self.takeItem(index)
        global_signals.task_list_updated.emit()

    def filter_tasks(self, text):
        first_visible_item = None
        for index in range(self.count()):
            item = self.item(index)
            task_widget = self.itemWidget(item)
            task = task_widget.task
            match_found = False
            if text.lower() in task.name.lower() or text.lower() in task.description.lower():
                match_found = True
            if task.subtasks:
                for subtask in task.subtasks:
                    if text.lower() in subtask["name"].lower():
                        match_found = True
                        break
            item.setHidden(not match_found)
            if match_found and first_visible_item is None:
                first_visible_item = item
        if first_visible_item:
            self.scrollToItem(first_visible_item)

    def on_rows_moved(self):
        self.update_task_order()

    def update_task_order(self):
        for index in range(self.count()):
            item = self.item(index)
            task_widget = self.itemWidget(item)
            if task_widget:
                task = task_widget.task
                task.list_order = index
                self.manager.update_task(task)
                self.task_list.disable_all_filters()
                self.manager.update_task_list(self.task_list)

    def load_tasks(self):
        # Determine if any sorting filter is active
        filtered = any([
            self.task_list.sort_by_queue,
            self.task_list.sort_by_stack,
            self.task_list.sort_by_priority,
            self.task_list.sort_by_due_datetime,
            self.task_list.sort_by_time_estimate,
        ])
        priority_filter = self.task_list.sort_by_priority
        # try:
        self.clear()

        if not filtered:
            tasks = sorted(self.task_list.get_tasks(), key=lambda task: task.list_order)
        else:
            tasks = self.task_list.get_tasks()

        if priority_filter:
            tasks = sorted(tasks, key=lambda task: task.priority, reverse=True)

        for task in tasks:
            task_widget = TaskWidget(self, task)
            item = QListWidgetItem()
            item.setSizeHint(task_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, task_widget)
        self.in_multi_selection_mode = False
        # except Exception as e:
        #     print(f"Error in load_tasks: {e}")

    def delete_task(self, task):
        self.manager.remove_task(task)
        try:
            for index in range(self.count()):
                item = self.item(index)
                task_widget = self.itemWidget(item)
                if task_widget.task == task:
                    self.takeItem(index)
                    break
        except Exception as e:
            print(f"Error in delete_task: {e}")
        global_signals.task_list_updated.emit()

    def startDrag(self, supportedActions):
        print("yo")
        item = self.currentItem()
        if item:
            task_widget = self.itemWidget(item)
            if task_widget:
                self.dragged_task_widget = task_widget
        super().startDrag(supportedActions)

    def dropEvent(self, event):
        if event.source() != self:
            source_widget = event.source()
            dragged_task_widget = getattr(source_widget, "dragged_task_widget", None)
            if dragged_task_widget:
                dragged_task_widget.move_to_list(self.task_list_name)
                print(
                    f"Task '{dragged_task_widget.task.name}' moved from {source_widget.objectName()} to {self.task_list_name}")
        super().dropEvent(event)
        global_signals.task_list_updated.emit()


class TaskWidget(QWidget):
    def __init__(self, task_list_widget: TaskListWidget, task: Task):
        super().__init__()
        self.task_list_widget = task_list_widget
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
        self.checkbox.setChecked(bool(self.task.status == "Completed"))
        self.checkbox.stateChanged.connect(self.task_checked)
        self.layout.addWidget(self.checkbox)
        self.task_label = QLabel(self.task.name)
        self.task_label.setStyleSheet("font-size: 14px; text-decoration: none;")
        self.task_label.mousePressEvent = self.on_task_label_click
        self.layout.addWidget(self.task_label)
        if self.task.count_required or self.task.time_estimate or self.task.subtasks:
            self.progress_bar = TaskProgressBar(self.task)
            self.layout.addWidget(self.progress_bar)
        self.layout.addStretch()
        self.due_label = QLabel()
        self.due_label.setStyleSheet("font-size: 14px;")
        self.due_label.mousePressEvent = self.pick_due_date
        self.layout.addWidget(self.due_label)
        self.radio_button = QRadioButton()
        self.radio_button.setChecked(bool(self.task.is_important()))
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
            move_to_menu = QMenu("Move To", self)
            categories_tasklists = self.task_list_widget.manager.get_category_tasklist_names()
            for category, task_lists in categories_tasklists.items():
                if task_lists:
                    category_menu = QMenu(category, self)
                    for list_name in task_lists:
                        if list_name != self.task_list_widget.task_list_name:
                            move_to_action = QAction(list_name, self)
                            move_to_action.triggered.connect(lambda _, name=list_name: self.move_to_list(name))
                            category_menu.addAction(move_to_action)
                    if not category_menu.isEmpty():
                        move_to_menu.addMenu(category_menu)
            menu.addMenu(move_to_menu)
            duplicate_action = QAction("Duplicate", self)
            duplicate_action.triggered.connect(self.duplicate_task)
            menu.addAction(duplicate_action)
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_task)
            menu.addAction(delete_action)
            menu.exec(self.mapToGlobal(position))

    def remove_due_date(self):
        self.clear_due_datetime()

    def set_due_today(self):
        now = datetime.now().date()
        self.task.due_datetime = datetime.combine(now, time.min)
        self.task_list_widget.manager.update_task(self.task)
        self.update_due_label()

    def set_due_tomorrow(self):
        tomorrow = datetime.now().date() + timedelta(days=1)
        time_component = self.task.due_datetime.time() if self.task.due_datetime else time.min
        self.task.due_datetime = datetime.combine(tomorrow, time_component)
        self.task_list_widget.manager.update_task(self.task)
        self.update_due_label()

    def pick_due_date(self, event):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(dialog)
        dialog.setLayout(layout)

        # Calendar widget
        calendar = QCalendarWidget(dialog)
        if self.task.due_datetime:
            calendar.setSelectedDate(QDate.fromString(
                self.task.due_datetime.strftime("%Y-%m-%d"),
                "yyyy-MM-dd"
            ))
        layout.addWidget(calendar)

        # Time edit widget
        time_edit = QTimeEdit(dialog)
        if self.task.due_datetime:
            time_edit.setTime(QTime.fromString(
                self.task.due_datetime.strftime("%H:%M"),
                "HH:mm"
            ))
        time_edit.setDisplayFormat("h:mm AP")
        layout.addWidget(time_edit)

        # Button layout
        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear Date & Time", dialog)
        clear_button.clicked.connect(self.clear_due_datetime)
        button_layout.addWidget(clear_button)
        layout.addLayout(button_layout)

        # Update function
        def update_due_datetime():
            date = calendar.selectedDate().toPyDate()
            time = time_edit.time().toPyTime()
            self.task.due_datetime = datetime.combine(date, time)
            self.task_list_widget.manager.update_task(self.task)
            self.update_due_label()

        calendar.selectionChanged.connect(update_due_datetime)
        time_edit.timeChanged.connect(update_due_datetime)

        # Position and show dialog
        dialog.move(
            self.due_label.mapToGlobal(QPoint(
                self.due_label.width() // 2,
                self.due_label.height() // 2
            )) - QPoint(
                dialog.width() // 2,
                dialog.height() // 2
            )
        )
        dialog.exec()

    def clear_due_datetime(self):
        self.task.due_datetime = None
        self.task_list_widget.manager.update_task(self.task)
        self.update_due_label()

    def update_due_label(self):
        if not self.task.due_datetime:
            self.due_label.setText("")
            self.due_label.setStyleSheet(f"color: {DEFAULT_COLOR}; font-size: 14px;")
            return

        if isinstance(self.task.due_datetime, str):
            try:
                # Try parsing with 'T' separator first
                self.task.due_datetime = datetime.strptime(self.task.due_datetime, "%Y-%m-%dT%H:%M")
            except ValueError:
                # If it fails, try parsing without the 'T'
                self.task.due_datetime = datetime.strptime(self.task.due_datetime, "%Y-%m-%d %H:%M")

        due_date = self.task.due_datetime.date()
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        end_of_week = today + timedelta(days=(6 - today.weekday()))
        is_this_year = due_date.year == today.year

        # Format the date portion
        if due_date == today:
            formatted_date = "Today"
            color = DUE_TODAY_COLOR
        elif due_date == tomorrow:
            formatted_date = "Tomorrow"
            color = DUE_TOMORROW_COLOR
        elif due_date < today:
            day = due_date.day
            suffix = "th" if 11 <= day <= 13 else ["st", "nd", "rd"][day % 10 - 1] if day % 10 in [1, 2, 3] else "th"
            month_abbr = due_date.strftime("%b")
            year = f" {due_date.year}" if not is_this_year else ""
            formatted_date = f"{day}{suffix} {month_abbr}{year}"
            color = PAST_DUE_COLOR
        elif today < due_date <= end_of_week:
            formatted_date = due_date.strftime("%a")
            color = DUE_THIS_WEEK_COLOR
        else:
            day = due_date.day
            suffix = "th" if 11 <= day <= 13 else ["st", "nd", "rd"][day % 10 - 1] if day % 10 in [1, 2, 3] else "th"
            month_abbr = due_date.strftime("%b")
            year = f" {due_date.year}" if not is_this_year else ""
            formatted_date = f"{day}{suffix} {month_abbr}{year}"
            color = DEFAULT_COLOR

        # Add time if present
        time = self.task.due_datetime.time()
        if time != time.min:
            formatted_time = self.task.due_datetime.strftime("%I:%M %p").lstrip("0")
            formatted_date += f" at {formatted_time}"

        # Update label
        self.due_label.setText(formatted_date)
        self.due_label.setStyleSheet(f"color: {color}; font-size: 14px;")

    def move_to_list(self, name):
        self.task.list_name = name
        self.task_list_widget.manager.update_task(self.task)
        global_signals.task_list_updated.emit()

    def delete_task(self):
        self.task_list_widget.delete_task(self.task)

    def duplicate_task(self):
        self.task_list_widget.manager.add_task(self.task)
        global_signals.task_list_updated.emit()

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
        self.task_list_widget.parent.add_task_detail_dock(self.task)

    def task_checked(self, state):
        try:
            if bool(state):
                self.task.set_completed()
            self.task_list_widget.manager.update_task(self.task)
            global_signals.task_list_updated.emit()
            self.task_list_widget.parent.history_dock.update_history()
        except Exception as e:
            print(f"Error in task_checked: {e}")

    def mark_important(self):
        try:
            if self.radio_button.isChecked():
                self.task.mark_as_important()
            else:
                self.task.unmark_as_important()
            self.task_list_widget.manager.update_task(self.task)
            global_signals.task_list_updated.emit()
        except Exception as e:
            print(f"Error in mark_important: {e}")
