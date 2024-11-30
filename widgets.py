from PIL.ImageChops import offset
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from datetime import datetime
from task_manager import *
from control import *
from gui import global_signals
import random

DUE_TODAY_COLOR = "#4fa7f2"
DUE_TOMORROW_COLOR = "#648742"
PAST_DUE_COLOR = "#ec4f4f"
DUE_THIS_WEEK_COLOR = "orange"
DEFAULT_COLOR = "white"


class TaskWidget(QWidget):
    def __init__(self, task_list_widget, task):
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
        self.task_list_widget.task_list.update_task(self.task)

    def update_task_due_time(self, due_time):
        self.task.due_time = due_time
        self.task_list_widget.task_list.update_task(self.task)

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

    def move_to_list(self, name):
        self.task.list_name = name
        self.task_list_widget.task_list.update_task(self.task)
        global_signals.task_list_updated.emit()

    def delete_task(self):
        self.task_list_widget.delete_task(self.task)

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
        self.task_list_widget.task_list.update_task(self.task)

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
        try:
            dialog = TaskDetailDialog(self.task, self.task_list_widget, self)
            global_signals.task_list_updated.emit()
            dock_widget = self.task_list_widget
            if dock_widget:
                dock_pos = dock_widget.mapToGlobal(QPoint(0, 0))
                dock_size = dock_widget.size()
                offset = int(0.2 * dock_size.width())
                dialog_width = dock_size.width() - offset
                dialog_height = dock_size.height()
                dialog_x = dock_pos.x() + offset
                dialog_y = dock_pos.y()
                dialog.resize(dialog_width, dialog_height)
                dialog.move(dialog_x, dialog_y)
                dialog.setFixedSize(dialog_width, dialog_height)
            else:
                dialog.adjustSize()
                dialog.move(self.mapToGlobal(QPoint(0, 0)))
            dialog.exec()
        except Exception as e:
            print(f"Error in edit_task: {e}")

    def task_checked(self, state):
        try:
            if bool(state):
                self.task.set_completed()
            self.task_list_widget.task_list.update_task(self.task)
            global_signals.task_list_updated.emit()
            self.task_list_widget.parent.history_dock.update_history()
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
            self.task_list_widget.task_list.update_task(self.task)
            global_signals.task_list_updated.emit()
        except Exception as e:
            print(f"Error in mark_important: {e}")


class TaskListWidget(QListWidget):
    def __init__(self, task_list, parent):
        super().__init__()
        self.task_list = task_list
        self.task_list_name = task_list.list_name
        self.parent = parent
        self.manager = self.parent.task_manager
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.load_tasks()
        global_signals.task_list_updated.connect(self.load_tasks)
        self.model().rowsMoved.connect(self.on_rows_moved)

    def filter_tasks(self, text):
        first_visible_item = None
        for index in range(self.count()):
            item = self.item(index)
            task_widget = self.itemWidget(item)
            task = task_widget.task
            match_found = False
            if text.lower() in task.title.lower() or text.lower() in task.description.lower():
                match_found = True
            for subtask in task.subtasks:
                if text.lower() in subtask.title.lower():
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
                task.order = index
                self.task_list.update_task(task)
                self.task_list.stack = False
                self.task_list.queue = False
                self.task_list.priority = False
                self.manager.update_task_list(self.task_list)

    def load_tasks(self):
        filtered = False
        if self.task_list.queue or self.task_list.stack or self.task_list.priority:
            filtered = True
        priority_filter = self.task_list.priority
        try:
            self.task_list.tasks = self.task_list.load_tasks()
            self.clear()

            if not filtered:
                tasks = sorted(self.task_list.get_tasks(), key=lambda task: task.order)
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
        except Exception as e:
            print(f"Error in load_tasks: {e}")

    def delete_task(self, task):
        try:
            self.task_list.remove_task(task)
            for index in range(self.count()):
                item = self.item(index)
                task_widget = self.itemWidget(item)
                if task_widget.task == task:
                    self.takeItem(index)
                    break
        except Exception as e:
            print(f"Error in delete_task: {e}")

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
                    f"Task '{dragged_task_widget.task.title}' moved from {source_widget.objectName()} to {self.task_list_name}")
        super().dropEvent(event)
        global_signals.task_list_updated.emit()


class TaskListManagerToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_action("+", parent, parent.task_list_collection.add_task_list)
        self.add_action("T", parent, parent.toggle_stacked_task_list)
        self.add_action("H", parent, parent.toggle_history)
        self.add_action("C", parent, parent.toggle_calendar)
        self.setObjectName("taskListManagerToolbar")

    def add_action(self, text, parent, function):
        action = QAction(text, parent)
        action.triggered.connect(function)
        self.addAction(action)


class CustomTreeWidget(QTreeWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loaded = False
        self.parent = parent
        self.task_manager = self.parent.task_manager
        self.itemExpanded.connect(self.save_tree_data)
        self.itemCollapsed.connect(self.save_tree_data)
        self.itemChanged.connect(self.save_tree_data)

    def dragLeaveEvent(self, event):
        event.accept()
        if self.currentItem().parent():
            unique_id = random.randint(1000, 9999)
            self.dock_widget = TaskListDock(self.currentItem().text(0), self.parent)
            self.dock_widget.setObjectName(f"TaskListDock_{self.currentItem().text(0)}_{unique_id}")
            self.dock_widget.start_drag()
            self.dock_widget.show()

    def save_tree_data(self):
        if self.loaded:
            print("saved")

    def dropEvent(self, event):
        dragged_item = self.currentItem()
        drop_position = event.position().toPoint()
        dragged_item_parent = dragged_item.parent()
        target_item = self.itemAt(drop_position)

        top_level_items = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]

        if dragged_item.parent() is not None:
            if target_item is None:
                event.ignore()
                return

        if dragged_item in top_level_items:
            if target_item is not None and target_item not in top_level_items:
                event.ignore()
                return

        if dragged_item.parent() is not None and target_item is not None:
            old_parent = dragged_item.parent()
            new_parent = target_item if target_item in top_level_items else target_item.parent()

            if old_parent != new_parent:
                task_list_name = dragged_item.text(0)
                new_category_name = new_parent.text(0) if new_parent else None
                if new_category_name == "Uncategorized":
                    new_category_name = None
                self.task_manager.update_task_list_category(task_list_name, new_category_name)

        super().dropEvent(event)

        if dragged_item in top_level_items:
            dragged_item_parent_current = dragged_item.parent()
            if dragged_item_parent_current is not None:
                dragged_item_parent_current.takeChild(dragged_item_parent_current.indexOfChild(dragged_item))
                self.addTopLevelItem(dragged_item)

        if dragged_item not in top_level_items:
            dragged_item_parent_current = dragged_item.parent()
            if dragged_item_parent_current is None:
                self.takeTopLevelItem(self.indexOfTopLevelItem(dragged_item))
                dragged_item_parent.addChild(dragged_item)

        self.print_structure()

    def print_structure(self):
        def print_item(item, indent=0):
            print(' ' * indent + f"- {item.text(0)} (Expanded: {item.isExpanded()})")
            for i in range(item.childCount()):
                print_item(item.child(i), indent + 2)

        for i in range(self.topLevelItemCount()):
            category_name = self.topLevelItem(i).text(0)
            new_order = i
            self.task_manager.update_category_order(category_name, new_order)
            for j in range(self.topLevelItem(i).childCount()):
                self.task_manager.update_task_list_order(self.topLevelItem(i).child(j).text(0), j)


