from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from datetime import datetime
from task_manager import *
from gui import global_signals


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
            print(self.task.resources)
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
        self.task_list_widget.task_list.update_task(self.task)
        global_signals.task_list_updated.emit()


class CountProgressWidget(QWidget):
    """
    A sleek widget displaying a progress bar with count tracking,
    including increment and decrement buttons, and percentage completed.
    """

    def __init__(self, task, task_list_widget, parent=None):
        """
        Initializes the CountProgressWidget.

        :param task: The task object associated with this widget.
        :param task_list_widget: The task list widget to update the task.
        :param parent: Optional parent widget.
        """
        super().__init__(parent)

        self.task = task
        self.task_list_widget = task_list_widget
        self.count_required = self.task.count_required
        self.count_completed = self.task.count_completed

        # Main layout
        self.progress_layout = QHBoxLayout(self)
        self.progress_layout.setContentsMargins(10, 5, 10, 5)
        self.progress_layout.setSpacing(5)

        # Decrement button
        self.decrement_button = QPushButton("−", self)
        self.decrement_button.setFixedSize(30, 30)
        self.decrement_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.decrement_button.clicked.connect(self.decrement_count)
        self.progress_layout.addWidget(self.decrement_button)

        # Spacer between decrement button and progress bar
        self.progress_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(self.count_required)
        self.progress_bar.setValue(self.count_completed)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_layout.addWidget(self.progress_bar)

        # Spacer between progress bar and count label
        self.progress_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Count label
        self.count_label = QLabel(self)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_layout.addWidget(self.count_label)

        # Spacer between count label and increment button
        self.progress_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Increment button
        self.increment_button = QPushButton("+", self)
        self.increment_button.setFixedSize(30, 30)
        self.increment_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.increment_button.clicked.connect(self.increment_count)
        self.progress_layout.addWidget(self.increment_button)

        # Initial update
        self.update_progress()

    def increment_count(self):
        """Increments the completed count and updates the progress bar and labels."""
        if self.count_completed < self.count_required:
            self.count_completed += 1
            self.task.count_completed = self.count_completed
            self.update_task()
            self.update_progress()

    def decrement_count(self):
        """Decrements the completed count and updates the progress bar and labels."""
        if self.count_completed > 0:
            self.count_completed -= 1
            self.task.count_completed = self.count_completed
            self.update_task()
            self.update_progress()

    def update_progress(self):
        """Updates the progress bar, count, and percentage labels."""
        self.progress_bar.setValue(self.count_completed)
        percentage = (self.count_completed / self.count_required) * 100 if self.count_required > 0 else 0
        self.progress_bar.setFormat(f"{percentage:.0f}%")
        self.count_label.setText(f"{self.count_completed}/{self.count_required}")

    def update_task(self):
        """Updates the task in the database and emits a global signal."""
        self.task_list_widget.task_list.update_task(self.task)
        global_signals.task_list_updated.emit()


