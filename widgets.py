from PIL.ImageChops import offset
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from datetime import datetime
from task_manager import *
from control import *
from gui import global_signals


class TaskWidget(QWidget):
    def __init__(self, task_list_widget, task):
        super().__init__()
        self.task_list_widget = task_list_widget
        self.task = task
        self.is_dragging = False

        self.setup_ui()
        self.setup_timer()

        self.checkbox.setObjectName("taskCheckbox")
        self.radio_button.setObjectName("importantRadioButton")

    def setup_ui(self):
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.checkbox = QCheckBox(self.task.title)
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.stateChanged.connect(self.task_checked)
        self.layout.addWidget(self.checkbox)

        self.layout.addStretch()

        # Show due date and time label if they are not default.
        if self.task.due_date != "2000-01-01" or self.task.due_time != "00:00":
            due_label_text = ""
            if self.task.due_date != "2000-01-01":
                try:
                    due_date_obj = datetime.strptime(self.task.due_date, "%Y-%m-%d")
                    due_label_text = due_date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    due_label_text = self.task.due_date  # If parsing fails, use the raw string

            if self.task.due_time != "00:00":
                try:
                    due_time_obj = datetime.strptime(self.task.due_time, "%H:%M")
                    due_label_text += f" {due_time_obj.strftime('%H:%M')}"
                except ValueError:
                    due_label_text += f" {self.task.due_time}"  # If parsing fails, use the raw string

            self.due_label = QLabel(due_label_text)
            self.layout.addWidget(self.due_label)

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
            # Set parent to None to avoid dependency on main_window
            dialog = TaskDetailDialog(self.task, self.task_list_widget, self)
            global_signals.task_list_updated.emit()

            # Position the dialog to appear over the dock containing the task
            dock_widget = self.task_list_widget
            if dock_widget:
                dock_pos = dock_widget.mapToGlobal(QPoint(0, 0))
                dock_size = dock_widget.size()

                # Adjust to make it slightly narrower and aligned to the right of the dock
                offset = int(0.2 * dock_size.width())
                dialog_width = dock_size.width() - offset
                dialog_height = dock_size.height()
                dialog_x = dock_pos.x() + offset
                dialog_y = dock_pos.y()

                dialog.resize(dialog_width, dialog_height)
                dialog.move(dialog_x, dialog_y)

                # Set fixed size to prevent resizing
                dialog.setFixedSize(dialog_width, dialog_height)
            else:
                # Default positioning if dock widget not found
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

            # Update the history dock in the parent window
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
        self.setup_ui()
        self.load_tasks()

        global_signals.task_list_updated.connect(self.load_tasks)

    def setup_ui(self):
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def load_tasks(self, priority_filter=False):
        try:
            # Refresh the tasks from the database
            self.task_list.tasks = self.task_list.load_tasks()
            self.clear()
            tasks = self.task_list.get_tasks_filter_priority() if priority_filter else self.task_list.get_tasks()
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
        self.add_action("+C", parent, parent.task_list_collection.add_category)
        self.add_action("T", parent, parent.toggle_stacked_task_list)
        self.add_action("H", parent, parent.toggle_history)
        self.add_action("C", parent, parent.toggle_calendar)

        self.setObjectName("taskListManagerToolbar")

    def add_action(self, text, parent, function):
        action = QAction(text, parent)
        action.triggered.connect(function)
        self.addAction(action)


