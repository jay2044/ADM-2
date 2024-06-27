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
    def __init__(self, task, task_list_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        self.task = task
        self.task_list_widget = task_list_widget

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

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.important_checkbox)

        # Delete button
        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.delete_task_button_action)
        hbox_layout.addStretch(1)
        hbox_layout.addWidget(self.delete_button)

        self.layout.addRow(hbox_layout)

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

    def delete_task_button_action(self):
        self.task_list_widget.delete_task(self.task)
        self.accept()


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
                dialog = EditTaskDialog(self.task, self.task_list_widget, self)
                dialog.adjustSize()

                # Get the dimensions of the task list widget
                task_list_widget_geometry = self.task_list_widget.geometry()
                task_list_widget_width = task_list_widget_geometry.width()
                task_list_widget_height = task_list_widget_geometry.height()

                # Calculate the size and position for the dialog
                dialog_width = int(task_list_widget_width * 0.8)
                dialog_height = task_list_widget_height
                dialog_x = self.task_list_widget.mapToGlobal(QPoint(task_list_widget_width - dialog_width, 0)).x()
                dialog_y = self.task_list_widget.mapToGlobal(QPoint(0, 0)).y()

                # Resize and move the dialog
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
            print(f"Error in mousePressEvent TaskWidget: {e}")

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
    def __init__(self, task_list_name, pin, queue, stack):
        super().__init__()
        self.task_list_name = task_list_name
        self.task_list = TaskList(self.task_list_name, pin, queue, stack)
        self.load_tasks()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def load_tasks(self, priority_filter=False):
        self.clear()
        if priority_filter:
            tasks = self.task_list.get_tasks_filter_priority()
        else:
            tasks = self.task_list.get_tasks()
        for task in tasks:
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
        font = QFont()
        font.setPointSize(12)
        app.setFont(font)

        self.setWindowTitle('ADM')
        screen_geometry = QApplication.primaryScreen().geometry()
        center_point = screen_geometry.center()
        window_width, window_height = 700, 600
        self.resize(window_width, window_height)
        top_left_point = center_point - QPoint(window_width // 2, window_height // 2)
        self.move(top_left_point)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Use QSplitter to divide left and right layouts
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # left layout containing widgets related to handling tabs of task lists
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)
        self.splitter.addWidget(self.left_widget)

        # left top toolbar
        self.left_top_toolbar = QToolBar()
        self.left_layout.addWidget(self.left_top_toolbar)

        add_task_list_action = QAction("+", self)
        add_task_list_action.triggered.connect(self.add_task_list)
        self.left_top_toolbar.addAction(add_task_list_action)

        history_action = QAction("H", self)
        history_action.triggered.connect(self.show_history)
        self.left_top_toolbar.addAction(history_action)

        calender_action = QAction("C", self)
        # calender_action.triggered.connect(self.)
        self.left_top_toolbar.addAction(calender_action)

        # widget for collection of task lists
        self.task_list_collection = QListWidget()
        self.task_list_collection.setDragEnabled(True)
        self.task_list_collection.setAcceptDrops(True)
        self.task_list_collection.setDropIndicatorShown(True)
        self.task_list_collection.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.hash_to_widget = {}
        self.task_list_collection.currentItemChanged.connect(self.switch_stack_widget_by_hash)
        self.left_layout.addWidget(self.task_list_collection)
        self.task_list_collection.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list_collection.customContextMenuRequested.connect(self.task_list_collection_context_menu)

        # right layout containing widgets related to handling tasks
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)
        self.splitter.addWidget(self.right_widget)

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

        priority_action = QAction("P", self)
        self.priority_filter = False
        priority_action.triggered.connect(self.priority_sort)
        self.right_toolbar.addAction(priority_action)

        self.right_toolbar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Stack to switch between different task list tabs
        self.stack_widget = QStackedWidget()
        self.right_layout.addWidget(self.stack_widget)

        self.load_task_lists()

        # Restore splitter state
        self.restore_splitter_state()

        self.hidden_widgets = []  # To keep track of hidden widgets

        # Initialize history widget
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.right_layout.addWidget(self.history_widget)
        self.history_widget.hide()

        self.task_list_collection.currentItemChanged.connect(self.exit_history_mode)

        # Add new widgets for history view
        history_label = QLabel("History", self)
        history_list = QListWidget(self)

        # Populate the history list with competed task from all the task lists
        # for i in range(10):
        #     self.task_manager.get_task_lists()

        self.history_layout.addWidget(history_label)
        self.history_layout.addWidget(history_list)

    def closeEvent(self, event):
        self.save_splitter_state()
        super().closeEvent(event)

    def save_splitter_state(self):
        settings = QSettings("current_user", "ADM")
        settings.setValue("splitterSizes", self.splitter.sizes())

    def restore_splitter_state(self):
        settings = QSettings("current_user", "ADM")
        sizes = settings.value("splitterSizes")
        if sizes:
            self.splitter.setSizes([int(size) for size in sizes])
        else:
            self.splitter.setSizes([200, 500])

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

    def show_history(self):
        self.history_widget.show()

        # Hide the current widgets in the right_layout and save them to hidden_widgets
        self.hidden_widgets.clear()
        for i in range(self.right_layout.count()):
            widget = self.right_layout.itemAt(i).widget()
            if widget is not None and widget != self.history_widget:
                self.hidden_widgets.append(widget)
                widget.hide()

    def exit_history_mode(self, current, previous):
        if not previous:
            return

        self.history_widget.hide()

        # Unhide the previously hidden widgets
        for widget in self.hidden_widgets:
            widget.show()

        # Clear the list of hidden widgets
        self.hidden_widgets.clear()
