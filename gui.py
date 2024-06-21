import sys
import os
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from task_manager import *


class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.date() == QDate(2000, 1, 1):
            self.setDate(QDate.currentDate())


class AddTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        self.layout = QFormLayout(self)

        self.title_edit = QLineEdit(self)
        self.layout.addRow("Title:", self.title_edit)

        self.description_edit = QLineEdit(self)
        self.layout.addRow("Description:", self.description_edit)

        self.due_date_edit = CustomDateEdit(self)  # Use the subclassed QDateEdit
        self.layout.addRow("Due Date:", self.due_date_edit)

        self.due_time_edit = QTimeEdit(self)
        self.layout.addRow("Due Time:", self.due_time_edit)

        self.important_checkbox = QCheckBox("Important", self)
        self.layout.addRow(self.important_checkbox)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

        # Set focus on the title edit when the dialog opens
        self.title_edit.setFocus()

    def get_task_data(self):
        return {
            "title": self.title_edit.text(),
            "description": self.description_edit.text(),
            "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
            "due_time": self.due_time_edit.time().toString("HH:mm"),
            "is_important": self.important_checkbox.isChecked()
        }


class EditTaskDialog(QDialog):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        self.layout = QFormLayout(self)

        self.title_edit = QLineEdit(self)
        self.title_edit.setText(task.title)
        self.layout.addRow("Title:", self.title_edit)

        self.description_edit = QLineEdit(self)
        self.description_edit.setText(task.description)
        self.layout.addRow("Description:", self.description_edit)

        self.due_date_edit = CustomDateEdit(self)
        if task.due_date:
            self.due_date_edit.setDate(QDate.fromString(task.due_date, "yyyy-MM-dd"))
        else:
            self.due_date_edit.setDate(QDate(2000, 1, 1))
        self.layout.addRow("Due Date:", self.due_date_edit)

        self.due_time_edit = QTimeEdit(self)
        if task.due_time:
            self.due_time_edit.setTime(QTime.fromString(task.due_time, "HH:mm"))
        else:
            self.due_time_edit.setTime(QTime(0, 0))
        self.layout.addRow("Due Time:", self.due_time_edit)

        self.priority_spinbox = QSpinBox(self)
        self.priority_spinbox.setMinimum(0)
        self.priority_spinbox.setMaximum(10)
        self.priority_spinbox.setValue(task.priority)
        self.layout.addRow("Priority:", self.priority_spinbox)

        self.important_checkbox = QCheckBox("Important", self)
        self.important_checkbox.setChecked(task.is_important)
        self.layout.addRow(self.important_checkbox)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_task_data(self):
        return {
            "title": self.title_edit.text(),
            "description": self.description_edit.text(),
            "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
            "due_time": self.due_time_edit.time().toString("HH:mm"),
            "priority": self.priority_spinbox.value(),
            "is_important": self.important_checkbox.isChecked()
        }


class TaskWidget(QWidget):
    def __init__(self, task_list_widget, task):
        super().__init__()
        self.task_list_widget = task_list_widget
        self.task = task

        self.layout = QHBoxLayout()
        self.checkbox = QCheckBox(task.title)
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.stateChanged.connect(self.task_checked)
        self.layout.addWidget(self.checkbox)

        self.layout.addStretch()

        self.radio_button = QRadioButton()
        self.radio_button.setChecked(self.task.is_important)
        self.radio_button.toggled.connect(self.mark_important)
        self.layout.addWidget(self.radio_button)

        self.setLayout(self.layout)

    def mousePressEvent(self, event):
        print("mousePressEvent TaskWidget")
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                dialog = EditTaskDialog(self.task, self)
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
            print(f"Error in mousePressEvent TaskWidget: {e}")

    def task_checked(self, state):
        self.task.completed = bool(state)
        self.task_list_widget.task_list.update_task(self.task)
        self.task_list_widget.load_tasks()

    def mark_important(self):
        if self.radio_button.isChecked():
            self.task.mark_as_important()
        else:
            self.task.unmark_as_important()
        self.task_list_widget.task_list.update_task(self.task)
        self.task_list_widget.load_tasks()