class TaskListCollection(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.task_manager = self.parent.task_manager

        self.setup_ui()
        self.load_task_lists()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search task lists...")
        self.search_bar.textChanged.connect(self.filter_task_lists)
        self.layout.addWidget(self.search_bar)

        # Use QTreeWidget instead of QListWidget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.task_list_collection_context_menu)
        self.tree_widget.itemClicked.connect(self.switch_stack_widget_by_item)
        self.tree_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree_widget.expandAll()
        self.layout.addWidget(self.tree_widget)

    def load_task_lists(self):
        try:
            self.tree_widget.clear()
            self.categories = self.task_manager.get_categories()

            # Sort categories based on 'pin' attribute and alphabetically
            sorted_categories = sorted(
                self.categories.items(),
                key=lambda x: (not x[1]['pin'], x[0].lower())
            )

            for category_name, category_info in sorted_categories:
                # Create QTreeWidgetItem for the category
                category_item = QTreeWidgetItem(self.tree_widget)
                category_item.setText(0, category_name)
                category_item.setExpanded(True)
                category_item.setFlags(category_item.flags())
                category_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'category', 'name': category_name})

                # Sort task lists based on 'pin' attribute and alphabetically
                sorted_task_lists = sorted(
                    category_info['task_lists'],
                    key=lambda x: (not x['pin'], x['list_name'].lower())
                )

                for task_list_info in sorted_task_lists:
                    task_list_name = task_list_info["list_name"]

                    # Create QTreeWidgetItem for the task list
                    task_list_item = QTreeWidgetItem(category_item)
                    task_list_item.setText(0, task_list_name)
                    task_list_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'task_list', 'info': task_list_info})
                    task_list_item.setFlags(task_list_item.flags())

                    # Retrieve or create TaskList instance
                    if task_list_name in self.parent.task_lists:
                        task_list = self.parent.task_lists[task_list_name]
                    else:
                        task_list = TaskList(
                            task_list_name,
                            self.task_manager,
                            task_list_info["pin"],
                            task_list_info["queue"],
                            task_list_info["stack"]
                        )
                        self.parent.task_lists[task_list_name] = task_list

                    # Add TaskListWidget to the stack widget if not already added
                    hash_key = hash(task_list_name)
                    if hash_key not in self.parent.hash_to_widget:
                        task_list_widget = TaskListWidget(task_list, self.parent)
                        self.parent.stacked_task_list.stack_widget.addWidget(task_list_widget)
                        self.parent.hash_to_widget[hash_key] = task_list_widget

            self.tree_widget.expandAll()
            self.filter_task_lists()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Task Lists", f"An error occurred: {e}")
            print(f"Error loading task lists: {e}")

    def filter_task_lists(self):
        search_text = self.search_bar.text().lower()
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.parent():
                # This is a task list item
                task_list_name = item.text(0).lower()
                item.setHidden(search_text not in task_list_name)
            else:
                # This is a category item
                child_count = sum(not item.child(i).isHidden() for i in range(item.childCount()))
                item.setHidden(child_count == 0)
            iterator += 1

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
                self.task_manager.add_task_list(task_list_name, pin=False, queue=False, stack=False,
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

    def task_list_collection_context_menu(self, position):
        try:
            item = self.tree_widget.itemAt(position)
            if not item:
                return

            menu = QMenu()

            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data is None:
                QMessageBox.warning(self, "Error", "No data associated with this item.")
                return

            item_type = data.get('type')

            if item_type == 'task_list':
                # Task list item
                task_list_info = data['info']
                task_list_name = task_list_info["list_name"]

                rename_action = QAction('Rename Task List', self)
                pin_action = QAction('Pin' if not task_list_info["pin"] else 'Unpin', self)
                duplicate_action = QAction('Duplicate Task List', self)
                delete_action = QAction('Delete Task List', self)
                move_action = QAction('Move to Category', self)

                rename_action.triggered.connect(lambda: self.rename_task_list(item))
                pin_action.triggered.connect(lambda: self.pin_task_list(item))
                duplicate_action.triggered.connect(lambda: self.duplicate_task_list(item))
                delete_action.triggered.connect(lambda: self.delete_task_list(item))
                move_action.triggered.connect(lambda: self.move_task_list(item))

                menu.addAction(rename_action)
                menu.addAction(pin_action)
                menu.addAction(duplicate_action)
                menu.addAction(move_action)
                menu.addAction(delete_action)

            elif item_type == 'category':
                # Category item
                category_name = data['name']
                category_info = self.categories[category_name]

                rename_action = QAction('Rename Category', self)
                pin_action = QAction('Pin' if not category_info["pin"] else 'Unpin', self)
                delete_action = QAction('Delete Category', self)

                rename_action.triggered.connect(lambda: self.rename_category(item))
                pin_action.triggered.connect(lambda: self.pin_category(item))
                delete_action.triggered.connect(lambda: self.delete_category(item))

                menu.addAction(rename_action)
                menu.addAction(pin_action)
                menu.addAction(delete_action)
            else:
                QMessageBox.warning(self, "Error", "Unknown item type.")

            menu.exec(self.tree_widget.viewport().mapToGlobal(position))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred in context menu: {e}")
            print(f"Error in task_list_collection_context_menu: {e}")

    def pin_category(self, item):
        try:
            category_name = item.text(0)
            category_info = self.categories[category_name]
            category_info['pin'] = not category_info['pin']
            self.task_manager.pin_category(category_name)
            self.load_task_lists()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while pinning the category: {e}")
            print(f"Error in pin_category: {e}")

    def move_task_list(self, item):
        task_list_name = item.text(0)
        current_category_name = item.parent().text(0)
        category_names = [name for name in self.categories.keys() if name != current_category_name]
        category_names.append("Uncategorized")
        new_category_name, ok = QInputDialog.getItem(self, "Move Task List", "Select new category:", category_names,
                                                     editable=False)
        if ok:
            # Update in task manager
            self.task_manager.move_task_list_to_category(task_list_name,
                                                         new_category_name if new_category_name != "Uncategorized" else None)
            # Update in categories
            task_list_info = next(
                (tl for tl in self.categories[current_category_name] if tl["list_name"] == task_list_name), None)
            if task_list_info:
                self.categories[current_category_name].remove(task_list_info)
                if not self.categories[current_category_name]:
                    del self.categories[current_category_name]
                task_list_info["category"] = new_category_name if new_category_name != "Uncategorized" else None
                self.categories.setdefault(new_category_name, []).append(task_list_info)
            # Update UI
            self.load_task_lists()
            self.select_task_list_in_tree(task_list_name)

    def move_task_list_to_category(self, list_name, category_name):
        cursor = self.conn.cursor()
        category_id = None
        if category_name:
            cursor.execute("SELECT id FROM categories WHERE name=?", (category_name,))
            result = cursor.fetchone()
            if result:
                category_id = result["id"]
        cursor.execute("UPDATE task_lists SET category_id=? WHERE list_name=?", (category_id, list_name))
        self.conn.commit()
        # Update in-memory data
        for task_list in self.task_lists:
            if task_list["list_name"] == list_name:
                task_list["category"] = category_name
                break
        # Update categories dictionary
        self.categories = self.load_categories()

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

    def pin_task_list(self, item):
        try:
            task_list_info = item.data(0, Qt.ItemDataRole.UserRole)['info']
            task_list_info["pin"] = not task_list_info["pin"]
            self.task_manager.pin_task_list(task_list_info["list_name"])
            self.load_task_lists()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while pinning the task list: {e}")
            print(f"Error in pin_task_list: {e}")

    def duplicate_task_list(self, item):
        task_list_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, "Duplicate Task List", "Enter new name:")
        if ok and new_name.strip():
            new_name = new_name.strip()
            if any(new_name == task_list["list_name"] for task_lists in self.categories.values() for task_list in
                   task_lists['task_lists']):
                QMessageBox.warning(self, "Duplicate Task List", "A task list with this name already exists.")
                return
            # Duplicate the task list
            category_name = item.parent().text(0)
            self.task_manager.add_task_list(new_name, pin=False, queue=False, stack=False, category=category_name)
            # Copy tasks
            original_task_list = TaskList(task_list_name, self.task_manager)
            for task in original_task_list.tasks:
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
                self.task_manager.add_task(new_task, new_name)
            # Add to categories
            self.categories[category_name]['task_lists'].append(
                {"list_name": new_name, "pin": False, "queue": False, "stack": False})
            self.load_task_lists()
            # Add to the stack widget
            task_list_widget = TaskListWidget(self.parent.task_lists[task_list_name], self.parent)
            self.parent.stacked_task_list.stack_widget.addWidget(task_list_widget)
            self.parent.hash_to_widget[hash(new_name)] = task_list_widget
            self.parent.stacked_task_list.stack_widget.setCurrentWidget(task_list_widget)
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
        self.setup_stack_widget()

    def setup_toolbar(self):
        self.toolbar = TaskListToolbar(self)
        self.layout.addWidget(self.toolbar)

    def setup_stack_widget(self):
        self.stack_widget = QStackedWidget()
        self.layout.addWidget(self.stack_widget)
        # QApplication.instance().focusChanged.connect(self.on_focus_changed)

    # def on_focus_changed(self, old, new):
    #     if self.isAncestorOf(new):
    #         print("Dock widget is in focus")
    #     else:
    #         print("Dock widget is not in focus")

    def add_task(self):
        current_task_list_widget = self.get_current_task_list_widget()
        # print(current_task_list_widget)
        # if not current_task_list_widget:
        #     return
        self.show_add_task_dialog(current_task_list_widget)

    def show_add_task_dialog(self, task_list_widget):
        try:
            dialog = AddTaskDialog(self)
            button_pos = self.toolbar.mapToGlobal(self.toolbar.rect().bottomRight())
            dialog.adjustSize()
            dialog.move(button_pos.x() - dialog.width(), button_pos.y())

            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_data = dialog.get_task_data()
                task = Task(
                    title=task_data["title"],
                    description=task_data["description"],
                    due_date=task_data["due_date"],
                    due_time=task_data["due_time"],
                    is_important=task_data["is_important"],
                    priority=task_data["priority"],
                    categories=task_data["categories"],
                    recurring=task_data["recurring"],
                    recur_every=task_data["recur_every"],
                    status=task_data["status"],
                    estimate=task_data["estimate"],
                    count_required=task_data["count_required"],
                    count_completed=task_data["count_completed"],
                    dependencies=task_data["dependencies"],
                    deadline_flexibility=task_data["deadline_flexibility"],
                    effort_level=task_data["effort_level"],
                    resources=task_data["resources"],
                    notes=task_data["notes"],
                    time_logged=task_data["time_logged"]
                )
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
            if current_task_list.queue:
                self.toolbar.actions()[1].setCheckable(True)
                self.toolbar.actions()[1].setChecked(current_task_list.queue)
                current_task_list.stack = False
                self.toolbar.actions()[2].setCheckable(False)
                self.toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
            else:
                self.toolbar.actions()[1].setCheckable(False)
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
                self.toolbar.actions()[2].setCheckable(True)
                self.toolbar.actions()[2].setChecked(current_task_list.stack)
                self.toolbar.actions()[1].setCheckable(False)
                self.toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
                current_task_list.queue = False

            else:
                self.toolbar.actions()[2].setCheckable(False)
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
                self.toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
                current_task_list_widget.load_tasks(False)
                return
            else:
                self.toolbar.actions()[3].setCheckable(True)
                self.toolbar.actions()[3].setChecked(True)
                self.toolbar.actions()[2].setCheckable(False)
                self.toolbar.actions()[1].setCheckable(False)
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


