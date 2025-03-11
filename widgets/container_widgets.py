from .task_widgets import *


class ResourcesWidget(QWidget):
    """
    A widget for managing a list of resources (URLs or file paths) associated with a task.
    Resources can be added, removed, and opened. Resources are displayed compactly and allow
    horizontal scrolling.
    """

    def __init__(self, task, task_list_widget, parent=None):
        """
        Initializes the ResourcesWidget with a scrollable area, an add button, and an input box.

        @param task: The task object to associate with this widget.
        @param task_list_widget: The task list widget to update the task.
        @param parent: The parent widget, if any.
        """
        super().__init__(parent)
        self.parent = parent
        self.task = task
        self.task_list_widget = task_list_widget
        self.setFixedHeight(60)
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        self.setLayout(self.main_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFixedHeight(50)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_widget = QWidget()
        self.scroll_layout = QHBoxLayout()
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(5)
        self.scroll_widget.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

        self.add_button = QPushButton("+", self)
        self.add_button.setFixedSize(30, 30)
        self.add_button.clicked.connect(self.show_input_box)
        self.main_layout.addWidget(self.add_button)

        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Enter URL or file path")
        self.input_box.setFixedSize(200, 30)
        self.input_box.hide()
        self.input_box.returnPressed.connect(self.add_new_resource)
        self.main_layout.addWidget(self.input_box)

        # Populate existing resources from the task
        for resource in self.task.resources:
            self.add_resource_node(resource)

        self.input_box.installEventFilter(self)

    def eventFilter(self, source, event):
        if source == self.input_box and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.add_new_resource()
                return True  # Event handled
        return super().eventFilter(source, event)

    def show_input_box(self):
        """
        Displays the input box for entering a new resource.
        """
        self.input_box.show()
        self.input_box.setFocus()

    def add_new_resource(self):
        """
        Adds a new resource based on the input box's text. The input box is hidden after adding the resource.
        """
        resource = self.input_box.text().strip()
        if resource:
            self.add_resource_node(resource)
            self.task.resources.append(resource)
            self.task_list_updated()
        self.input_box.hide()
        self.input_box.clear()

    def add_resource_node(self, resource):
        """
        Adds a resource node to the widget.

        @param resource The resource to be added, either a URL or a file path.
        """
        if self.is_url(resource):
            display_name = self.extract_display_name_from_url(resource)
            is_url = True
        else:
            display_name = os.path.basename(resource)
            is_url = False

        resource_container = QWidget()
        resource_layout = QHBoxLayout()
        resource_layout.setContentsMargins(0, 0, 0, 0)
        resource_layout.setSpacing(2)
        resource_container.setLayout(resource_layout)

        label = QLabel(display_name, self)
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setCursor(Qt.CursorShape.PointingHandCursor)
        label.mousePressEvent = lambda event, res=resource, url=is_url: self.open_resource(res, url)

        delete_button = QPushButton("x", self)
        delete_button.setFixedSize(20, 20)
        delete_button.setToolTip("Remove resource")
        delete_button.clicked.connect(lambda: self.remove_resource_node(resource_container, resource))

        resource_layout.addWidget(label)
        resource_layout.addWidget(delete_button)
        self.scroll_layout.addWidget(resource_container)

    def remove_resource_node(self, container, resource):
        """
        Removes a resource node from the widget and updates the task's resources.

        @param container The container widget holding the resource node to be removed.
        @param resource The resource string to remove from the task.
        """
        container.setParent(None)
        container.deleteLater()
        if resource in self.task.resources:
            self.task.resources.remove(resource)
            self.task_list_updated()

    def is_url(self, resource):
        """
        Checks whether a given resource is a URL.

        @param resource The resource to check.
        @return True if the resource is a URL, False otherwise.
        """
        return resource.startswith("http://") or resource.startswith("https://") or resource.startswith("file:///")

    def extract_display_name_from_url(self, url):
        """
        Extracts a display name from a URL, typically the domain name or the last path segment.

        @param url The URL to extract the display name from.
        @return The extracted display name.
        """
        parsed_url = QUrl(url)
        host = parsed_url.host()
        path = parsed_url.path()
        if host:
            return host
        elif path:
            return os.path.basename(path)
        else:
            return url

    def open_resource(self, resource, is_url):
        """
        Opens a resource. URLs are opened in the default web browser. File paths are opened
        with their associated application.

        @param resource The resource to open.
        @param is_url True if the resource is a URL, False if it is a file path.
        """
        if self.is_url(resource):
            if resource.startswith("file:///"):
                # Handle file URLs
                resource_path = resource.replace("file:///", "", 1)
                normalized_path = os.path.normpath(resource_path)
                if os.path.exists(normalized_path):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                else:
                    print(f"File not found: {normalized_path}")
            else:
                QDesktopServices.openUrl(QUrl(resource))
        else:
            normalized_path = os.path.normpath(resource)
            if os.path.exists(normalized_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
            else:
                print(f"File not found: {normalized_path}")

    def get_all_resources(self):
        """
        Returns a list of all resources currently added to the widget.

        @return A list of strings representing the resources.
        """
        return list(self.task.resources)

    def task_list_updated(self):
        """
        Updates the task in the database and emits a global signal.
        """
        self.task_list_widget.manager.update_task(self.task)
        global_signals.task_list_updated.emit()


class TaskDropdownsWidget(QWidget):
    """
    A custom widget that contains labeled dropdowns for task status,
    deadline flexibility, and effort level in the same row.
    """

    def __init__(self, task, parent=None):
        """
        Initializes the TaskDropdownsWidget.

        :param task: An object representing the task, with attributes for status,
                     flexibility, and effort_level.
        :param parent: Optional parent widget.
        """
        super().__init__(parent)
        self.task = task

        # Create the main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)  # Add spacing between dropdowns

        # Add labeled dropdowns with an empty option
        self.status_dropdown = self.add_labeled_dropdown(
            main_layout,
            "Status",
            ["Not Started", "In Progress", "Completed", "Failed", "On Hold"],
            self.task.status,
            lambda value: self.update_task_attribute('status', value)
        )

        self.flexibility_dropdown = self.add_labeled_dropdown(
            main_layout,
            "Deadline Flexibility",
            ["Strict", "Flexible", "Very Flexible"],
            self.task.flexibility,
            lambda value: self.update_task_attribute('flexibility', value)
        )

        self.effort_dropdown = self.add_labeled_dropdown(
            main_layout,
            "Effort Level",
            ["Low", "Medium", "High"],
            self.task.effort_level,
            lambda value: self.update_task_attribute('effort_level', value)
        )

        # Set the layout
        self.setLayout(main_layout)

    def add_labeled_dropdown(self, layout, label_text, items, current_value, on_change_callback):
        """
        Adds a label and a dropdown to the provided layout.

        :param layout: The layout to add the widgets to.
        :param label_text: The text for the label.
        :param items: A list of items to add to the dropdown.
        :param current_value: The current value to set in the dropdown.
        :param on_change_callback: A callback function to call when the selection changes.
        :return: Configured QComboBox instance.
        """
        # Create a vertical layout for the label and dropdown
        dropdown_layout = QVBoxLayout()
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_layout.setSpacing(0)  # Remove spacing between label and dropdown

        # Create and configure the label
        label = QLabel(label_text)
        font = QFont()
        font.setPointSize(8)  # Set small font size
        label.setFont(font)
        dropdown_layout.addWidget(label)

        # Create and configure the dropdown
        dropdown = QComboBox()
        dropdown.addItems([str(item) for item in items])  # Convert items to strings
        index = dropdown.findText(str(current_value)) if current_value else 0  # Convert current_value to string
        dropdown.setCurrentIndex(index)
        dropdown.currentTextChanged.connect(on_change_callback)
        dropdown_layout.addWidget(dropdown)

        # Add the vertical layout to the main horizontal layout
        layout.addLayout(dropdown_layout)

        return dropdown

    def update_task_attribute(self, attribute, value):
        """Update the task attribute, setting it to None if the value is empty."""
        if value == "":
            setattr(self.task, attribute, None)
        else:
            setattr(self.task, attribute, value)

    def connect_dropdown_signals(self, status_callback, flexibility_callback, effort_callback):
        """
        Connects external callbacks to the dropdown signals.
        :param status_callback: Callback for status dropdown.
        :param flexibility_callback: Callback for deadline flexibility dropdown.
        :param effort_callback: Callback for effort level dropdown.
        """
        self.status_dropdown.currentTextChanged.connect(status_callback)
        self.flexibility_dropdown.currentTextChanged.connect(flexibility_callback)
        self.effort_dropdown.currentTextChanged.connect(effort_callback)


class DescriptionContainer(QWidget):
    """
    A container widget with rounded edges, shadow effect, and a QTextEdit
    for displaying descriptions with adjustable height.
    """

    def __init__(self, description: str):
        """
        Initializes the DescriptionContainer with a description text.

        :param description: The text content to display in the container.
        """
        super().__init__()

        self.setAutoFillBackground(True)

        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow_effect)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.description_text_edit = QTextEdit(description)
        self.description_text_edit.setReadOnly(True)
        self.description_text_edit.viewport().setAutoFillBackground(False)
        self.description_text_edit.setContentsMargins(0, 0, 0, 0)
        self.description_text_edit.document().setDocumentMargin(0)
        self.layout.addWidget(self.description_text_edit)

        QTimer.singleShot(0, self.adjust_height)

    def adjust_height(self):
        """
        Adjusts the height of the container based on the content size
        and manages scrollbar visibility.
        """
        self.description_text_edit.document().adjustSize()
        content_height = int(self.description_text_edit.document().size().height())
        if 0 < content_height < 75:
            self.description_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.description_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setMaximumHeight(content_height)
        else:
            self.description_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.description_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setMaximumHeight(75)


class SubtaskItemWidget(QWidget):
    """
    Widget representing an individual subtask, allowing interaction via a checkbox and drag handle.
    """

    def __init__(self, subtask, parent=None):
        super().__init__(parent)
        self.subtask = subtask
        self.init_ui()
        self.parent = parent

    def init_ui(self):
        """
        Initialize the UI layout with a checkbox and drag handle.
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        print(f"Initializing subtask: {self.subtask}")  # Debug log

        self.checkbox = QCheckBox(self.subtask["name"])
        self.checkbox.setChecked(self.subtask["completed"])  # Sync with subtask
        self.checkbox.stateChanged.connect(self.on_state_changed)
        layout.addWidget(self.checkbox)

        layout.addStretch()

        self.drag_handle = QLabel()
        self.drag_handle.setCursor(Qt.CursorShape.OpenHandCursor)
        self.drag_handle.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.drag_handle)

        self.drag_start_position = None

    def on_state_changed(self, state):
        """
        Handle checkbox state change.
        """
        # Direct integer comparison
        is_checked = (state == 2)  # 2 corresponds to Qt.CheckState.Checked
        print(f"Checkbox state changed: {state}, is_checked computed as: {is_checked}")  # Debug log

        # Update the subtask
        self.subtask["completed"] = is_checked

        # Update the corresponding subtask in the parent's task list
        for subtask in self.parent.task.subtasks:
            if subtask["order"] == self.subtask["order"]:  # Match by unique identifier
                subtask["completed"] = is_checked
                break

        print(f"Subtask state updated: {self.subtask}")
        print(f"Parent subtasks list: {self.parent.task.subtasks}")  # Debugging output
        self.parent.update_subtask_completion()


class SubtaskWindow(QWidget):
    """
    Window for managing subtasks within a task, providing UI for adding, editing, deleting, and reordering subtasks.
    """

    def __init__(self, task, parent=None):
        super().__init__()
        self.parent = parent
        self.task = task
        self.manager = self.parent.task_list_widget.manager
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("border-radius: 10px;")
        self.setMinimumSize(50, 100)

        self.main_layout = QVBoxLayout(self)
        self.input_layout = QHBoxLayout()
        self.subtask_input = QLineEdit()
        self.subtask_input.setPlaceholderText("Add a subtask...")
        self.subtask_input.returnPressed.connect(self.add_subtask)
        self.input_layout.addWidget(self.subtask_input)
        self.main_layout.addLayout(self.input_layout)

        self.subtask_list = QListWidget()
        self.subtask_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.subtask_list.customContextMenuRequested.connect(self.show_context_menu)
        self.subtask_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.subtask_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.subtask_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.subtask_list.setDragEnabled(True)
        self.subtask_list.setAcceptDrops(True)
        self.subtask_list.viewport().setAcceptDrops(True)
        self.subtask_list.setDropIndicatorShown(True)
        self.subtask_list.model().rowsMoved.connect(self.on_subtask_reordered)
        self.main_layout.addWidget(self.subtask_list)

        self.load_subtasks()

    def load_subtasks(self):
        """
        Load existing subtasks from the task into the list widget.
        """
        self.subtask_list.clear()
        for subtask in self.task.subtasks:
            item = QListWidgetItem()
            widget = SubtaskItemWidget(subtask, parent=self)
            item.setSizeHint(widget.sizeHint())
            self.subtask_list.addItem(item)
            self.subtask_list.setItemWidget(item, widget)

    def add_subtask(self):
        """
        Add a new subtask to the task list and update the view.
        """
        subtask_name = self.subtask_input.text().strip()
        if subtask_name:
            new_subtask = {"order": len(self.task.subtasks), "name": subtask_name, "completed": False}
            self.task.subtasks.append(new_subtask)
            self.subtask_input.clear()
            self.load_subtasks()
        self.manager.update_task(self.task)
        global_signals.task_list_updated.emit()

    def update_subtask_completion(self):
        """
        Update subtask completion status and emit update signal.
        """
        self.manager.update_task(self.task)
        # print(self.task.subtasks)
        global_signals.task_list_updated.emit()

    def show_context_menu(self, position):
        """
        Show a context menu for editing or deleting subtasks.
        """
        item = self.subtask_list.itemAt(position)
        if item:
            menu = QMenu()
            edit_action = QAction("Edit")
            delete_action = QAction("Delete")
            menu.addAction(edit_action)
            menu.addAction(delete_action)

            action = menu.exec(self.subtask_list.viewport().mapToGlobal(position))
            if action == edit_action:
                self.edit_subtask(item)
            elif action == delete_action:
                self.delete_subtask(item)

    def edit_subtask(self, item):
        """
        Switch subtask item to edit mode with an input line for name change.
        """
        index = self.subtask_list.row(item)
        subtask = self.task.subtasks[index]
        widget = self.subtask_list.itemWidget(item)

        line_edit = QLineEdit(widget.checkbox.text())
        line_edit.returnPressed.connect(lambda: self.finish_edit_subtask(line_edit, item, subtask))
        line_edit.setFocus()

        widget.checkbox.hide()
        widget.layout().insertWidget(0, line_edit)
        widget.line_edit = line_edit

    def finish_edit_subtask(self, line_edit, item, subtask):
        """
        Complete editing and update the subtask name.
        """
        new_name = line_edit.text().strip()
        widget = self.subtask_list.itemWidget(item)
        if new_name:
            subtask["name"] = new_name
            widget.layout().removeWidget(line_edit)
            line_edit.deleteLater()
            widget.checkbox.setText(subtask["name"])
            widget.checkbox.show()
            del widget.line_edit
            self.subtask_list.clearFocus()
            self.clearFocus()
            self.manager.update_task(self.task)
            global_signals.task_list_updated.emit()
        else:
            self.delete_subtask(item)
            self.manager.update_task(self.task)
            global_signals.task_list_updated.emit()

    def delete_subtask(self, item):
        """
        Remove a subtask from the task list and update the view.
        """
        index = self.subtask_list.row(item)
        del self.task.subtasks[index]
        self.load_subtasks()
        self.manager.update_task(self.task)
        global_signals.task_list_updated.emit()

    def on_subtask_reordered(self):
        """
        Reorder subtasks within the list and update their order.
        """
        new_order = []
        for index in range(self.subtask_list.count()):
            widget = self.subtask_list.itemWidget(self.subtask_list.item(index))
            subtask = widget.subtask
            subtask["order"] = index
            new_order.append(subtask)
        self.task.subtasks = new_order
        self.manager.update_task(self.task)
        global_signals.task_list_updated.emit()


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
            from .dock_widgets import TaskListDock
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
                task_list = next((tl for tl in self.task_manager.task_lists if tl.name == task_list_name), None)
                task_list.category = new_category_name
                self.task_manager.update_task_list(task_list)

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
        self.setObjectName("TaskListCollection")

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        self.search_bar = QLineEdit(self)
        self.search_bar.setObjectName("TaskListSearch")
        self.search_bar.setPlaceholderText("Search...")
        self.layout.addWidget(self.search_bar)
        self.search_bar.textChanged.connect(self.filter_items)
        self.task_list_widget_in_focus_before_search = None

        self.tree_widget = CustomTreeWidget(self.parent)
        self.tree_widget.setObjectName("TaskListTree")
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
            # Reset visibility of all items and revert to previously focused task list
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

        # Iterate over categories and task lists
        for i in range(self.tree_widget.topLevelItemCount()):
            category_item = self.tree_widget.topLevelItem(i)
            category_visible = False
            if text.lower() in category_item.text(0).lower():
                category_visible = True
            for j in range(category_item.childCount()):
                task_list_item = category_item.child(j)
                task_list_visible = False
                task_list_name = task_list_item.text(0)
                task_list = next((tl for tl in self.task_manager.task_lists if tl.name == task_list_name), None)
                tasks = task_list.tasks if task_list else []
                for task in tasks:
                    if text.lower() in task.name.lower() or text.lower() in task.description.lower():
                        task_list_visible = True
                        break
                    for subtask in task.subtasks:
                        if text.lower() in subtask["name"].lower():
                            task_list_visible = True
                            break
                    if task_list_visible:
                        break
                task_list_item.setHidden(not task_list_visible)
                if task_list_visible:
                    category_visible = True
                    if first_match_task_list_name is None:
                        first_match_task_list_name = task_list_name
            category_item.setHidden(not category_visible)

        if first_match_task_list_name:
            print(f"Switching to task list: {first_match_task_list_name}")  # Debugging
            self.select_task_list_in_tree(first_match_task_list_name)
            self.parent.stacked_task_list.show_task_list(first_match_task_list_name)

    def load_task_lists(self):
        self.tree_widget.clear()
        self.categories = self.task_manager.categories

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
            if "task_lists" in category_info:  # If the category has task lists
                # Sort task lists by their order
                sorted_task_lists = sorted(
                    category_info['task_lists'],
                    key=lambda task_list: task_list.order
                )

                for task_list_info in sorted_task_lists:
                    task_list_name = task_list_info.name

                    task_list_item = QTreeWidgetItem(category_item)
                    task_list_item.setFlags(task_list_item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
                    task_list_item.setText(0, task_list_name)
                    task_list_item.setData(0, Qt.ItemDataRole.UserRole,
                                           {'type': 'task_list', 'info': task_list_info})
                    task_list_item.setFlags(task_list_item.flags())

                    task_list = next((tl for tl in self.task_manager.task_lists if tl.name == task_list_name), None)

                    hash_key = hash(task_list_name)
                    if hash_key not in self.parent.hash_to_task_list_widgets:
                        task_list_widget = TaskListWidget(task_list, self.parent)
                        self.parent.stacked_task_list.stack_widget.addWidget(task_list_widget)
                        self.parent.hash_to_task_list_widgets[hash_key] = task_list_widget

    def add_category(self):
        category_name, ok = QInputDialog.getText(self, "New Category", "Enter category name:")
        if ok and category_name.strip():
            category_name = category_name.strip()
            if category_name in self.categories:
                QMessageBox.warning(self, "Duplicate Category", "A category with this name already exists.")
                return
            self.categories[category_name] = {
                "order": len(self.categories),
                "task_lists": []
            }
            self.task_manager.add_category(category_name)
            self.load_task_lists()

    def add_task_list(self):
        task_list_name, ok = QInputDialog.getText(self, "New Task List", "Enter task list name:")
        if ok and task_list_name.strip():
            task_list_name = task_list_name.strip()
            # Check for duplicates
            if any(task_list_name == task_list.name for category in self.categories.values() for task_list
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
                    category_name = "Uncategorized"
            else:
                category_name = "Uncategorized"
            if category_name not in self.categories:
                category_name = "Uncategorized"

            # Add the task list
            task_list = TaskList(name=task_list_name, category=category_name)
            self.task_manager.add_task_list(task_list)
            # Update self.categories
            self.categories = self.task_manager.categories

            # Add to the stack widget
            task_list_widget = TaskListWidget(task_list, self.parent)
            self.parent.stacked_task_list.stack_widget.addWidget(task_list_widget)
            self.parent.hash_to_task_list_widgets[hash(task_list_name)] = task_list_widget
            self.parent.stacked_task_list.stack_widget.setCurrentWidget(task_list_widget)
            self.select_task_list_in_tree(task_list_name)
            self.load_task_lists()

    def add_task_list_to_category(self, category_item):
        # Get the category name
        category_name = category_item.text(0)

        # Ask for a task list name
        task_list_name, ok = QInputDialog.getText(self, "New Task List", "Enter task list name:")
        if ok and task_list_name.strip():
            task_list_name = task_list_name.strip()

            # Check if the task list already exists in the category
            if any(task_list_name == task_list.name for task_list in
                   self.categories[category_name]['task_lists']):
                QMessageBox.warning(self, "Duplicate Task List",
                                    "A task list with this name already exists in this category.")
                return

            # Add the task list to the category
            self.task_manager.add_task_list(TaskList(name=task_list_name, category=category_name))

            # Reload the task lists and update the UI
            self.categories = self.task_manager.categories
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
            if hash_key in self.parent.hash_to_task_list_widgets:
                self.parent.stacked_task_list.stack_widget.setCurrentWidget(
                    self.parent.hash_to_task_list_widgets[hash_key])
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
                    task_list_name = task_list_info.name

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
            if any(new_name == task_list.name for category in self.categories.values() for task_list in
                   category["task_lists"]):
                QMessageBox.warning(self, "Duplicate Task List", "A task list with this name already exists.")
                return

            # Update task list name in the categories structure
            category_name = item.parent().text(0)
            for task_list in self.categories[category_name]['task_lists']:
                if task_list.name == old_name:
                    task_list.name = new_name
                    # Update in task manager (database)
                    self.task_manager.update_task_list(task_list)
                    break

            # Update in UI
            item.setText(0, new_name)

            # Update hash_to_widget
            self.parent.hash_to_task_list_widgets[hash(new_name)] = self.parent.hash_to_task_list_widgets.pop(
                hash(old_name))

            # Reload task lists and select the renamed task list
            self.load_task_lists()
            self.select_task_list_in_tree(new_name)

    def delete_task_list(self, item):
        task_list_name = item.text(0)
        reply = QMessageBox.question(self, 'Delete Task List', f'Are you sure you want to delete "{task_list_name}"?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            category_name = item.parent().text(0)
            if category_name in self.categories:
                self.categories[category_name]["task_lists"] = [
                    task_list for task_list in self.categories[category_name]["task_lists"] if
                    task_list.name != task_list_name
                ]

            self.task_manager.remove_task_list(task_list_name)

            index = self.tree_widget.indexOfTopLevelItem(item)
            if index != -1:
                self.tree_widget.takeTopLevelItem(index)
            else:
                item.parent().removeChild(item)

            hash_key = hash(task_list_name)
            if hash_key in self.parent.hash_to_task_list_widgets:
                widget_to_remove = self.parent.hash_to_task_list_widgets.pop(hash_key)
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
                self.categories = self.task_manager.categories
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
                task_lists_in_category = [
                    task_list for task_list in self.categories.get(category_name, {}).get("task_lists", [])
                    if task_list.category == category_name
                ]
                for task_list_info in task_lists_in_category:
                    task_list_name = task_list_info.name

                    # Remove from task manager
                    self.task_manager.remove_task_list(task_list_name)

                    # Remove from stack widget
                    hash_key = hash(task_list_name)
                    if hash_key in self.parent.hash_to_task_list_widgets:
                        widget_to_remove = self.parent.hash_to_task_list_widgets.pop(hash_key)
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