class TaskListWidget(QListWidget):
    def __init__(self, task_list_name, pin, queue, stack):
        super().__init__()
        self.task_list_name = task_list_name
        self.task_list = TaskList(self.task_list_name, pin, queue, stack)
        self.load_tasks()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def load_tasks(self):
        self.clear()
        for task in self.task_list.get_tasks():
            item = QListWidgetItem(self)
            task_widget = TaskWidget(self, task)
            item.setSizeHint(task_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, task_widget)

    def delete_task(self, task):
        try:
            self.task_list.remove_task(task)
            for index in range(self.count()):
                item = self.item(index)
                task_widget = item.data(Qt.ItemDataRole.UserRole)
                if task_widget.task == task:
                    self.takeItem(index)
                    break
        except Exception as e:
            print(e)

    def startDrag(self, supportedActions):
        try:
            print("startDrag")
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
            print("dragEnterEvent")
            if event.source() == self:
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            print(f"Error in dragEnterEvent: {e}")

    def dragMoveEvent(self, event):
        try:
            print("dragMoveEvent")
            if event.source() == self:
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            print(f"Error in dragMoveEvent: {e}")

    def dropEvent(self, event):
        try:
            print("dropEvent")
            if event.source() == self:
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                super().dropEvent(event)
                self.reorder_tasks()
            else:
                event.ignore()
        except Exception as e:
            print(f"Error in dropEvent: {e}")

    def reorder_tasks(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.task_manager = TaskListManager()

        font_id = QFontDatabase.addApplicationFont("fonts/entsans.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        # font = QFont(font_family)
        font = QFont()
        font.setPointSize(12)
        app.setFont(font)

        self.setWindowTitle('ADM')
        screen_geometry = QApplication.primaryScreen().geometry()
        center_point = screen_geometry.center()
        window_width, window_height = 800, 600
        self.resize(window_width, window_height)
        top_left_point = center_point - QPoint(window_width // 2, window_height // 2)
        self.move(top_left_point)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # left layout containing widgets related to handling tabs of task lists.
        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout, stretch=1)

        # widget for collection of task lists
        self.task_list_collection = QListWidget()
        self.task_list_collection.setDragEnabled(True)
        self.task_list_collection.setAcceptDrops(True)
        self.task_list_collection.setDropIndicatorShown(True)
        self.task_list_collection.setDragDropMode(QListWidget.DragDropMode.InternalMove)

        # Mapping of hash values to stack widget pages
        self.hash_to_widget = {}
        self.task_list_collection.currentItemChanged.connect(self.switch_stack_widget_by_hash)

        self.left_layout.addWidget(self.task_list_collection)
        self.task_list_collection.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list_collection.customContextMenuRequested.connect(self.task_list_collection_context_menu)

        # right layout containing widgets related to handling tasks
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_layout, stretch=4)

        # right toolbar
        self.right_toolbar = QToolBar()
        self.right_layout.addWidget(self.right_toolbar)

        add_task_action = QAction("+", self)
        add_task_action.triggered.connect(self.add_task)
        self.right_toolbar.addAction(add_task_action)

        queue_action = QAction("Q", self)
        queue_action.triggered.connect(self.set_queue)
        self.right_toolbar.addAction(queue_action)

        stack_action = QAction("S", self)
        stack_action.triggered.connect(self.set_stack)
        self.right_toolbar.addAction(stack_action)

        self.right_toolbar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Stack to switch between different task list tabs
        self.stack_widget = QStackedWidget()
        self.right_layout.addWidget(self.stack_widget)

        # Button to create a new task list
        add_task_list_button = QPushButton('Add Task List')
        self.left_layout.addWidget(add_task_list_button, alignment=Qt.AlignmentFlag.AlignBottom)
        add_task_list_button.clicked.connect(self.add_task_list)

        self.load_task_lists()

    def load_task_lists(self):
        for task_list_info in self.task_manager.get_task_lists():
            self.add_task_list(
                task_list_info["list_name"],
                pin=task_list_info["pin"],
                queue=task_list_info["queue"],
                stack=task_list_info["stack"]
            )

    def add_task_list(self, task_list_name="", pin=False, queue=False, stack=False):
        try:
            if not task_list_name:  # Check if task_list_name is empty or None
                task_list_name, ok = QInputDialog.getText(self, "New Task List", "Enter name:")
                if not ok or not task_list_name.strip():
                    return

            task_list_name = str(task_list_name).strip()

            # Check for duplicate task list names
            if any(self.task_list_collection.item(i).text() == task_list_name for i in
                   range(self.task_list_collection.count())):
                QMessageBox.warning(self, "Duplicate Name", "A task list with this name already exists.")
                return

            self.task_list_collection.addItem(task_list_name)
            self.task_manager.add_task_list(task_list_name, pin=pin, queue=queue, stack=stack)
            task_list_widget = TaskListWidget(task_list_name, pin=pin, queue=queue, stack=stack)
            self.stack_widget.addWidget(task_list_widget)
            self.hash_to_widget[hash(task_list_name)] = task_list_widget
            self.stack_widget.setCurrentWidget(task_list_widget)  # Ensure the new list is selected
            self.task_list_collection.setCurrentItem(
                self.task_list_collection.findItems(task_list_name, Qt.MatchFlag.MatchExactly)[0])

        except Exception as e:
            print(f"An error occurred while adding a task list: {e}")

    # responsible for showing tasklist of the widget item selected from the left layout
    def switch_stack_widget_by_hash(self, current, previous):
        try:
            if current:
                hash_key = hash(current.text())
                print(f"switching to {current.text()}")
                if hash_key in self.hash_to_widget:
                    self.stack_widget.setCurrentWidget(self.hash_to_widget[hash_key])
                    print(f"switched to {self.stack_widget.currentWidget().task_list_name}")
        except Exception as e:
            print(f"An error occurred while switching stack: {e}")

    def add_task(self):
        current_task_list_widget = self.stack_widget.currentWidget()
        if not isinstance(current_task_list_widget, TaskListWidget):
            return

        try:
            dialog = AddTaskDialog(self)

            button_pos = self.right_toolbar.mapToGlobal(self.right_toolbar.rect().bottomRight())
            dialog.adjustSize()  # ensures the dialog's size is calculated correctly; like idk tf
            dialog_x = button_pos.x() - dialog.width()
            dialog_y = button_pos.y()
            dialog.move(dialog_x, dialog_y)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.get_task_data()
                task = Task(
                    title=task_data["title"],
                    description=task_data["description"],
                    due_date=task_data["due_date"],
                    due_time=task_data["due_time"]
                )
                task.is_important = task_data["is_important"]
                current_task_list_widget.task_list.add_task(task)
                current_task_list_widget.load_tasks()
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
                current_task_list.stack = False
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
                current_task_list.queue = False
            current_task_list_widget.load_tasks()
            self.task_manager.update_task_list(current_task_list)
        except Exception as e:
            print(f"Error in set_stack: {e}")

    def task_list_collection_context_menu(self, position):
        try:
            task_list = self.task_list_collection.itemAt(position)
            if not task_list:
                return

            # Create the context menu
            menu = QMenu()
            edit_action = QAction('Edit', self)
            delete_action = QAction('Delete', self)

            # Connect actions to methods
            edit_action.triggered.connect(lambda: self.edit_task_list(task_list))
            delete_action.triggered.connect(lambda: self.delete_task_list(task_list))

            # Add actions to the menu
            menu.addAction(edit_action)
            menu.addAction(delete_action)

            # Show the context menu at the current mouse position
            menu.exec(self.task_list_collection.viewport().mapToGlobal(position))
        except Exception as e:
            print(f"An error occurred in task_list_collection_context_menu: {e}")

    def edit_task_list(self, task_list):
        print(f"Editing item: {task_list.text()}")

    def delete_task_list(self, task_list):
        try:
            row = self.task_list_collection.row(task_list)
            hash_key = hash(task_list.text())
            # Remove the corresponding widget from the stack
            if hash_key in self.hash_to_widget:
                widget_to_remove = self.hash_to_widget.pop(hash_key)
                self.stack_widget.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()
            self.task_list_collection.takeItem(row)
            # Remove from database
            self.task_manager.remove_task_list(task_list.text())
        except Exception as e:
            print(f"An error occurred while deleting a task list: {e}")