class TaskListDock(QDockWidget):
    def __init__(self, task_list_name, parent=None):
        super().__init__(task_list_name, parent)
        self.type = "dock"
        self.parent = parent
        self.task_manager = self.parent.task_manager
        self.task_list_name = task_list_name
        self.setWindowTitle(task_list_name)

        # Retrieve the shared TaskList instance
        if task_list_name in self.parent.task_lists:
            task_list = self.parent.task_lists[task_list_name]
        else:
            # Should not happen, but handle it just in case
            task_list = TaskList(task_list_name, self.task_manager, False, False, False)
            self.parent.task_lists[task_list_name] = task_list

        # Use the shared TaskList instance to create TaskListWidget
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
                task = Task(
                    title=task_data["title"],
                    description=task_data["description"],
                    due_date=task_data["due_date"],
                    due_time=task_data["due_time"],
                    is_important=task_data["is_important"],
                    priority=task_data["priority"],
                    categories=task_data["categories"],
                    recurring=task_data["recurring"],
                    recur_every=task_data["recur_every"],
                    status=task_data["status"],
                    estimate=task_data["estimate"],
                    count_required=task_data["count_required"],
                    count_completed=task_data["count_completed"],
                    dependencies=task_data["dependencies"],
                    deadline_flexibility=task_data["deadline_flexibility"],
                    effort_level=task_data["effort_level"],
                    resources=task_data["resources"],
                    notes=task_data["notes"],
                    time_logged=task_data["time_logged"]
                )
                task_list_widget.task_list.add_task(task)
                global_signals.task_list_updated.emit()
        except Exception as e:
            print(f"An error occurred while adding a task: {e}")

    def set_queue(self):
        try:
            task_list = self.task_list_widget.task_list
            task_list.queue = not task_list.queue
            if task_list.queue:
                self.toolbar.actions()[1].setCheckable(True)
                self.toolbar.actions()[1].setChecked(task_list.queue)
                task_list.stack = False
                self.toolbar.actions()[2].setCheckable(False)
                self.toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
            else:
                self.toolbar.actions()[1].setCheckable(False)
            self.task_list_widget.load_tasks()
            self.task_manager.update_task_list(task_list)
        except Exception as e:
            print(f"Error in set_queue: {e}")

    def set_stack(self):
        try:
            task_list = self.task_list_widget.task_list
            task_list.stack = not task_list.stack
            if task_list.stack:
                self.toolbar.actions()[2].setCheckable(True)
                self.toolbar.actions()[2].setChecked(task_list.stack)
                self.toolbar.actions()[1].setCheckable(False)
                self.toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
                task_list.queue = False

            else:
                self.toolbar.actions()[2].setCheckable(False)
            self.task_list_widget.load_tasks()
            self.task_manager.update_task_list(task_list)
        except Exception as e:
            print(f"Error in set_stack: {e}")

    def priority_sort(self):
        try:
            task_list = self.task_list_widget.task_list

            if self.priority_filter:
                self.toolbar.actions()[3].setCheckable(False)
                self.priority_filter = False
                self.task_list_widget.load_tasks(False)
                return
            else:
                self.toolbar.actions()[3].setCheckable(True)
                self.toolbar.actions()[3].setChecked(True)
                self.toolbar.actions()[2].setCheckable(False)
                self.toolbar.actions()[1].setCheckable(False)
                task_list.queue = False
                task_list.stack = False
                self.priority_filter = True
            self.task_list_widget.load_tasks(True)
            self.task_manager.update_task_list(task_list)
        except Exception as e:
            print(f"Error in priority_sort: {e}")


