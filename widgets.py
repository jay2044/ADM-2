from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from task_manager import *
from control import *


class TaskWidget(QWidget):
    def __init__(self, task_list_widget, task):
        super().__init__()
        self.task_list_widget = task_list_widget
        self.task = task
        self.is_dragging = False

        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.checkbox = QCheckBox(self.task.title)
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.stateChanged.connect(self.task_checked)
        self.layout.addWidget(self.checkbox)

        self.layout.addStretch()

        self.radio_button = QRadioButton()
        self.radio_button.setChecked(self.task.is_important)
        self.radio_button.toggled.connect(self.mark_important)
        self.layout.addWidget(self.radio_button)

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.edit_task)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.timer.start(250)
            self.start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.is_dragging and (event.pos() - self.start_pos).manhattanLength() > QApplication.startDragDistance():
            self.is_dragging = True
            self.timer.stop()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.timer.isActive():
                self.timer.stop()
                self.edit_task()
        super().mouseReleaseEvent(event)

    def edit_task(self):
        try:
            dialog = EditTaskDialog(self.task, self.task_list_widget, self)
            dialog.adjustSize()

            task_list_widget_geometry = self.task_list_widget.geometry()
            dialog_width = int(task_list_widget_geometry.width() * 0.8)
            dialog_height = task_list_widget_geometry.height()
            dialog_x = self.task_list_widget.mapToGlobal(
                QPoint(task_list_widget_geometry.width() - dialog_width, 0)).x()
            dialog_y = self.task_list_widget.mapToGlobal(QPoint(0, 0)).y()

            dialog.resize(dialog_width, dialog_height)
            dialog.move(dialog_x, dialog_y)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.get_task_data()
                self.task.title = task_data["title"]
                self.task.description = task_data["description"]
                self.task.due_date = task_data["due_date"]
                self.task.due_time = task_data["due_time"]
                self.task.is_important = task_data["is_important"]
                self.task.priority = task_data["priority"]
                self.task_list_widget.task_list.update_task(self.task)
                self.task_list_widget.load_tasks()
        except Exception as e:
            print(f"Error in edit_task: {e}")

    def task_checked(self, state):
        self.task.completed = bool(state)
        self.task_list_widget.task_list.update_task(self.task)
        self.task_list_widget.load_tasks()

    def mark_important(self):
        if self.radio_button.isChecked():
            self.task.mark_as_important()
            self.task.priority = 7
        else:
            self.task.unmark_as_important()
            self.task.priority = 0
        self.task_list_widget.task_list.update_task(self.task)
        self.task_list_widget.load_tasks()


class TaskListWidget(QListWidget):
    def __init__(self, task_list_name, manager, pin, queue, stack):
        super().__init__()
        self.task_list_name = task_list_name
        self.task_list = TaskList(task_list_name, manager, pin, queue, stack)
        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def load_tasks(self, priority_filter=False):
        self.clear()
        tasks = self.task_list.get_tasks_filter_priority() if priority_filter else self.task_list.get_tasks()
        for task in tasks:
            task_widget = TaskWidget(self, task)
            item = QListWidgetItem()
            item.setSizeHint(task_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, task_widget)

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
            print(e)

    def startDrag(self, supportedActions):
        try:
            item = self.currentItem()
            if item:
                drag = QDrag(self)
                mime_data = QMimeData()
                drag.setMimeData(mime_data)

                pixmap = QPixmap(item.sizeHint().width(), item.sizeHint().height())
                item_widget = self.itemWidget(item)
                item_widget.render(pixmap)
                drag.setPixmap(pixmap)

                drag.exec(Qt.DropAction.MoveAction)
        except Exception as e:
            print(f"Error in startDrag: {e}")

    def dragEnterEvent(self, event):
        try:
            if event.source() == self:
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            print(f"Error in dragEnterEvent: {e}")

    def dragMoveEvent(self, event):
        try:
            if event.source() == self:
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            print(f"Error in dragMoveEvent: {e}")


class TaskListManagerToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_action("+", parent, parent.task_list_collection.add_task_list)
        self.add_action("H", parent, parent.toggle_history)
        self.add_action("C", parent, parent.toggle_calendar)

    def add_action(self, text, parent, function):
        action = QAction(text, parent)
        action.triggered.connect(function)
        self.addAction(action)