class TimeProgressWidget(QWidget):
    """
    A sleek widget displaying a progress bar for time logged,
    including increment, decrement, and record buttons.
    """

    def __init__(self, task, task_list_widget, parent=None):
        """
        Initializes the TimeProgressWidget.

        :param task: The task object associated with this widget.
        :param task_list_widget: The task list widget to update the task.
        :param parent: Optional parent widget.
        """
        super().__init__(parent)

        self.task = task
        self.task_list_widget = task_list_widget
        self.estimate = self.task.estimate
        self.time_logged = self.task.time_logged

        # Main layout
        self.time_layout = QHBoxLayout(self)
        self.time_layout.setContentsMargins(10, 5, 10, 5)
        self.time_layout.setSpacing(5)

        # Decrement button
        self.decrement_time_button = QPushButton("−", self)
        self.decrement_time_button.setFixedSize(30, 30)
        self.decrement_time_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.decrement_time_button.clicked.connect(self.decrement_time_logged)
        self.time_layout.addWidget(self.decrement_time_button)

        # Spacer between decrement button and progress bar
        self.time_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Progress bar
        self.time_progress_bar = QProgressBar(self)
        self.time_progress_bar.setMinimum(0)
        self.time_progress_bar.setMaximum(int(self.estimate))
        self.time_progress_bar.setValue(int(self.time_logged))
        self.time_progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_layout.addWidget(self.time_progress_bar)

        # Spacer between progress bar and time label
        self.time_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Time label
        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_layout.addWidget(self.time_label)

        # Spacer between time label and buttons
        self.time_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Increment and record buttons
        self.increment_time_button = QPushButton("+", self)
        self.increment_time_button.setFixedSize(30, 30)
        self.increment_time_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.increment_time_button.clicked.connect(self.increment_time_logged)
        self.time_layout.addWidget(self.increment_time_button)

        self.record_time_button = QPushButton("⏱", self)
        self.record_time_button.setFixedSize(30, 30)
        self.record_time_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.record_time_button.clicked.connect(self.record_time)
        self.time_layout.addWidget(self.record_time_button)

        # Initial update
        self.update_progress()

    def increment_time_logged(self):
        """Increments the time logged and updates the progress bar and labels."""
        if self.time_logged < self.estimate:
            self.time_logged += 1
            self.task.time_logged = self.time_logged
            self.update_task()
            self.update_progress()

    def decrement_time_logged(self):
        """Decrements the time logged and updates the progress bar and labels."""
        if self.time_logged > 0:
            self.time_logged -= 1
            self.task.time_logged = self.time_logged
            self.update_task()
            self.update_progress()

    def record_time(self):
        """Records an additional hour of work (or other logic)."""
        # Implement recording logic here
        pass

    def update_progress(self):
        """Updates the progress bar and time labels."""
        self.time_progress_bar.setValue(int(self.time_logged))
        percentage = (self.time_logged / self.estimate) * 100 if self.estimate > 0 else 0
        self.time_progress_bar.setFormat(f"{percentage:.0f}%")
        time_logged_display = f"{self.time_logged:.2f}".rstrip("0").rstrip(".")
        estimate_display = f"{self.estimate:.2f}".rstrip("0").rstrip(".")
        self.time_label.setText(f"Hr: {time_logged_display}/{estimate_display}")

    def update_task(self):
        """Updates the task in the database and emits a global signal."""
        self.task_list_widget.task_list.update_task(self.task)
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
                     deadline_flexibility, and effort_level.
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
            [""] + ["Not Started", "In Progress", "Completed", "Failed", "On Hold"],
            self.task.status,
            lambda value: self.update_task_attribute('status', value)
        )

        self.flexibility_dropdown = self.add_labeled_dropdown(
            main_layout,
            "Deadline Flexibility",
            [""] + ["Strict", "Flexible"],
            self.task.deadline_flexibility,
            lambda value: self.update_task_attribute('deadline_flexibility', value)
        )

        self.effort_dropdown = self.add_labeled_dropdown(
            main_layout,
            "Effort Level",
            [""] + ["Easy", "Medium", "Hard"],
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
        dropdown.addItems(items)
        index = dropdown.findText(current_value) if current_value else 0
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

        self.checkbox = QCheckBox(self.subtask.title)
        self.checkbox.setChecked(self.subtask.completed)
        self.checkbox.stateChanged.connect(self.on_state_changed)
        layout.addWidget(self.checkbox)

        layout.addStretch()

        self.drag_handle = QLabel()
        self.drag_handle.setCursor(Qt.CursorShape.OpenHandCursor)
        self.drag_handle.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.drag_handle)

        self.drag_handle.mousePressEvent = self.drag_handle_mouse_press_event
        self.drag_handle.mouseMoveEvent = self.drag_handle_mouse_move_event
        self.drag_handle.mouseReleaseEvent = self.drag_handle_mouse_release_event

        self.drag_start_position = None

    def on_state_changed(self, state):
        """
        Handle checkbox state change.
        """
        self.subtask.completed = (state == Qt.CheckState.Checked)
        self.parent.toggle_subtask_completion(self.subtask, state)

    def drag_handle_mouse_press_event(self, event):
        """
        Handle mouse press event for drag functionality.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            self.drag_handle.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def drag_handle_mouse_move_event(self, event):
        """
        Handle mouse movement to initiate drag if beyond drag threshold.
        """
        if event.buttons() & Qt.MouseButton.LeftButton:
            if (event.pos() - self.drag_start_position).manhattanLength() > QApplication.startDragDistance():
                self.start_drag()
                event.accept()

    def drag_handle_mouse_release_event(self, event):
        """
        Reset cursor when mouse button is released.
        """
        self.drag_handle.setCursor(Qt.CursorShape.OpenHandCursor)
        self.clearFocus()
        event.accept()

    def start_drag(self):
        """
        Initiate a drag-and-drop operation for the widget.
        """
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.subtask.id))
        drag.setMimeData(mime_data)

        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)

        drag.exec(Qt.DropAction.MoveAction)


class SubtaskWindow(QWidget):
    """
    Window for managing subtasks within a task, providing UI for adding, editing, deleting, and reordering subtasks.
    """

    def __init__(self, task, task_list):
        super().__init__()
        self.task = task
        self.task_list = task_list
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("border-radius: 10px;")
        self.setMinimumSize(50, 100)

        self.main_layout = QVBoxLayout(self)
        # self.main_layout.setContentsMargins(10, 10, 10, 10)

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
            item.setData(Qt.ItemDataRole.UserRole, subtask.id)
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
            new_subtask = Subtask(title=subtask_name, completed=False, task_id=self.task.id)
            self.task_list.add_subtask(self.task, new_subtask)
            self.subtask_input.clear()
            self.load_subtasks()

    def toggle_subtask_completion(self, subtask, state):
        """
        Toggle the completion status of a subtask.
        """
        subtask.completed = (state == Qt.CheckState.Checked)
        self.task_list.update_subtask(subtask)

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
        Complete editing and update the subtask name in the database.
        """
        new_name = line_edit.text().strip()
        widget = self.subtask_list.itemWidget(item)
        if new_name:
            subtask.title = new_name
            self.task_list.update_subtask(subtask)
            widget.layout().removeWidget(line_edit)
            line_edit.deleteLater()
            widget.checkbox.setText(subtask.title)
            widget.checkbox.show()
            del widget.line_edit
            self.subtask_list.clearFocus()
            self.clearFocus()
        else:
            self.delete_subtask(item)

    def delete_subtask(self, item):
        """
        Remove a subtask from the task list and update the view.
        """
        index = self.subtask_list.row(item)
        subtask = self.task.subtasks[index]
        self.task_list.remove_subtask(self.task, subtask)
        self.load_subtasks()

    def on_subtask_reordered(self, start, end, destination, row):
        """
        Reorder subtasks within the list and update their order in the database.
        """
        id_to_subtask = {subtask.id: subtask for subtask in self.task.subtasks}
        new_order_ids = [self.subtask_list.item(index).data(Qt.ItemDataRole.UserRole)
                         for index in range(self.subtask_list.count())]

        for index, subtask_id in enumerate(new_order_ids):
            subtask = id_to_subtask[subtask_id]
            subtask.order = index
            self.task_list.update_subtask(subtask)

        self.task.subtasks = [id_to_subtask[subtask_id] for subtask_id in new_order_ids]
        self.task_list.update_task(self.task)

        self.subtask_list.clearSelection()
        self.subtask_list.clearFocus()