class HistoryDock(QDockWidget):
    def __init__(self, parent):
        super().__init__("History", parent)
        self.parent = parent

        self.set_allowed_areas()

        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search completed tasks...")
        self.search_bar.textChanged.connect(self.update_history)
        self.history_layout.addWidget(self.search_bar)

        # Use QTreeWidget instead of QListWidget
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Task", "Completed On", "Due Date", "Priority"])
        self.history_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_tree.itemDoubleClicked.connect(self.view_task_details)

        # Context menu
        self.history_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_tree.customContextMenuRequested.connect(self.show_context_menu)

        self.history_layout.addWidget(self.history_tree)
        self.setWidget(self.history_widget)

        self.setObjectName("historyDock")
        self.search_bar.setObjectName("historySearchBar")
        self.history_tree.setObjectName("historyTree")

        # Connect to the global signal
        global_signals.task_list_updated.connect(self.update_history)

        # Initial update
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
            # Refresh the task list
            task_list = TaskList(task_list_info["list_name"], self.parent.task_manager, task_list_info["pin"],
                                 task_list_info["queue"], task_list_info["stack"])
            task_list.refresh_tasks()  # Ensure tasks are up-to-date
            completed_tasks = task_list.get_completed_tasks()

            # Filter tasks based on search text
            if search_text:
                completed_tasks = [task for task in completed_tasks if search_text in task.title.lower() or
                                   search_text in task.description.lower()]

            if completed_tasks:
                # Create top-level item for the task list
                task_list_item = QTreeWidgetItem(self.history_tree)
                task_list_item.setText(0, task_list_info["list_name"])
                task_list_item.setFirstColumnSpanned(True)
                self.history_tree.addTopLevelItem(task_list_item)

                # Group tasks by completion date
                tasks_by_date = {}
                for task in completed_tasks:
                    completed_date = task.last_completed_date.strftime(
                        '%Y-%m-%d') if task.last_completed_date else 'Unknown'
                    if completed_date not in tasks_by_date:
                        tasks_by_date[completed_date] = []
                    tasks_by_date[completed_date].append(task)

                for date, tasks in sorted(tasks_by_date.items(), reverse=True):
                    # Create a child item for the completion date
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
                        task_item.setData(0, Qt.ItemDataRole.UserRole, task)  # Store task object for later use
                        date_item.addChild(task_item)

                task_list_item.setExpanded(True)

        self.history_tree.expandAll()

    def show_context_menu(self, position):
        item = self.history_tree.itemAt(position)
        if item and item.parent() and item.parent().parent():
            # This is a task item
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
            # Open the TaskDetailDialog
            self.open_task_detail(task)

    def open_task_detail(self, task):
        """
        Open the TaskDetailDialog for the selected task.
        """
        # Retrieve the shared TaskList instance
        if task.list_name in self.parent.task_lists:
            task_list = self.parent.task_lists[task.list_name]
        else:
            task_list = TaskList(task.list_name, self.parent.task_manager)
            self.parent.task_lists[task.list_name] = task_list

        # Use the shared TaskListWidget instance
        task_list_widget = self.parent.hash_to_widget.get(task.list_name)
        if not task_list_widget:
            task_list_widget = TaskListWidget(task_list, self.parent)
            self.parent.hash_to_widget[task.list_name] = task_list_widget

        # Create the TaskDetailDialog
        dialog = TaskDetailDialog(task, task_list_widget, parent=self)

        # Position the dialog to appear near the HistoryDock
        dock_widget = self
        if dock_widget:
            dock_pos = dock_widget.mapToGlobal(QPoint(0, 0))
            dock_size = dock_widget.size()

            # Adjust position and size to align with the dock
            offset = int(0.2 * dock_size.width())
            dialog_width = dock_size.width() - offset
            dialog_height = dock_size.height()
            dialog_x = dock_pos.x() + offset
            dialog_y = dock_pos.y()

            dialog.resize(dialog_width, dialog_height)
            dialog.move(dialog_x, dialog_y)

            # Set fixed size to prevent resizing
            dialog.setFixedSize(dialog_width, dialog_height)
        else:
            # Default positioning if dock widget not found
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
            # Emit global signal to update all views
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
        """Set the allowed areas where the dock widget can be placed."""
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

    def setup_ui(self):
        """Set up the UI components of the CalendarDock."""
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.layout = QVBoxLayout(self.widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Filter Layout
        self.setup_filters()
        self.layout.addLayout(self.filter_layout)

        # Calendar Widget
        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.on_date_clicked)
        self.layout.addWidget(self.calendar)

        # Task List Widget
        self.task_list_widget = QListWidget()
        self.task_list_widget.itemClicked.connect(self.on_task_clicked)
        self.layout.addWidget(self.task_list_widget)

        # Initial Highlight and Task Loading
        self.highlight_tasks_on_calendar()
        self.load_tasks_for_selected_date()

    def setup_filters(self):
        """Set up the filter widgets."""
        self.filter_layout = QHBoxLayout()

        # Priority Filter
        self.filter_label = QLabel("Priority:")
        self.filter_priority_combo = QComboBox()
        self.filter_priority_combo.addItem("All")
        self.filter_priority_combo.addItems([str(i) for i in range(1, 11)])  # Priorities 1 to 10
        self.filter_priority_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.filter_layout.addWidget(self.filter_label)
        self.filter_layout.addWidget(self.filter_priority_combo)

        # Status Filter
        self.status_filter_label = QLabel("Status:")
        self.filter_status_combo = QComboBox()
        self.filter_status_combo.addItem("All")
        self.filter_status_combo.addItem("Completed")
        self.filter_status_combo.addItem("Not Completed")
        self.filter_status_combo.currentIndexChanged.connect(self.on_filter_changed)
        self.filter_layout.addWidget(self.status_filter_label)
        self.filter_layout.addWidget(self.filter_status_combo)

        # Category Filter
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
        """Retrieve all unique categories from tasks."""
        categories = set()
        for task_list_info in self.task_manager.get_task_lists():
            task_list = TaskList(task_list_info["list_name"], self.task_manager, task_list_info["pin"],
                                 task_list_info["queue"], task_list_info["stack"])
            for task in task_list.tasks:
                categories.update(task.categories)
        return sorted(categories)

    def highlight_tasks_on_calendar(self):
        """Highlight dates on the calendar that have tasks."""
        tasks_by_date = self.get_tasks_grouped_by_date()

        # Clear existing formats
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())

        # Create a QTextCharFormat for highlighting
        highlight_format = QTextCharFormat()
        highlight_format.setFontWeight(QFont.Weight.Bold)

        # Highlight dates with tasks
        for date_str, tasks in tasks_by_date.items():
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            # Display number of tasks on the date
            highlight_format.setToolTip(f"{len(tasks)} tasks due")
            self.calendar.setDateTextFormat(date, highlight_format)

    def get_tasks_grouped_by_date(self):
        """
        Retrieve tasks grouped by their due dates.

        Returns:
            dict: A dictionary where keys are date strings in 'yyyy-MM-dd' format
                  and values are lists of Task objects due on that date.
        """
        tasks_by_date = {}
        for task_list_info in self.task_manager.get_task_lists():
            task_list = TaskList(task_list_info["list_name"], self.task_manager, task_list_info["pin"],
                                 task_list_info["queue"], task_list_info["stack"])
            for task in task_list.tasks:
                if task.due_date and task.due_date != "2000-01-01":
                    # Apply filters
                    if not self.apply_filters(task):
                        continue

                    date_str = task.due_date
                    if date_str not in tasks_by_date:
                        tasks_by_date[date_str] = []
                    tasks_by_date[date_str].append(task)
        return tasks_by_date

    def apply_filters(self, task):
        """Apply the selected filters to a task."""
        # Priority Filter
        if self.filter_priority_combo.currentText() != "All":
            if str(task.priority) != self.filter_priority_combo.currentText():
                return False

        # Status Filter
        if self.filter_status_combo.currentText() == "Completed" and not task.completed:
            return False
        if self.filter_status_combo.currentText() == "Not Completed" and task.completed:
            return False

        # Category Filter
        if self.filter_category_combo.currentText() != "All":
            if self.filter_category_combo.currentText() not in task.categories:
                return False

        return True

    def on_date_clicked(self, date):
        """Handle the event when a date is clicked on the calendar."""
        self.load_tasks_for_selected_date()

    def load_tasks_for_selected_date(self):
        """Load and display tasks for the currently selected date."""
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString("yyyy-MM-dd")
        tasks_by_date = self.get_tasks_grouped_by_date()
        self.task_list_widget.clear()

        if date_str in tasks_by_date:
            tasks = tasks_by_date[date_str]
            # Sort tasks by priority descending
            tasks.sort(key=lambda x: x.priority, reverse=True)
            for task in tasks:
                item = QListWidgetItem()
                # Create a widget to display task details
                task_widget = self.create_task_item_widget(task)
                item.setSizeHint(task_widget.sizeHint())
                self.task_list_widget.addItem(item)
                self.task_list_widget.setItemWidget(item, task_widget)
        else:
            self.task_list_widget.addItem("No tasks due on this date.")

    def create_task_item_widget(self, task):
        """
        Create a custom widget to display task details.

        Args:
            task (Task): The task to display.

        Returns:
            QWidget: The custom widget containing task details.
        """
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Task Title
        title_label = QLabel(task.title)
        title_font = QFont()
        title_font.setPointSize(10)
        if task.completed:
            title_font.setStrikeOut(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Spacer
        layout.addStretch()

        # Due Time (optional)
        if task.due_time and task.due_time != "00:00":
            due_time_label = QLabel(f"{task.due_time}")
            due_time_label.setStyleSheet("color: gray; font-size: 9px;")
            layout.addWidget(due_time_label)

        # Checkbox for completion
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task.completed)
        self.checkbox.stateChanged.connect(lambda state, t=task: self.mark_task_completed(t, state))
        layout.addWidget(self.checkbox)

        widget.setLayout(layout)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.mousePressEvent = lambda event, t=task: self.open_task_detail(t)
        return widget

    def mark_task_completed(self, task, state):
        """Mark the task as completed or not completed."""
        task.completed = bool(state)
        self.task_manager.update_task(task)
        global_signals.task_list_updated.emit()

    def open_task_detail(self, task):
        """
        Open the TaskDetailDialog for the selected task.

        Args:
            task (Task): The task to view/edit.
        """
        # Retrieve the shared TaskList instance
        if task.list_name in self.parent.task_lists:
            task_list = self.parent.task_lists[task.list_name]
        else:
            task_list = TaskList(task.list_name, self.task_manager, False, False, False)
            self.parent.task_lists[task.list_name] = task_list

        # Use the shared TaskListWidget instance
        task_list_widget = self.parent.hash_to_widget.get(task.list_name)
        if not task_list_widget:
            task_list_widget = TaskListWidget(task_list, self.parent)
            self.parent.hash_to_widget[task.list_name] = task_list_widget

        # Create the TaskDetailDialog
        dialog = TaskDetailDialog(task, task_list_widget, parent=self)
        global_signals.task_list_updated.emit()

        # Position the dialog to appear over the dock containing the task
        dock_widget = self
        if dock_widget:
            dock_pos = dock_widget.mapToGlobal(QPoint(0, 0))
            dock_size = dock_widget.size()

            # Adjust to make it slightly narrower and aligned to the right of the dock
            offset = int(0.2 * dock_size.width())
            dialog_width = dock_size.width() - offset
            dialog_height = dock_size.height()
            dialog_x = dock_pos.x() + offset
            dialog_y = dock_pos.y()

            dialog.resize(dialog_width, dialog_height)
            dialog.move(dialog_x, dialog_y)

            # Set fixed size to prevent resizing
            dialog.setFixedSize(dialog_width, dialog_height)
        else:
            # Default positioning if dock widget not found
            dialog.adjustSize()
            dialog.move(self.mapToGlobal(QPoint(0, 0)))

        dialog.exec()

    def on_task_clicked(self, item):
        """
        Handle the event when a task item is clicked.

        Args:
            item (QListWidgetItem): The clicked item.
        """
        # The checkbox state change is already handled; do nothing here
        pass

    def on_filter_changed(self, index):
        """Handle changes in the filters."""
        self.highlight_tasks_on_calendar()
        self.load_tasks_for_selected_date()

    def update_calendar(self):
        """Update the calendar highlights and task list when tasks are updated."""
        self.highlight_tasks_on_calendar()
        self.load_tasks_for_selected_date()