class TaskListCollection(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.task_manager = self.parent.task_manager

        self.setup_ui()
        self.load_task_lists()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.layout.addWidget(self.search_bar)
        self.search_bar.textChanged.connect(self.filter_items)
        self.task_list_widget_in_focus_before_search = None

        self.tree_widget = CustomTreeWidget(self.parent)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.task_list_collection_context_menu)
        self.tree_widget.itemClicked.connect(self.switch_stack_widget_by_item)
        self.tree_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree_widget.expandAll()
        self.layout.addWidget(self.tree_widget)

    def filter_items(self, text):
        self.tree_widget.clearSelection()
        first_match_task_list_name = None

        if not self.task_list_widget_in_focus_before_search:
            self.task_list_widget_in_focus_before_search = self.parent.stacked_task_list.stack_widget.currentWidget()

        if not text:
            # Show all items when the search bar is empty
            for i in range(self.tree_widget.topLevelItemCount()):
                category_item = self.tree_widget.topLevelItem(i)
                category_item.setHidden(False)
                for j in range(category_item.childCount()):
                    task_list_item = category_item.child(j)
                    task_list_item.setHidden(False)
            if self.task_list_widget_in_focus_before_search:
                self.parent.stacked_task_list.stack_widget.setCurrentWidget(
                    self.task_list_widget_in_focus_before_search)
                self.task_list_widget_in_focus_before_search = None
            return

        # Iterate over categories and task lists to match the search term
        for i in range(self.tree_widget.topLevelItemCount()):
            category_item = self.tree_widget.topLevelItem(i)
            category_visible = False
            # Check if the category name matches the search term
            if text.lower() in category_item.text(0).lower():
                category_visible = True
            # Iterate over task lists in the category
            for j in range(category_item.childCount()):
                task_list_item = category_item.child(j)
                task_list_visible = False
                # Check if the task list name matches the search term
                if text.lower() in task_list_item.text(0).lower():
                    task_list_visible = True
                # Load tasks and check if any task or its subtasks match the search term
                task_list_name = task_list_item.text(0)
                task_list = self.parent.task_lists[task_list_name]
                tasks = task_list.load_tasks()
                for task in tasks:
                    # Check task title, description, and subtasks
                    if text.lower() in task.title.lower() or text.lower() in task.description.lower():
                        task_list_visible = True
                        break
                    # Check subtasks
                    for subtask in task.subtasks:
                        if text.lower() in subtask.title.lower() or text.lower():
                            task_list_visible = True
                            break
                    if task_list_visible:
                        break
                # Show or hide the task list item based on the search result
                task_list_item.setHidden(not task_list_visible)
                if task_list_visible:
                    category_visible = True
                    if first_match_task_list_name is None:
                        first_match_task_list_name = task_list_name
                else:
                    # Hide task lists that don't match
                    task_list_item.setHidden(True)
            # Show or hide the category item based on whether any of its task lists are visible
            category_item.setHidden(not category_visible)

        # Bring the first matching task list into focus
        if first_match_task_list_name:
            self.select_task_list_in_tree(first_match_task_list_name)
            self.parent.stacked_task_list.show_task_list(first_match_task_list_name)

    def load_task_lists(self):
        try:
            self.tree_widget.clear()
            self.categories = self.task_manager.get_categories()

            sorted_categories = sorted(
                self.categories.items(),
                key=lambda item: (item[1]['order'] if item[1]['order'] is not None else float('inf'), item[0])
            )

            for category_name, category_info in sorted_categories:
                # Create QTreeWidgetItem for the category
                category_item = QTreeWidgetItem(self.tree_widget)
                category_item.setText(0, category_name)
                category_item.setExpanded(True)
                category_item.setFlags(category_item.flags())
                category_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'category', 'name': category_name})

                # Ensure that empty categories are still shown
                if category_info.get('task_lists'):  # If the category has task lists
                    # Sort task lists by their order
                    sorted_task_lists = sorted(
                        category_info['task_lists'],
                        key=lambda task_list: task_list['order']
                    )

                    for task_list_info in sorted_task_lists:
                        task_list_name = task_list_info["list_name"]

                        task_list_item = QTreeWidgetItem(category_item)
                        task_list_item.setFlags(task_list_item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
                        task_list_item.setText(0, task_list_name)
                        task_list_item.setData(0, Qt.ItemDataRole.UserRole,
                                               {'type': 'task_list', 'info': task_list_info})
                        task_list_item.setFlags(task_list_item.flags())

                        if task_list_name in self.parent.task_lists:
                            task_list = self.parent.task_lists[task_list_name]
                        else:
                            task_list = TaskList(
                                task_list_name,
                                self.task_manager,
                                task_list_info["queue"],
                                task_list_info["stack"],
                                task_list_info["priority"]
                            )
                            self.parent.task_lists[task_list_name] = task_list

                        hash_key = hash(task_list_name)
                        if hash_key not in self.parent.hash_to_widget:
                            task_list_widget = TaskListWidget(task_list, self.parent)
                            self.parent.stacked_task_list.stack_widget.addWidget(task_list_widget)
                            self.parent.hash_to_widget[hash_key] = task_list_widget
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Task Lists", f"An error occurred: {e}")
            print(f"Error loading task lists: {e}")

    def add_category(self):
        category_name, ok = QInputDialog.getText(self, "New Category", "Enter category name:")
        if ok and category_name.strip():
            category_name = category_name.strip()
            if category_name in self.categories:
                QMessageBox.warning(self, "Duplicate Category", "A category with this name already exists.")
                return
            self.categories[category_name] = []
            self.task_manager.add_category(category_name)
            self.load_task_lists()

    def add_task_list(self):
        try:
            task_list_name, ok = QInputDialog.getText(self, "New Task List", "Enter task list name:")
            if ok and task_list_name.strip():
                task_list_name = task_list_name.strip()
                # Check for duplicates
                if any(task_list_name == task_list["list_name"] for category in self.categories.values() for task_list
                       in category['task_lists']):
                    QMessageBox.warning(self, "Duplicate Task List", "A task list with this name already exists.")
                    return
                # Ask if the user wants to assign a category
                assign_category_reply = QMessageBox.question(
                    self,
                    'Assign Category',
                    'Do you want to assign a category to this task list?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                category_name = None
                if assign_category_reply == QMessageBox.StandardButton.Yes:
                    category_names = [name for name in self.categories.keys() if name != "Uncategorized"]
                    category_name, ok = QInputDialog.getItem(
                        self,
                        "Select Category",
                        "Choose a category:",
                        category_names,
                        editable=False
                    )
                    if not ok:
                        category_name = None  # User canceled category selection
                # Add the task list
                self.task_manager.add_task_list(task_list_name, queue=False, stack=False,
                                                category=category_name)
                # Update self.categories
                self.categories = self.task_manager.get_categories()
                self.load_task_lists()
                # Add to the stack widget
                task_list_widget = TaskListWidget(self.parent.task_lists[task_list_name], self.parent)
                self.parent.stacked_task_list.stack_widget.addWidget(task_list_widget)
                self.parent.hash_to_widget[hash(task_list_name)] = task_list_widget
                self.parent.stacked_task_list.stack_widget.setCurrentWidget(task_list_widget)
                self.select_task_list_in_tree(task_list_name)
        except Exception as e:
            QMessageBox.critical(self, "Error Adding Task List", f"An error occurred: {e}")
            print(f"Error in add_task_list: {e}")

    def add_task_list_to_category(self, category_item):
        # Get the category name
        category_name = category_item.text(0)

        # Ask for a task list name
        task_list_name, ok = QInputDialog.getText(self, "New Task List", "Enter task list name:")
        if ok and task_list_name.strip():
            task_list_name = task_list_name.strip()

            # Check if the task list already exists in the category
            if any(task_list_name == task_list["list_name"] for task_list in
                   self.categories[category_name]['task_lists']):
                QMessageBox.warning(self, "Duplicate Task List",
                                    "A task list with this name already exists in this category.")
                return

            # Add the task list to the category
            self.task_manager.add_task_list(task_list_name, queue=False, stack=False, category=category_name)

            # Reload the task lists and update the UI
            self.categories = self.task_manager.get_categories()
            self.load_task_lists()
        else:
            QMessageBox.warning(self, "Invalid Name", "Task list name cannot be empty.")

    def select_task_list_in_tree(self, task_list_name):
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.text(0) == task_list_name:
                self.tree_widget.setCurrentItem(item)
                break
            iterator += 1

    def switch_stack_widget_by_item(self, item, column):
        if item.parent():
            # This is a task list item
            task_list_name = item.text(0)
            hash_key = hash(task_list_name)
            if hash_key in self.parent.hash_to_widget:
                self.parent.stacked_task_list.stack_widget.setCurrentWidget(self.parent.hash_to_widget[hash_key])
                self.parent.stacked_task_list.update_toolbar()

    def task_list_collection_context_menu(self, position):
        try:
            item = self.tree_widget.itemAt(position)
            menu = QMenu()

            if not item:
                # Right-clicked outside the tree widget, add "Add Category" option
                add_category_action = QAction("Add Category", self)
                add_category_action.triggered.connect(self.add_category)
                menu.addAction(add_category_action)
            else:
                # Item is clicked, check if it's a category
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data is None:
                    return

                item_type = data.get('type')

                if item_type == 'task_list':
                    # Task list item
                    task_list_info = data['info']
                    task_list_name = task_list_info["list_name"]

                    rename_action = QAction('Rename Task List', self)
                    delete_action = QAction('Delete Task List', self)

                    rename_action.triggered.connect(lambda: self.rename_task_list(item))
                    delete_action.triggered.connect(lambda: self.delete_task_list(item))

                    menu.addAction(rename_action)
                    menu.addAction(delete_action)

                elif item_type == 'category':
                    # Category item
                    category_name = data['name']

                    # Option to add a task list to this category
                    add_task_list_action = QAction('Add Task List', self)
                    add_task_list_action.triggered.connect(lambda: self.add_task_list_to_category(item))

                    rename_action = QAction('Rename Category', self)
                    delete_action = QAction('Delete Category', self)

                    rename_action.triggered.connect(lambda: self.rename_category(item))
                    delete_action.triggered.connect(lambda: self.delete_category(item))

                    menu.addAction(add_task_list_action)
                    menu.addAction(rename_action)
                    menu.addAction(delete_action)

                else:
                    QMessageBox.warning(self, "Error", "Unknown item type.")

            menu.exec(self.tree_widget.viewport().mapToGlobal(position))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred in context menu: {e}")
            print(f"Error in task_list_collection_context_menu: {e}")

    def rename_task_list(self, item):
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, "Rename Task List", "Enter new name:", text=old_name)
        if ok and new_name.strip():
            new_name = new_name.strip()

            # Check for duplicate task list name
            if any(new_name == task_list["list_name"] for category in self.categories.values() for task_list in
                   category["task_lists"]):
                QMessageBox.warning(self, "Duplicate Task List", "A task list with this name already exists.")
                return

            # Update task list name in the categories structure
            category_name = item.parent().text(0)
            for task_list in self.categories[category_name]['task_lists']:
                if task_list["list_name"] == old_name:
                    task_list["list_name"] = new_name
                    break

            # Update in task manager (database)
            self.task_manager.change_task_list_name_by_name(old_name, new_name)

            # Update in UI
            item.setText(0, new_name)

            # Update hash_to_widget
            self.parent.hash_to_widget[hash(new_name)] = self.parent.hash_to_widget.pop(hash(old_name))

            # Reload task lists and select the renamed task list
            self.load_task_lists()
            self.select_task_list_in_tree(new_name)

    def delete_task_list(self, item):
        task_list_name = item.text(0)
        reply = QMessageBox.question(self, 'Delete Task List', f'Are you sure you want to delete "{task_list_name}"?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from categories
            category_name = item.parent().text(0)
            self.categories[category_name] = [task_list for task_list in self.categories[category_name] if
                                              task_list != task_list_name]
            # Remove from task manager
            self.task_manager.remove_task_list(task_list_name)
            # Remove from UI
            index = self.tree_widget.indexOfTopLevelItem(item)
            if index != -1:
                self.tree_widget.takeTopLevelItem(index)
            else:
                item.parent().removeChild(item)
            # Remove from stack widget
            hash_key = hash(task_list_name)
            if hash_key in self.parent.hash_to_widget:
                widget_to_remove = self.parent.hash_to_widget.pop(hash_key)
                self.parent.stacked_task_list.stack_widget.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()
            self.load_task_lists()

    def rename_category(self, item):
        old_name = item.text(0)
        if old_name == "Uncategorized":
            QMessageBox.warning(self, "Invalid Operation", "Cannot rename the 'Uncategorized' category.")
            return
        if old_name == "Uncategorized":
            QMessageBox.warning(self, "Invalid Operation", "Cannot rename the 'Uncategorized' category.")
            return
        new_name, ok = QInputDialog.getText(self, "Rename Category", "Enter new name:", text=old_name)
        if ok and new_name.strip():
            new_name = new_name.strip()
            if new_name in self.categories:
                QMessageBox.warning(self, "Duplicate Category", "A category with this name already exists.")
                return
            try:
                # Update in task manager
                self.task_manager.rename_category(old_name, new_name)
                # Reload categories
                self.categories = self.task_manager.get_categories()
                # Update UI
                self.load_task_lists()
                # Select the new category
                self.select_category_in_tree(new_name)
            except Exception as e:
                print(f"Error renaming category: {e}")
                QMessageBox.critical(self, "Error", f"An error occurred while renaming the category: {e}")

    def select_category_in_tree(self, category_name):
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.text(0) == category_name and not item.parent():
                self.tree_widget.setCurrentItem(item)
                break
            iterator += 1

    def delete_category(self, item):
        category_name = item.text(0)

        if category_name == "Uncategorized":
            QMessageBox.warning(self, "Invalid Operation", "Cannot delete the 'Uncategorized' category.")
            return

        reply = QMessageBox.question(self, 'Delete Category',
                                     f'Are you sure you want to delete the category "{category_name}" and all its task lists?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove all task lists in the category
                task_lists_in_category = self.categories.get(category_name, {}).get("task_lists", [])
                for task_list_info in task_lists_in_category:
                    task_list_name = task_list_info["list_name"]

                    # Remove from task manager
                    self.task_manager.remove_task_list(task_list_name)

                    # Remove from stack widget
                    hash_key = hash(task_list_name)
                    if hash_key in self.parent.hash_to_widget:
                        widget_to_remove = self.parent.hash_to_widget.pop(hash_key)
                        self.parent.stacked_task_list.stack_widget.removeWidget(widget_to_remove)
                        widget_to_remove.deleteLater()

                # Remove category from the database
                self.task_manager.remove_category(category_name)

                # Remove category from the data structure
                del self.categories[category_name]

                # Remove category from UI (tree widget)
                index = self.tree_widget.indexOfTopLevelItem(item)
                self.tree_widget.takeTopLevelItem(index)

                # Reload task lists to refresh the UI
                self.load_task_lists()

            except Exception as e:
                print(f"Error in delete_category: {e}")


class InfoBar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.task_manager = parent.task_manager
        self.task_list_count_label = QLabel()
        self.update_task_list_count_label()
        self.task_list_count_label.setStyleSheet("font-size: 12px;")
        self.task_list_count_label.setFixedHeight(9)

        # Layout to add the label to the InfoBar
        layout = QHBoxLayout()
        layout.addWidget(self.task_list_count_label)
        layout.addStretch()
        self.setLayout(layout)

    def update_task_list_count_label(self):
        task_count = self.task_manager.get_task_list_count()
        self.task_list_count_label.setText(f"  {task_count}")


class TaskListToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_action("+", parent, parent.add_task)
        self.add_action("Q", parent, parent.set_queue)
        self.add_action("S", parent, parent.set_stack)
        self.add_action("P", parent, parent.priority_sort)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def add_action(self, text, parent, function):
        action = QAction(text, parent)
        action.triggered.connect(function)
        self.addAction(action)


class TaskListDockStacked(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Tasks", parent)
        self.type = "stack"
        self.priority_filter = False
        self.parent = parent
        self.task_manager = self.parent.task_manager
        self.set_allowed_areas()
        self.setup_ui()
        self.setObjectName("taskListDockStacked")
        self.toolbar.setObjectName("taskListToolbar")
        self.stack_widget.setObjectName("stackWidget")

    def filter_current_task_list(self, text):
        current_task_list_widget = self.get_current_task_list_widget()
        if current_task_list_widget:
            current_task_list_widget.filter_tasks(text)

    def show_task_list(self, task_list_name):
        hash_key = hash(task_list_name)
        if hash_key in self.parent.hash_to_widget:
            task_list_widget = self.parent.hash_to_widget[hash_key]
            self.stack_widget.setCurrentWidget(task_list_widget)
            self.update_toolbar()
            search_text = self.parent.task_list_collection.search_bar.text()
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
            self.toolbar.actions()[1].setChecked(current_task_list.queue)
            self.toolbar.actions()[2].setCheckable(True)
            self.toolbar.actions()[2].setChecked(current_task_list.stack)
            self.toolbar.actions()[3].setCheckable(True)
            self.toolbar.actions()[3].setChecked(current_task_list.priority)
        except Exception as e:
            print(e)

    def setup_stack_widget(self):
        self.stack_widget = QStackedWidget()
        self.layout.addWidget(self.stack_widget)

    def add_task(self):
        current_task_list_widget = self.get_current_task_list_widget()
        self.show_add_task_dialog(current_task_list_widget)

    def show_add_task_dialog(self, task_list_widget):
        try:
            dialog = AddTaskDialog(self)
            button_pos = self.toolbar.mapToGlobal(self.toolbar.rect().bottomRight())
            dialog.adjustSize()
            dialog.move(button_pos.x() - dialog.width(), button_pos.y())
            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.get_task_data()
                task = Task(**task_data)
                task_list_widget.task_list.add_task(task)
                global_signals.task_list_updated.emit()
        except Exception as e:
            print(f"An error occurred while adding a task: {e}")

    def set_queue(self):
        try:
            current_task_list_widget = self.stack_widget.currentWidget()
            if not isinstance(current_task_list_widget, TaskListWidget):
                return
            current_task_list = current_task_list_widget.task_list
            current_task_list.queue = not current_task_list.queue
            self.toolbar.actions()[1].setCheckable(True if current_task_list.queue else False)
            self.toolbar.actions()[1].setChecked(current_task_list.queue)
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
            current_task_list.stack = not current_task_list.stack
            self.toolbar.actions()[2].setCheckable(True if current_task_list.stack else False)
            self.toolbar.actions()[2].setChecked(current_task_list.stack)
            self.toolbar.actions()[1].setCheckable(False)
            self.toolbar.actions()[3].setCheckable(False)
            self.priority_filter = False
            current_task_list.queue = False
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
            current_task_list.priority = not current_task_list.priority
            self.toolbar.actions()[3].setCheckable(True if not self.priority_filter else False)
            self.toolbar.actions()[3].setChecked(True if not self.priority_filter else False)
            self.toolbar.actions()[2].setCheckable(False)
            self.toolbar.actions()[1].setCheckable(False)
            self.priority_filter = not self.priority_filter
            current_task_list_widget.load_tasks()
            self.task_manager.update_task_list(current_task_list)
        except Exception as e:
            print(f"Error in priority_sort: {e}")

    def get_current_task_list_widget(self):
        current_widget = self.stack_widget.currentWidget()
        return current_widget if isinstance(current_widget, TaskListWidget) else None


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

        task_list = self.parent.task_lists.get(task_list_name,
                                               TaskList(task_list_name, self.task_manager, False, False, False))
        self.parent.task_lists[task_list_name] = task_list
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

    def setup_toolbar(self):
        self.toolbar = TaskListToolbar(self)
        self.layout.addWidget(self.toolbar)

    def add_task(self):
        self.show_add_task_dialog(self.task_list_widget)

    def show_add_task_dialog(self, task_list_widget):
        try:
            dialog = AddTaskDialog(self)
            button_pos = self.toolbar.mapToGlobal(self.toolbar.rect().bottomRight())
            dialog.adjustSize()
            dialog.move(button_pos.x() - dialog.width(), button_pos.y())
            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.get_task_data()
                task = Task(**task_data)
                task_list_widget.task_list.add_task(task)
                global_signals.task_list_updated.emit()
        except Exception as e:
            print(f"An error occurred while adding a task: {e}")

    def set_queue(self):
        try:
            task_list = self.task_list_widget.task_list
            task_list.queue = not task_list.queue
            self.toolbar.actions()[1].setCheckable(task_list.queue)
            self.toolbar.actions()[1].setChecked(task_list.queue)
            task_list.stack = False
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
            task_list.stack = not task_list.stack
            self.toolbar.actions()[2].setCheckable(task_list.stack)
            self.toolbar.actions()[2].setChecked(task_list.stack)
            self.toolbar.actions()[1].setCheckable(False)
            self.toolbar.actions()[3].setCheckable(False)
            self.priority_filter = False
            task_list.queue = False
            self.task_list_widget.load_tasks()
            self.task_manager.update_task_list(task_list)
        except Exception as e:
            print(f"Error in set_stack: {e}")

    def priority_sort(self):
        try:
            task_list = self.task_list_widget.task_list
            task_list.priority = not task_list.priority
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

        for task_list_info in self.parent.task_manager.get_task_lists():
            task_list = TaskList(task_list_info["list_name"], self.parent.task_manager,
                                 task_list_info["queue"], task_list_info["stack"])
            task_list.refresh_tasks()
            completed_tasks = task_list.get_completed_tasks()

            if search_text:
                completed_tasks = [task for task in completed_tasks if search_text in task.title.lower() or
                                   search_text in task.description.lower()]

            if completed_tasks:
                task_list_item = QTreeWidgetItem(self.history_tree)
                task_list_item.setText(0, task_list_info["list_name"])
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
                        task_item.setText(0, task.title)
                        task_item.setText(1, task.last_completed_date.strftime(
                            '%Y-%m-%d %H:%M') if task.last_completed_date else '')
                        task_item.setText(2, task.due_date if task.due_date != "2000-01-01" else '')
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
        if task.list_name in self.parent.task_lists:
            task_list = self.parent.task_lists[task.list_name]
        else:
            task_list = TaskList(task.list_name, self.parent.task_manager)
            self.parent.task_lists[task.list_name] = task_list

        task_list_widget = self.parent.hash_to_widget.get(task.list_name)
        if not task_list_widget:
            task_list_widget = TaskListWidget(task_list, self.parent)
            self.parent.hash_to_widget[task.list_name] = task_list_widget

        dialog = TaskDetailDialog(task, task_list_widget, parent=self)

        dock_widget = self
        if dock_widget:
            dock_pos = dock_widget.mapToGlobal(QPoint(0, 0))
            dock_size = dock_widget.size()

            offset = int(0.2 * dock_size.width())
            dialog_width = dock_size.width() - offset
            dialog_height = dock_size.height()
            dialog_x = dock_pos.x() + offset
            dialog_y = dock_pos.y()

            dialog.resize(dialog_width, dialog_height)
            dialog.move(dialog_x, dialog_y)
            dialog.setFixedSize(dialog_width, dialog_height)
        else:
            dialog.adjustSize()
            dialog.move(self.mapToGlobal(QPoint(0, 0)))

        dialog.exec()

    def restore_task(self, task):
        reply = QMessageBox.question(self, 'Restore Task', 'Are you sure you want to restore this task?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            task.completed = False
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

        task_list_widget = self.parent.hash_to_widget.get(task.list_name)
        if not task_list_widget:
            task_list_widget = TaskListWidget(task_list, self.parent)
            self.parent.hash_to_widget[task.list_name] = task_list_widget

        dialog = TaskDetailDialog(task, task_list_widget, parent=self)
        global_signals.task_list_updated.emit()
        dock_widget = self
        if dock_widget:
            dock_pos = dock_widget.mapToGlobal(QPoint(0, 0))
            dock_size = dock_widget.size()

            offset = int(0.2 * dock_size.width())
            dialog_width = dock_size.width() - offset
            dialog_height = dock_size.height()
            dialog_x = dock_pos.x() + offset
            dialog_y = dock_pos.y()

            dialog.resize(dialog_width, dialog_height)
            dialog.move(dialog_x, dialog_y)
            dialog.setFixedSize(dialog_width, dialog_height)
        else:
            dialog.adjustSize()
            dialog.move(self.mapToGlobal(QPoint(0, 0)))

        dialog.exec()

    def on_task_clicked(self, item):
        pass

    def on_filter_changed(self, index):
        self.highlight_tasks_on_calendar()
        self.load_tasks_for_selected_date()

    def update_calendar(self):
        self.highlight_tasks_on_calendar()
        self.load_tasks_for_selected_date()