class TagInputWidget(QWidget):
    """
    A widget that allows users to input and manage tags dynamically.
    Tags can be added from a predefined list or entered manually. Each tag
    is displayed with a delete button for easy removal.
    """

    def __init__(self, tags, tag_list=None):
        """
        Initializes the TagInputWidget.

        :param tags: A list of available tags to suggest in the input field.
        :param tag_list: An optional list of pre-existing tags to initialize the widget with.
        """
        super().__init__()
        if tag_list is None:
            tag_list = []
        self.available_tags = tags
        self.tag_list = tag_list

        self.layout = QVBoxLayout()
        self.input_field = QComboBox(self)
        self.input_field.setEditable(True)
        self.input_field.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.input_field.lineEdit().setPlaceholderText("add a tag...")
        self.input_field.addItems(self.available_tags)
        self.input_field.setCurrentIndex(-1)
        self.input_field.lineEdit().returnPressed.connect(self.add_tag)
        self.input_field.lineEdit().textEdited.connect(self.update_suggestions)

        self.tags_layout = QHBoxLayout()
        self.layout.addLayout(self.tags_layout)
        self.layout.addWidget(self.input_field)
        self.setLayout(self.layout)

        if self.tag_list:
            for tag in self.tag_list:
                self.add_existing_tag(tag)
            self.reset_suggestions()

    def add_tag(self):
        """
        Adds a new tag from the input field to the tag list if it is valid
        and not already present.
        """
        tag_text = self.input_field.currentText().strip()
        if tag_text and tag_text not in self.tag_list:
            self.add_existing_tag(tag_text)
            self.tag_list.append(tag_text)
            self.input_field.setCurrentText("")
            self.reset_suggestions()

    def add_existing_tag(self, tag_text):
        """
        Creates a tag display with the specified text and a delete button.

        :param tag_text: The text of the tag to be added.
        """
        tag_label = QLabel(f"{tag_text} ")
        delete_button = QPushButton("x")
        delete_button.setFixedSize(15, 25)
        delete_button.clicked.connect(lambda _, t=tag_text: self.remove_tag(t))

        tag_layout = QHBoxLayout()
        tag_layout.addWidget(tag_label)
        tag_layout.addWidget(delete_button)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(0)

        tag_widget = QWidget()
        tag_widget.setLayout(tag_layout)
        self.tags_layout.addWidget(tag_widget)
        tag_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def remove_tag(self, tag_text):
        """
        Removes a tag from the tag list and its associated widget from the UI.

        :param tag_text: The text of the tag to be removed.
        """
        for i in reversed(range(self.tags_layout.count())):
            tag_widget = self.tags_layout.itemAt(i).widget()
            tag_label = tag_widget.findChild(QLabel)
            if tag_label and tag_label.text().strip() == f"{tag_text}":
                self.tags_layout.takeAt(i).widget().deleteLater()
                self.tag_list.remove(tag_text)
                self.reset_suggestions()
                break

    def update_suggestions(self, text):
        self.filtered_tags = [tag for tag in self.available_tags if text.lower() in tag.lower()]
        self.input_field.clear()
        self.input_field.addItems(self.filtered_tags)
        self.input_field.setCurrentText(text)

    def reset_suggestions(self):
        self.filtered_tags = [tag for tag in self.available_tags if tag not in self.tag_list]
        self.input_field.clear()
        self.input_field.addItems(self.filtered_tags)
        self.input_field.setCurrentIndex(-1)

    def get_tags(self):
        return self.tag_list


class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setObjectName("customDateEdit")

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.date() == QDate(2000, 1, 1):
            self.setDate(QDate.currentDate())


class AddTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")

        # Set dialog properties
        self.resize(500, 400)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Tab widget
        self.tab_widget = QTabWidget(self)
        self.main_layout.addWidget(self.tab_widget)

        # Basic Tab
        self.basic_tab = QWidget()
        self.basic_layout = QFormLayout(self.basic_tab)

        # Basic Fields
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("Enter task title")
        self.basic_layout.addRow("Title*:", self.title_edit)

        self.description_edit = QLineEdit(self)
        self.description_edit.setPlaceholderText("Enter task description")
        self.basic_layout.addRow("Description:", self.description_edit)

        self.due_date_edit = CustomDateEdit(self)
        self.basic_layout.addRow("Due Date:", self.due_date_edit)

        self.due_time_edit = QTimeEdit(self)
        self.basic_layout.addRow("Due Time:", self.due_time_edit)

        self.priority_spinbox = QSpinBox(self)
        self.priority_spinbox.setMinimum(0)
        self.priority_spinbox.setMaximum(10)
        self.priority_spinbox.setValue(0)
        self.basic_layout.addRow("Priority:", self.priority_spinbox)

        categories = []
        # if a TaskListDock
        if parent.type == "dock":
            categories = parent.task_list_widget.task_list.get_task_categories()
        elif parent.type == "stack":  # if TaskListStacked
            categories = parent.get_current_task_list_widget().task_list.get_task_categories()

        self.categories_input = TagInputWidget(categories)
        self.basic_layout.addRow("Category:", self.categories_input)

        self.important_checkbox = QCheckBox("Important", self)
        self.basic_layout.addRow(self.important_checkbox)

        self.recurring_checkbox = QCheckBox("Recurring", self)
        self.basic_layout.addRow(self.recurring_checkbox)

        # Recurrence Options
        self.recurrence_options_widget = QWidget()
        self.recurrence_layout = QVBoxLayout(self.recurrence_options_widget)

        self.recur_type_group = QButtonGroup(self)

        self.every_n_days_radio = QRadioButton("Every N days")
        self.specific_weekdays_radio = QRadioButton("Specific weekdays")

        self.recur_type_group.addButton(self.every_n_days_radio)
        self.recur_type_group.addButton(self.specific_weekdays_radio)

        self.recurrence_layout.addWidget(self.every_n_days_radio)
        self.recurrence_layout.addWidget(self.specific_weekdays_radio)

        # Every N Days Widget
        self.every_n_days_widget = QWidget()
        self.every_n_days_layout = QHBoxLayout(self.every_n_days_widget)

        self.every_n_days_label = QLabel("Every")
        self.every_n_days_spinbox = QSpinBox()
        self.every_n_days_spinbox.setMinimum(1)
        self.every_n_days_spinbox.setMaximum(365)
        self.every_n_days_spinbox.setValue(1)
        self.every_n_days_unit_label = QLabel("day(s)")

        self.every_n_days_layout.addWidget(self.every_n_days_label)
        self.every_n_days_layout.addWidget(self.every_n_days_spinbox)
        self.every_n_days_layout.addWidget(self.every_n_days_unit_label)

        # Specific Weekdays Widget
        self.specific_weekdays_widget = QWidget()
        self.specific_weekdays_layout = QHBoxLayout(self.specific_weekdays_widget)

        self.weekday_checkboxes = []
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day in weekdays:
            checkbox = QCheckBox(day)
            checkbox.setObjectName(f"{day}Checkbox")
            self.weekday_checkboxes.append(checkbox)
            self.specific_weekdays_layout.addWidget(checkbox)

        self.recurrence_layout.addWidget(self.every_n_days_widget)
        self.recurrence_layout.addWidget(self.specific_weekdays_widget)

        # Initially hide recurrence detail widgets
        self.every_n_days_widget.hide()
        self.specific_weekdays_widget.hide()

        # Add recurrence options to basic layout
        self.basic_layout.addRow(self.recurrence_options_widget)

        # Connect signals
        self.recurring_checkbox.stateChanged.connect(self.toggle_recurrence_options)
        self.every_n_days_radio.toggled.connect(self.update_recurrence_detail_widgets)
        self.specific_weekdays_radio.toggled.connect(self.update_recurrence_detail_widgets)

        # Add Basic Tab to Tab Widget
        self.tab_widget.addTab(self.basic_tab, "Basic")

        # Advanced Tab
        self.advanced_tab = QWidget()
        self.advanced_layout = QFormLayout(self.advanced_tab)

        # Advanced Fields
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Not Started", "In Progress", "Completed", "Failed", "On Hold"])
        self.status_combo.setCurrentIndex(-1)
        self.advanced_layout.addRow("Status:", self.status_combo)

        self.estimate_spinbox = QDoubleSpinBox()
        self.estimate_spinbox.setMinimum(0.0)
        self.estimate_spinbox.setMaximum(1000.0)
        self.estimate_spinbox.setDecimals(2)
        self.advanced_layout.addRow("Estimate (hours):", self.estimate_spinbox)

        self.count_required_spinbox = QSpinBox()
        self.count_required_spinbox.setMinimum(0)
        self.count_required_spinbox.setMaximum(1000)
        self.advanced_layout.addRow("Count Required:", self.count_required_spinbox)

        self.count_completed_spinbox = QSpinBox()
        self.count_completed_spinbox.setMinimum(0)
        self.count_completed_spinbox.setMaximum(1000)
        self.advanced_layout.addRow("Count Completed:", self.count_completed_spinbox)

        self.dependencies_edit = QLineEdit()
        self.dependencies_edit.setPlaceholderText("Dependency tasks, separated by commas")
        self.advanced_layout.addRow("Dependencies:", self.dependencies_edit)

        self.deadline_flexibility_combo = QComboBox()
        self.deadline_flexibility_combo.addItems(["Strict", "Flexible"])
        self.deadline_flexibility_combo.setCurrentIndex(-1)  # Initialize to None
        self.advanced_layout.addRow("Deadline Flexibility:", self.deadline_flexibility_combo)

        self.effort_level_combo = QComboBox()
        self.effort_level_combo.addItems(["Easy", "Medium", "Hard"])
        self.effort_level_combo.setCurrentIndex(-1)  # Initialize to None
        self.advanced_layout.addRow("Effort Level:", self.effort_level_combo)

        self.resources_edit = QLineEdit()
        self.resources_edit.setPlaceholderText("Resources, separated by commas")
        self.advanced_layout.addRow("Resources:", self.resources_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(60)
        self.advanced_layout.addRow("Notes:", self.notes_edit)

        self.time_logged_spinbox = QDoubleSpinBox()
        self.time_logged_spinbox.setMinimum(0.0)
        self.time_logged_spinbox.setMaximum(1000.0)
        self.time_logged_spinbox.setDecimals(2)
        self.advanced_layout.addRow("Time Logged (hours):", self.time_logged_spinbox)

        # Add Advanced Tab to Tab Widget
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        # Dialog Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

        self.title_edit.setFocus()

        # Object Names (for styling or testing)
        self.setObjectName("addTaskDialog")

    def focusOutEvent(self, event):
        print("lost focus")
        self.close()

    def keyPressEvent(self, event, **kwargs):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.categories_input.input_field.lineEdit().hasFocus():
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def toggle_recurrence_options(self, state):
        if state == Qt.CheckState.Checked.value:
            self.recurrence_options_widget.show()
            self.every_n_days_radio.setChecked(True)
            self.update_recurrence_detail_widgets()
        else:
            self.recurrence_options_widget.hide()

    def update_recurrence_detail_widgets(self):
        if self.every_n_days_radio.isChecked():
            self.every_n_days_widget.show()
            self.specific_weekdays_widget.hide()
        elif self.specific_weekdays_radio.isChecked():
            self.every_n_days_widget.hide()
            self.specific_weekdays_widget.show()
        else:
            self.every_n_days_widget.hide()
            self.specific_weekdays_widget.hide()

    def accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
            return
        super().accept()

    def get_task_data(self):
        task_data = {
            "title": self.title_edit.text(),
            "description": self.description_edit.text(),
            "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
            "due_time": self.due_time_edit.time().toString("HH:mm"),
            "priority": self.priority_spinbox.value(),
            "categories": self.categories_input.get_tags(),
            "is_important": self.important_checkbox.isChecked(),
            "recurring": self.recurring_checkbox.isChecked(),
            "recur_every": [],  # Calculated below
            # Default Advanced Fields
            "status": self.status_combo.currentText() if self.status_combo.currentText() else None,
            "estimate": self.estimate_spinbox.value(),
            "count_required": self.count_required_spinbox.value(),
            "count_completed": self.count_completed_spinbox.value(),
            "dependencies": [],
            "deadline_flexibility": self.deadline_flexibility_combo.currentText() if self.deadline_flexibility_combo.currentText() else None,
            "effort_level": self.effort_level_combo.currentText() if self.effort_level_combo.currentText() else None,
            "resources": [],
            "notes": self.notes_edit.toPlainText(),
            "time_logged": self.time_logged_spinbox.value()
        }

        # Recurrence Data
        if self.recurring_checkbox.isChecked():
            if self.every_n_days_radio.isChecked():
                task_data["recur_every"] = int(self.every_n_days_spinbox.value())
            elif self.specific_weekdays_radio.isChecked():
                selected_weekdays = []
                for checkbox in self.weekday_checkboxes:
                    if checkbox.isChecked():
                        selected_weekdays.append(checkbox.text())
                task_data["recur_every"] = selected_weekdays
        else:
            task_data["recur_every"] = None

        # Advanced Data
        dependencies_text = self.dependencies_edit.text()
        task_data["dependencies"] = [dep.strip() for dep in dependencies_text.split(",") if dep.strip()]
        resources_text = self.resources_edit.text()
        task_data["resources"] = [res.strip() for res in resources_text.split(",") if res.strip()]

        return task_data


class TaskDetailDialog(QDialog):
    def __init__(self, task, task_list_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Task Details")

        # Set dialog properties
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.task = task
        self.task_list_widget = task_list_widget
        self.is_edit_mode = False

        self.setup_ui()
        self.display_task_details()
        self.setup_due_date_display()
        self.installEventFilter(self)

    def setup_ui(self):
        # Main layout for the dialog
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Container widget for the content
        self.content_widget = QWidget()
        self.main_layout.addWidget(self.content_widget)

        # Layout for the content widget
        self.content_layout = QVBoxLayout(self.content_widget)

        # Header Layout: Task Name, Due Date, Edit, and Close Buttons
        self.header_layout = QHBoxLayout()

        # Initialize the Task Name Label as a QLabel initially
        self.task_name_label = QLabel()
        self.task_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.task_name_label.setText(self.task.title)  # Set initial text from task
        self.task_name_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.task_name_label.mousePressEvent = self.edit_task_name  # Trigger edit on click
        self.header_layout.addWidget(self.task_name_label)

        # Due Date Label
        self.due_date_label = QLabel()
        self.due_date_label.setStyleSheet("font-size: 14px; color: gray;")
        self.due_date_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.due_date_label.mousePressEvent = self.open_due_date_picker
        self.header_layout.addWidget(self.due_date_label)

        self.header_layout.addStretch()

        # Edit Button
        self.edit_button = QPushButton("Edit")
        self.edit_button.setFixedSize(60, 24)
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        self.header_layout.addWidget(self.edit_button)

        # Close Button
        self.close_button = QPushButton("Close")
        self.close_button.setFixedSize(60, 24)
        self.close_button.clicked.connect(self.close)
        self.header_layout.addWidget(self.close_button)

        self.content_layout.addLayout(self.header_layout)

        # Separator Line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.content_layout.addWidget(separator)

        # Task Details Area with white background and reduced spacing
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_layout.setSpacing(2)  # Adjust spacing between widgets

        self.details_widget.setLayout(self.details_layout)
        self.content_layout.addWidget(self.details_widget)

        # Buttons Layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addStretch()

        # Save and Cancel Buttons (only in edit mode)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_task_edits)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_edits)

        # Add buttons to the buttons_layout
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)

        # Initially hide the buttons
        self.save_button.hide()
        self.cancel_button.hide()

        # Add the buttons_layout to the main_layout
        self.main_layout.addLayout(self.buttons_layout)

    def display_task_details(self):
        # Clear existing widgets
        self.clear_layout(self.details_layout)
        self.details_layout.setContentsMargins(0, 0, 0, 0)

        # Update task name
        self.task_name_label.setText(self.task.title)

        # If task is recurring, show when it is recurring
        if self.task.recurring:
            recurring_list = self.task.recur_every
            if all(isinstance(item, str) for item in recurring_list):
                # Convert each item in the list to a string before joining
                str_recurring_list = ", ".join(map(str, recurring_list))
                str_recurring_list = "Due every " + str_recurring_list
            else:
                str_recurring_list = str(recurring_list[0])

                if self.task.last_completed_date is not None:
                    days_due_in = (self.task.last_completed_date + timedelta(
                        days=int(recurring_list[0])) - datetime.now()).days
                    str_recurring_list = f"Due every {str_recurring_list} days, next in {days_due_in} days."
                else:
                    str_recurring_list = f"Due every {str_recurring_list} days."

            recurring_label = QLabel(str_recurring_list)
            recurring_label.setStyleSheet("font-size: 12px; color: gray;")
            recurring_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            self.details_layout.addWidget(recurring_label, alignment=Qt.AlignmentFlag.AlignRight)

        dropdowns = TaskDropdownsWidget(task=self.task, parent=self)
        dropdowns.connect_dropdown_signals(
            lambda value: self.update_task_attribute('status', value),
            lambda value: self.update_task_attribute('deadline_flexibility', value),
            lambda value: self.update_task_attribute('effort_level', value)
        )
        self.details_layout.addWidget(dropdowns)

        # Check if task has a description
        if self.task.description:
            description_container = DescriptionContainer(self.task.description)
            self.details_layout.addWidget(description_container, stretch=0)

        sub_task_window = SubtaskWindow(self.task, self.task_list_widget.task_list)
        self.details_layout.addWidget(sub_task_window)

        # Resources
        self.resources_widget = ResourcesWidget(self.task, self.task_list_widget, parent=self)
        self.details_layout.addWidget(self.resources_widget)

        # Progress Bar for Count
        # Progress Bar for Count
        if self.task.count_required > 0:
            progress_bar = CountProgressWidget(task=self.task, task_list_widget=self.task_list_widget, parent=self)
            self.details_layout.addWidget(progress_bar)

        # Progress Bar for Time Logged
        if self.task.estimate > 0:
            time_bar = TimeProgressWidget(task=self.task, task_list_widget=self.task_list_widget, parent=self)
            self.details_layout.addWidget(time_bar)

        # Notes
        if self.task.notes:
            notes_label = QLabel("Note:")
            notes_label.setStyleSheet("font-weight: bold;")
            self.details_layout.addWidget(notes_label)
            notes_content = QLabel(self.task.notes)
            notes_content.setWordWrap(True)
            self.details_layout.addWidget(notes_content)

        # Create the tag layout
        tag_layout = QHBoxLayout()
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(5)  # Adds spacing between tags
        tag_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align tags within the layout

        # Set up the tag widget
        tag_widget = QWidget()
        tag_widget.setLayout(tag_layout)
        tag_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Allow the widget to expand

        # Style each tag label with centered alignment, shadow, translucent background, and inverted text color
        for category in self.task.categories:
            tag_label = QLabel(f"{category} ")
            tag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align text within the label

            # Add shadow effect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setOffset(2, 2)
            shadow.setColor(QColor(0, 0, 0, 120))  # Light shadow with some transparency
            tag_label.setGraphicsEffect(shadow)

            # Translucent background color with inverted text color
            tag_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(211, 211, 211, 0.8);  /* Light gray with 80% opacity */
                    color: black;  /* Inverted text color for better contrast on light background */
                    border-radius: 10px;
                    padding: 5px 10px;
                }
            """)

            # Add the styled label to the layout
            tag_layout.addWidget(tag_label)

        # Add the tag widget to the main layout with center alignment
        self.details_layout.addWidget(tag_widget, alignment=Qt.AlignmentFlag.AlignCenter)

    def update_task_attribute(self, attribute, value):
        self.task.set_attribute(attribute, value)
        self.task_list_widget.task_list.update_task(self.task)
        global_signals.task_list_updated.emit()

    def edit_task_name(self, event):
        # Replace QLabel with QLineEdit for editing
        self.task_name_edit = QLineEdit(self.task_name_label.text())
        self.task_name_edit.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.task_name_edit.setFocus()
        self.task_name_edit.selectAll()

        # Connect both finishing events for saving
        self.task_name_edit.editingFinished.connect(self.finish_editing_task_name)
        self.header_layout.replaceWidget(self.task_name_label, self.task_name_edit)
        self.task_name_label.hide()

    def finish_editing_task_name(self):
        # Update task title with the new text and replace QLineEdit with QLabel
        self.task.title = self.task_name_edit.text()  # Update task with new name
        self.task_name_label.setText(self.task.title)

        # Replace QLineEdit back with QLabel
        self.header_layout.replaceWidget(self.task_name_edit, self.task_name_label)
        self.task_name_edit.deleteLater()  # Clean up QLineEdit
        self.task_name_label.show()
        global_signals.task_list_updated.emit()

    def keyPressEvent(self, event, **kwargs):
        try:
            # Check if Enter was pressed to finish editing
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                focus_widget = self.focusWidget()
                # If the focused widget is a QLineEdit, finish editing
                if isinstance(focus_widget, QLineEdit):
                    focus_widget.clearFocus()
                    event.accept()
                else:
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        except Exception as e:
            print(f"Error in keyPressEvent: {e}")

    def eventFilter(self, source, event):
        # Detect mouse clicks outside the dialog to close it
        if event.type() == QEvent.Type.MouseButtonPress:
            if not self.geometry().contains(event.globalPosition().toPoint()):
                self.close()
                return True
        if event.type() == QEvent.Type.MouseButtonPress:
            try:
                if hasattr(self, 'task_name_edit') and self.task_name_edit.isVisible():
                    # Check if the click is outside the QLineEdit
                    if not self.task_name_edit.geometry().contains(event.pos()):
                        self.finish_editing_task_name()
                        return True  # Event has been handled
            except RuntimeError:
                # Handle case where task_name_edit has been deleted
                pass
        return super().eventFilter(source, event)

    def setup_due_date_display(self):
        # Determine the due date string based on conditions
        due_date_text = ""
        due_date = QDate.fromString(self.task.due_date, "yyyy-MM-dd")
        due_time = QTime.fromString(self.task.due_time, "HH:mm")

        if due_date != QDate(2000, 1, 1):  # Check if due date is set
            today = QDate.currentDate()
            days_to_due = today.daysTo(due_date)

            if days_to_due == 0:
                due_date_text = "today"
            elif 0 < days_to_due <= 6:  # Due within the current week
                due_date_text = due_date.toString("ddd")
            else:
                due_date_text = due_date.toString("dd MMM")
                if due_date.year() != today.year():
                    due_date_text += f" {due_date.year()}"

        if due_time != QTime(0, 0):  # Check if due time is set
            due_date_text += " " + due_time.toString("h:mm AP")

        self.due_date_label.setText(due_date_text)

    def open_due_date_picker(self, event):
        # Create a transparent popup dialog
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)

        # Main vertical layout to hold the calendar, time, and buttons
        layout = QVBoxLayout(dialog)
        dialog.setLayout(layout)

        # Calendar widget for due date
        calendar = QCalendarWidget(dialog)

        # Check if the due date is the default placeholder; if so, set it to today
        default_due_date = "2000-01-01"
        current_due_date = QDate.fromString(self.task.due_date, "yyyy-MM-dd")
        if current_due_date.toString("yyyy-MM-dd") != default_due_date:
            # Otherwise, use the existing due date
            calendar.setSelectedDate(current_due_date)

        # Connect the calendar selection to update the due date
        calendar.selectionChanged.connect(lambda: self.update_due_date_from_calendar(calendar))
        layout.addWidget(calendar)

        # Time Edit widget for due time
        time_edit = QTimeEdit(dialog)
        current_due_time = QTime.fromString(self.task.due_time, "HH:mm")
        time_edit.setTime(current_due_time)
        time_edit.setDisplayFormat("h:mm AP")
        time_edit.timeChanged.connect(lambda: self.update_due_time_from_time_edit(time_edit))
        layout.addWidget(time_edit)

        # Button layout for delete options
        button_layout = QHBoxLayout()

        # Button to clear due date
        clear_date_button = QPushButton("Clear Date", dialog)
        clear_date_button.clicked.connect(lambda: self.clear_due_date(calendar))
        button_layout.addWidget(clear_date_button)

        # Button to clear due time
        clear_time_button = QPushButton("Clear Time", dialog)
        clear_time_button.clicked.connect(lambda: self.clear_due_time(time_edit))
        button_layout.addWidget(clear_time_button)

        layout.addLayout(button_layout)

        # Position the dialog at the center of the due_date_label click
        label_pos = self.due_date_label.mapToGlobal(
            QPoint(self.due_date_label.width() // 2, self.due_date_label.height() // 2))
        dialog.move(label_pos - QPoint(dialog.width() // 2, dialog.height() // 2))
        dialog.exec()

    def update_task_due_date(self, due_date):
        # Update task's due date
        self.task.due_date = due_date
        self.task_list_widget.task_list.update_task(self.task)
        global_signals.task_list_updated.emit()

    def update_task_due_time(self, due_time):
        # Update task's due time
        self.task.due_time = due_time
        self.task_list_widget.task_list.update_task(self.task)
        global_signals.task_list_updated.emit()

    def update_due_date_from_calendar(self, calendar):
        # Use update_task_due_date to set due date based on calendar selection
        selected_date = calendar.selectedDate().toString("yyyy-MM-dd")
        self.update_task_due_date(selected_date)
        self.setup_due_date_display()

    def update_due_time_from_time_edit(self, time_edit):
        # Use update_task_due_time to set due time based on time edit
        selected_time = time_edit.time().toString("HH:mm")
        self.update_task_due_time(selected_time)
        self.setup_due_date_display()

    def clear_due_date(self, calendar):
        # Use update_task_due_date to clear the due date
        self.update_task_due_date("2000-01-01")  # Default/undefined date
        calendar.clearFocus()
        self.setup_due_date_display()

    def clear_due_time(self, time_edit):
        # Use update_task_due_time to clear the due time
        self.update_task_due_time("00:00")  # Default/undefined time
        time_edit.setTime(QTime(0, 0))
        self.setup_due_date_display()

    def toggle_edit_mode(self):
        if self.is_edit_mode:
            # Already in edit mode, do nothing
            return
        else:
            self.is_edit_mode = True
            self.edit_button.hide()
            self.switch_to_edit_mode()

    def add_labeled_widget(self, label_text, widget):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addWidget(widget)
        self.details_layout.addLayout(layout)

    def switch_to_edit_mode(self):
        # Clear existing widgets
        self.clear_layout(self.details_layout)

        # Editable Task Name
        self.task_name_edit = QLineEdit(self.task.title)
        self.header_layout.replaceWidget(self.task_name_label, self.task_name_edit)
        self.task_name_label.hide()

        # Description
        self.description_edit = QTextEdit(self.task.description)
        self.add_labeled_widget("Description:", self.description_edit)

        # Priority
        self.priority_spinbox = QSpinBox()
        self.priority_spinbox.setRange(0, 10)
        self.priority_spinbox.setValue(self.task.priority)
        self.add_labeled_widget("Priority:", self.priority_spinbox)

        # Categories
        self.categories_input = TagInputWidget(
            self.task_list_widget.task_list.get_task_categories(), self.task.categories)
        self.add_labeled_widget("Categories:", self.categories_input)

        # Recurring
        self.recurring_checkbox = QCheckBox("Recurring")
        self.recurring_checkbox.setChecked(self.task.recurring)
        self.details_layout.addWidget(self.recurring_checkbox)

        # Recur Every
        self.recur_every_edit = QLineEdit(", ".join(map(str, self.task.recur_every)))
        self.add_labeled_widget("Recur Every (list of days or numbers):", self.recur_every_edit)

        # Estimate
        self.estimate_spinbox = QDoubleSpinBox()
        self.estimate_spinbox.setRange(0, 10000)
        self.estimate_spinbox.setDecimals(2)
        self.estimate_spinbox.setValue(self.task.estimate)
        self.add_labeled_widget("Estimate (hours):", self.estimate_spinbox)

        # Time Logged
        self.time_logged_spinbox = QDoubleSpinBox()
        self.time_logged_spinbox.setRange(0, 10000)
        self.time_logged_spinbox.setDecimals(2)
        self.time_logged_spinbox.setValue(self.task.time_logged)
        self.add_labeled_widget("Time Logged (hours):", self.time_logged_spinbox)

        # Count Required
        self.count_required_spinbox = QSpinBox()
        self.count_required_spinbox.setRange(0, 1000)
        self.count_required_spinbox.setValue(self.task.count_required)
        self.add_labeled_widget("Count Required:", self.count_required_spinbox)

        # Count Completed (Initialized with current count)
        self.count_completed_spinbox = QSpinBox()
        self.count_completed_spinbox.setRange(0, 1000)
        self.count_completed_spinbox.setValue(self.task.count_completed)
        self.add_labeled_widget("Count Completed:", self.count_completed_spinbox)

        # Notes
        self.notes_edit = QTextEdit(self.task.notes)
        self.add_labeled_widget("Notes:", self.notes_edit)

        # Subtasks (Editable in edit mode)
        self.subtask_editor = SubtaskWindow(self.task, self.task_list_widget.task_list)
        self.details_layout.addWidget(self.subtask_editor)

        # Show Save and Cancel buttons
        self.save_button.show()
        self.cancel_button.show()

    def save_task_edits(self):
        # Validate title
        try:
            title = self.task_name_edit.text().strip()
            if not title:
                QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
                return
            # Update task attributes
            self.task.title = title
        except Exception as e:
            print(e)

        # Update other task attributes
        self.task.description = self.description_edit.toPlainText()
        self.task.priority = self.priority_spinbox.value()
        self.task.categories = self.categories_input.get_tags()
        self.task.recurring = self.recurring_checkbox.isChecked()

        # Recur Every
        recur_every_text = self.recur_every_edit.text().strip()
        if recur_every_text:
            try:
                self.task.recur_every = [int(item) for item in recur_every_text.split(',') if item.strip().isdigit()]
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Recur Every must be a list of integers separated by commas.")
                return
        else:
            self.task.recur_every = []

        self.task.estimate = self.estimate_spinbox.value()
        self.task.time_logged = self.time_logged_spinbox.value()
        self.task.count_required = self.count_required_spinbox.value()
        self.task.count_completed = self.count_completed_spinbox.value()
        self.task.notes = self.notes_edit.toPlainText()

        # Update subtasks
        self.subtask_editor.save_subtasks()

        # Update task and refresh UI
        self.task_list_widget.task_list.update_task(self.task)
        global_signals.task_list_updated.emit()
        self.exit_edit_mode()

    def cancel_edits(self):
        # Exit edit mode without saving changes
        self.exit_edit_mode()

    def exit_edit_mode(self):
        self.is_edit_mode = False
        self.edit_button.show()
        try:
            # Replace QLineEdit with QLabel for task name
            self.header_layout.replaceWidget(self.task_name_edit, self.task_name_label)
            self.task_name_edit.deleteLater()
            self.task_name_label.show()
        except Exception as e:
            print(e)

        # Hide the Save and Cancel buttons
        self.save_button.hide()
        self.cancel_button.hide()

        # Refresh the task details view
        self.display_task_details()

    def increment_time_logged(self):
        """Increment the time logged by one hour."""
        if self.task.time_logged < self.task.estimate:
            self.task.time_logged += 1
            self.task_list_widget.task_list.update_task(self.task)
            self.display_task_details()
            global_signals.task_list_updated.emit()

    def decrement_time_logged(self):
        """Decrement the time logged by one hour, ensuring it doesn't go below zero."""
        if self.task.time_logged > 0:
            self.task.time_logged -= 1
            self.task_list_widget.task_list.update_task(self.task)
            self.display_task_details()
            global_signals.task_list_updated.emit()

    def increment_count(self):
        """Increment the count completed by one."""
        if self.task.count_completed < self.task.count_required:
            self.task.count_completed += 1
            self.task_list_widget.task_list.update_task(self.task)
            self.display_task_details()
            global_signals.task_list_updated.emit()

    def decrement_count(self):
        """Decrement the count completed by one, ensuring it doesn't go below zero."""
        if self.task.count_completed > 0:
            self.task.count_completed -= 1
            self.task_list_widget.task_list.update_task(self.task)
            self.display_task_details()
            global_signals.task_list_updated.emit()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout(item.layout())

    def focusOutEvent(self, event):
        """Close the dialog when it loses focus to a widget outside itself."""
        # Check if the new focus widget is not a descendant of this dialog
        if not self.isAncestorOf(QApplication.focusWidget()):
            self.close()
        super().focusOutEvent(event)