class TaskListCollection(QListWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.currentItemChanged.connect(self.switch_stack_widget_by_hash)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.task_list_collection_context_menu)

    def load_task_lists(self):
        self.clear()
        for task_list_info in self.parent.task_manager.get_task_lists():
            self.add_task_list(task_list_info["list_name"], pin=task_list_info["pin"],
                               queue=task_list_info["queue"], stack=task_list_info["stack"])

    def add_task_list(self, task_list_name="", pin=False, queue=False, stack=False):
        try:
            if not task_list_name:
                task_list_name, ok = QInputDialog.getText(self, "New Task List", "Enter name:")
                if not ok or not task_list_name.strip():
                    return

            task_list_name = str(task_list_name).strip()

            if any(self.item(i).text() == task_list_name for i in range(self.count())):
                QMessageBox.warning(self, "Duplicate Name", "A task list with this name already exists.")
                return

            self.addItem(task_list_name)
            self.parent.task_manager.add_task_list(task_list_name, pin=pin, queue=queue, stack=stack)
            task_list_widget = TaskListWidget(task_list_name, self.parent.task_manager, pin, queue, stack)
            self.parent.right_dock.stack_widget.addWidget(task_list_widget)
            self.parent.hash_to_widget[hash(task_list_name)] = task_list_widget
            self.parent.right_dock.stack_widget.setCurrentWidget(task_list_widget)
            self.setCurrentItem(self.findItems(task_list_name, Qt.MatchFlag.MatchExactly)[0])
            self.parent.info_bar.update_task_list_count_label()

        except Exception as e:
            print(f"An error occurred while adding a task list: {e}")

    def switch_stack_widget_by_hash(self, current):
        try:
            if current:
                hash_key = hash(current.text())
                if hash_key in self.parent.hash_to_widget:
                    self.parent.right_dock.stack_widget.setCurrentWidget(self.parent.hash_to_widget[hash_key])
        except Exception as e:
            print(f"An error occurred while switching stack: {e}")

    def task_list_collection_context_menu(self, position):
        try:
            task_list = self.itemAt(position)
            if not task_list:
                return

            hash_key = hash(task_list.text())
            task_list_widget = self.parent.hash_to_widget[hash_key]

            menu = QMenu()
            rename_action = QAction('Rename', self)
            pin_action = QAction('Pin', self) if not task_list_widget.task_list.pin else QAction('Unpin', self)
            duplicate_action = QAction('Duplicate', self)
            delete_action = QAction('Delete', self)

            rename_action.triggered.connect(lambda: self.rename_task_list(task_list_widget))
            pin_action.triggered.connect(lambda: self.pin_task_list(task_list))
            duplicate_action.triggered.connect(lambda: self.duplicate_task_list(task_list_widget))
            delete_action.triggered.connect(lambda: self.delete_task_list(task_list))

            menu.addAction(rename_action)
            menu.addAction(pin_action)
            menu.addAction(duplicate_action)
            menu.addAction(delete_action)

            menu.exec(self.viewport().mapToGlobal(position))
        except Exception as e:
            print(f"An error occurred in task_list_collection_context_menu: {e}")

    def rename_task_list(self, task_list_widget):
        try:
            current_name = task_list_widget.task_list.list_name
            task_list_name, ok = QInputDialog.getText(self, "Rename Task List", "Enter name:", text=current_name)
            if not ok or not task_list_name.strip():
                return

            task_list_name = str(task_list_name).strip()
            self.parent.task_manager.change_task_list_name(task_list_widget.task_list, task_list_name)
            self.parent.hash_to_widget[hash(task_list_name)] = task_list_widget
            self.load_task_lists()
        except Exception as e:
            print(f"An error occurred while renaming the task list: {e}")

    def pin_task_list(self, task_list):
        self.parent.task_manager.pin_task_list(task_list.text())
        self.load_task_lists()

    def duplicate_task_list(self, task_list_widget):
        try:
            new_name, ok = QInputDialog.getText(self, "Duplicate Task List", "Enter new name:")
            if not ok or not new_name.strip():
                return

            new_name = str(new_name).strip()

            if any(self.item(i).text() == new_name for i in range(self.count())):
                QMessageBox.warning(self, "Duplicate Name", "A task list with this name already exists.")
                return

            self.parent.task_manager.add_task_list(new_name, pin=task_list_widget.task_list.pin,
                                                   queue=task_list_widget.task_list.queue,
                                                   stack=task_list_widget.task_list.stack)

            for task in task_list_widget.task_list.tasks:
                new_task = Task(
                    title=task.title,
                    description=task.description,
                    due_date=task.due_date,
                    due_time=task.due_time,
                    is_important=task.is_important,
                    priority=task.priority,
                    completed=task.completed,
                    categories=task.categories,
                    recurring=task.recurring,
                    recur_every=task.recur_every
                )
                self.parent.task_manager.add_task(new_task, new_name)

            self.add_task_list(new_name, pin=task_list_widget.task_list.pin,
                               queue=task_list_widget.task_list.queue,
                               stack=task_list_widget.task_list.stack)
        except Exception as e:
            print(f"An error occurred while duplicating the task list: {e}")

    def delete_task_list(self, task_list):
        try:
            row = self.row(task_list)
            hash_key = hash(task_list.text())
            if hash_key in self.parent.hash_to_widget:
                widget_to_remove = self.parent.hash_to_widget.pop(hash_key)
                self.parent.right_dock.stack_widget.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()
            self.takeItem(row)
            self.parent.task_manager.remove_task_list(task_list.text())
            self.parent.info_bar.update_task_list_count_label()
        except Exception as e:
            print(f"An error occurred while deleting a task list: {e}")


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
        self.priority_filter = False
        self.task_manager = parent.task_manager
        self.set_allowed_areas()
        self.setup_ui()

    def set_allowed_areas(self):
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                         QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                         QDockWidget.DockWidgetFeature.DockWidgetClosable)

    def setup_ui(self):
        self.right_widget = QWidget()
        self.setWidget(self.right_widget)
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)
        self.setup_toolbar()
        self.setup_stack_widget()

    def setup_toolbar(self):
        self.right_toolbar = TaskListToolbar(self)
        self.right_layout.addWidget(self.right_toolbar)

    def setup_stack_widget(self):
        self.stack_widget = QStackedWidget()
        self.right_layout.addWidget(self.stack_widget)
        QApplication.instance().focusChanged.connect(self.on_focus_changed)

    def on_focus_changed(self, old, new):
        if self.isAncestorOf(new):
            print("Dock widget is in focus")
        else:
            print("Dock widget is not in focus")

    def add_task(self):
        current_task_list_widget = self.get_current_task_list_widget()
        print(current_task_list_widget)
        # if not current_task_list_widget:
        #     return
        self.show_add_task_dialog(current_task_list_widget)

    def show_add_task_dialog(self, task_list_widget):
        try:
            dialog = AddTaskDialog(self)
            button_pos = self.right_toolbar.mapToGlobal(self.right_toolbar.rect().bottomRight())
            dialog.adjustSize()
            dialog.move(button_pos.x() - dialog.width(), button_pos.y())

            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.get_task_data()
                task = Task(
                    title=task_data["title"],
                    description=task_data["description"],
                    due_date=task_data["due_date"],
                    due_time=task_data["due_time"],
                    is_important=task_data["is_important"]
                )
                task_list_widget.task_list.add_task(task)
                task_list_widget.load_tasks()
        except Exception as e:
            print(f"An error occurred while adding a task: {e}")

    def set_queue(self):
        try:
            current_task_list_widget = self.stack_widget.currentWidget()
            if not isinstance(current_task_list_widget, TaskListWidget):
                return

            current_task_list = current_task_list_widget.task_list
            current_task_list.queue = not current_task_list.queue
            if current_task_list.queue:
                self.right_toolbar.actions()[1].setCheckable(True)
                self.right_toolbar.actions()[1].setChecked(current_task_list.queue)
                current_task_list.stack = False
                self.right_toolbar.actions()[2].setCheckable(False)
                self.right_toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
            else:
                self.right_toolbar.actions()[1].setCheckable(False)
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
            if current_task_list.stack:
                self.right_toolbar.actions()[2].setCheckable(True)
                self.right_toolbar.actions()[2].setChecked(current_task_list.stack)
                self.right_toolbar.actions()[1].setCheckable(False)
                self.right_toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
                current_task_list.queue = False

            else:
                self.right_toolbar.actions()[2].setCheckable(False)
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

            if self.priority_filter:
                self.right_toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
                current_task_list_widget.load_tasks(False)
                return
            else:
                self.right_toolbar.actions()[3].setCheckable(True)
                self.right_toolbar.actions()[3].setChecked(True)
                self.right_toolbar.actions()[2].setCheckable(False)
                self.right_toolbar.actions()[1].setCheckable(False)
                current_task_list.queue = False
                current_task_list.stack = False
                self.priority_filter = True
            current_task_list_widget.load_tasks(True)
            self.task_manager.update_task_list(current_task_list)
        except Exception as e:
            print(f"Error in priority_sort: {e}")

    def get_current_task_list_widget(self):
        current_widget = self.stack_widget.currentWidget()
        return current_widget if isinstance(current_widget, TaskListWidget) else None
