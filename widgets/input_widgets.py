from .task_widgets import *
import uuid
from datetime import time


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


class PeriodSelectionCalendar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.added_date_time = None
        self.due_date_time = None
        self._state = 0
        self.startLineEdit = QLineEdit("None")
        self.endLineEdit = QLineEdit("None")
        self.startLineEdit.setReadOnly(True)
        self.endLineEdit.setReadOnly(True)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._handleDateClicked)
        timeLayout = QHBoxLayout()
        self.dueTimeEdit = QTimeEdit()
        self.dueTimeEdit.setDisplayFormat("hh:mm AP")
        self.dueTimeEdit.setTime(QTime(0, 0))
        self.clearTimeButton = QPushButton("Clear Time")
        timeLayout.addWidget(self.dueTimeEdit)
        timeLayout.addWidget(self.clearTimeButton)
        self.dueTimeEdit.timeChanged.connect(self._onDueTimeChanged)
        self.clearTimeButton.clicked.connect(self._onClearDueTime)
        self._last_highlight_start = None
        self._last_highlight_end = None
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.startLineEdit)
        topLayout.addWidget(self.endLineEdit)
        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.calendar)
        mainLayout.addLayout(timeLayout)
        self._refreshDisplay()

    def _handleDateClicked(self, date: QDate):
        if self._state == 0:
            self.due_date_time = date;
            self._state = 1
        elif self._state == 1:
            if date == self.due_date_time:
                self.added_date_time = date;
                self._state = 2
            else:
                self.due_date_time = date
        else:
            if date == self.added_date_time:
                self._clearDates();
                return
            else:
                self.due_date_time = date
        self._refreshDisplay()

    def _refreshDisplay(self):
        if self.added_date_time is None:
            self.startLineEdit.setText("None")
        else:
            self.startLineEdit.setText(self.added_date_time.toString("yyyy-MM-dd"))
        if self.due_date_time is None:
            self.endLineEdit.setText("None")
        else:
            self.endLineEdit.setText(self.due_date_time.toString("yyyy-MM-dd"))
        if self.due_date_time is None:
            self.dueTimeEdit.setEnabled(False);
            self.clearTimeButton.setEnabled(False)
        else:
            self.dueTimeEdit.setEnabled(True);
            self.clearTimeButton.setEnabled(True)
            if isinstance(self.due_date_time, QDate):
                self.dueTimeEdit.setTime(QTime(0, 0))
            else:
                self.dueTimeEdit.setTime(self.due_date_time.time())
        if self.added_date_time:
            self.calendar.setMinimumDate(self.added_date_time)
        else:
            self.calendar.setMinimumDate(QDate(1900, 1, 1))
        self._highlightSelection()

    def _highlightSelection(self):
        default_fmt = QTextCharFormat()
        if self._last_highlight_start and self._last_highlight_end:
            cur = self._last_highlight_start
            while cur <= self._last_highlight_end:
                self.calendar.setDateTextFormat(cur, default_fmt)
                cur = cur.addDays(1)
        if not self.due_date_time:
            self._last_highlight_start = None
            self._last_highlight_end = None
            return
        highlight_fmt = QTextCharFormat()
        highlight_fmt.setBackground(QBrush(QColor("lightblue")))

        # Ensure we are working with QDate, extract date if it's QDateTime
        due_date = self.due_date_time.date() if isinstance(self.due_date_time, QDateTime) else self.due_date_time
        added_date = self.added_date_time.date() if isinstance(self.added_date_time,
                                                               QDateTime) else self.added_date_time

        if added_date and due_date:
            start = min(added_date, due_date)
            end = max(added_date, due_date)
            cur = start
            while cur <= end:
                self.calendar.setDateTextFormat(cur, highlight_fmt)
                cur = cur.addDays(1)
            self._last_highlight_start = start
            self._last_highlight_end = end
        elif due_date:
            self.calendar.setDateTextFormat(due_date, highlight_fmt)
            self._last_highlight_start = due_date
            self._last_highlight_end = due_date

    def _clearDates(self):
        self.added_date_time = None;
        self.due_date_time = None;
        self._state = 0
        self.calendar.setMinimumDate(QDate(1900, 1, 1));
        self._refreshDisplay()

    def getSelectedDates(self):
        date_format = "yyyy-MM-dd"
        datetime_format = "yyyy-MM-dd HH:mm"

        added_date_str = self.added_date_time.toString(date_format) if self.added_date_time else None

        if isinstance(self.due_date_time, QDateTime):
            due_date_str = self.due_date_time.toString(datetime_format)
        elif isinstance(self.due_date_time, QDate):
            due_date_str = QDateTime(self.due_date_time, self.dueTimeEdit.time()).toString(datetime_format)
        else:
            due_date_str = None

        return added_date_str, due_date_str

    def getDateStates(self):
        added_state = "none" if self.added_date_time is None else "added"
        due_state = "none" if self.due_date_time is None else "due"
        return {"added_date_time": self.added_date_time, "added_state": added_state,
                "due_date_time": self.due_date_time, "due_state": due_state}

    def _onDueTimeChanged(self, time):
        if isinstance(self.due_date_time, QDate):
            self.due_date_time = QDateTime(self.due_date_time, time)
        elif self.due_date_time is None:
            self.due_date_time = QDateTime(QDate.currentDate(), time)
        else:
            self.due_date_time.setTime(time)

    def _onClearDueTime(self):
        self.dueTimeEdit.setTime(QTime(0, 0))
        if isinstance(self.due_date_time, QDateTime):
            self.due_date_time.setTime(QTime(0, 0))


class OptionSelector(QWidget):
    def __init__(self, name: str, options: list[str], default_value: str = None, fixed_width: int = None):
        super().__init__()

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name + ":")
        main_layout.addWidget(name_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        for option in options:
            btn = QPushButton(option)
            btn.setCheckable(True)
            btn.setFlat(False)
            if fixed_width:
                btn.setFixedWidth(fixed_width)
            self.button_group.addButton(btn)

            if option == default_value:
                btn.setChecked(True)
            button_layout.addWidget(btn)

        container = QWidget()
        container.setLayout(button_layout)
        main_layout.addWidget(container)

        self.setLayout(main_layout)

    def get_selection(self):
        checked_button = self.button_group.checkedButton()
        return checked_button.text() if checked_button else None


class MultiOptionSelector(QWidget):
    def __init__(self, options: list[str], name: str = None, default_value: str = None, fixed_width: int = None):
        super().__init__()

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(0, 0, 0, 0)
        if name:
            name_label = QLabel(name + ":")
            main_layout.addWidget(name_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.buttons = {}

        for option in options:
            btn = QPushButton(option)
            btn.setCheckable(True)
            btn.setFlat(False)
            if fixed_width:
                btn.setFixedWidth(fixed_width)
            self.buttons[option] = btn
            button_layout.addWidget(btn)

        container = QWidget()
        container.setLayout(button_layout)
        main_layout.addWidget(container)

        self.setLayout(main_layout)

        if default_value:
            self.set_selected([default_value])

    def get_selected(self):
        return [opt for opt, btn in self.buttons.items() if btn.isChecked()]

    def set_selected(self, selected_options):
        for opt, btn in self.buttons.items():
            btn.setChecked(opt in selected_options)


class TimeEstimateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setSpacing(0)  # No spacing
        layout.setContentsMargins(0, 0, 0, 0)  # No margins

        self.hours_label = QLabel("Hrs:")
        self.hours_spinbox = QSpinBox()
        self.hours_spinbox.setRange(0, 99)
        self.hours_spinbox.setFixedWidth(75)

        self.minutes_label = QLabel("Min:")
        self.minutes_spinbox = QSpinBox()
        self.minutes_spinbox.setRange(-1, 60)
        self.minutes_spinbox.setFixedWidth(75)

        # Prevents automatic expansion
        for widget in [self.hours_label, self.hours_spinbox, self.minutes_label, self.minutes_spinbox]:
            widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.minutes_spinbox.valueChanged.connect(self.adjust_time)

        layout.addWidget(self.hours_label)
        layout.addWidget(self.hours_spinbox)
        layout.addWidget(self.minutes_label)
        layout.addWidget(self.minutes_spinbox)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)  # Prevents widget from expanding

    def adjust_time(self, value):
        if value == 60 and self.hours_spinbox.value() < 99:
            self.hours_spinbox.setValue(self.hours_spinbox.value() + 1)
            self.minutes_spinbox.setValue(0)
        elif value == -1 and self.hours_spinbox.value() > 0:
            self.hours_spinbox.setValue(self.hours_spinbox.value() - 1)
            self.minutes_spinbox.setValue(59)
        elif value == -1 and self.hours_spinbox.value() == 0:
            self.minutes_spinbox.setValue(0)

    def get_time_estimate(self):
        return self.hours_spinbox.value(), self.minutes_spinbox.value()

    def set_time_estimate(self, hours, minutes):
        self.hours_spinbox.setValue(hours)
        self.minutes_spinbox.setValue(min(59, max(0, minutes)))


# --- FlowLayout definition (for wrapping custom chunks) ---
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=5):
        super().__init__(parent)
        self.itemList = []
        self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing

    def __del__(self):
        while self.count():
            item = self.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self._spacing
            spaceY = self._spacing
            nextX = x + wid.sizeHint().width() + spaceX
            if nextX > rect.right() and lineHeight > 0:
                # Wrap to next line
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + wid.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), wid.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, wid.sizeHint().height())

        return y + lineHeight - rect.y()


class ChunkingSelectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout (Vertical)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(2)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        ### Time Assignment Layout ###
        self.time_assignment_layout = QHBoxLayout()
        self.time_assignment_layout.setSpacing(3)
        self.time_assignment_layout.setContentsMargins(0, 0, 0, 0)
        self.time_assignment_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.te_label = QLabel("Time Estimate:")
        self.te_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.te_label.setMaximumWidth(self.te_label.sizeHint().width())

        self.time_estimate_selector = TimeEstimateWidget(self)
        self.time_estimate_selector.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Default to 15 min
        self.time_estimate_selector.set_time_estimate(0, 15)

        # Connect changes
        self.time_estimate_selector.hours_spinbox.valueChanged.connect(self._onTimeEstimateChanged)
        self.time_estimate_selector.minutes_spinbox.valueChanged.connect(self._onTimeEstimateChanged)

        # Quick Time Selection Buttons
        quick_time_select_layout = QHBoxLayout()
        quick_time_select_layout.setSpacing(2)
        quick_time_select_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_time_select = QButtonGroup(self)
        self.quick_time_select.setExclusive(True)
        self.quick_times_map = {
            "15 min": (0, 15),
            "30 min": (0, 30),
            "1 hr": (1, 0),
            "2 hr": (2, 0),
            "3 hr": (3, 0),
        }
        for option, (hrs, mins) in self.quick_times_map.items():
            btn = QPushButton(option)
            btn.setCheckable(True)
            btn.setFixedWidth(60)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.quick_time_select.addButton(btn)
            quick_time_select_layout.addWidget(btn)
            btn.toggled.connect(lambda checked, o=option: self._handleQuickTimeSelection(o, checked))

        quick_time_container = QWidget()
        quick_time_container.setLayout(quick_time_select_layout)
        quick_time_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        quick_time_container.setMaximumWidth(len(self.quick_times_map) * 60)

        # Count Selection
        count_layout = QHBoxLayout()
        count_layout.setSpacing(8)
        count_layout.setContentsMargins(0, 0, 0, 0)
        self.count_lb = QLabel("Count:")
        self.count_lb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.count_selector = QSpinBox(self)
        self.count_selector.setRange(0, 999999)
        self.count_selector.setFixedWidth(75)
        self.count_selector.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.count_selector.valueChanged.connect(self._updateChunkSpinboxes)
        count_layout.addWidget(self.count_lb)
        count_layout.addWidget(self.count_selector)

        # Assemble Time Assignment Layout
        self.time_assignment_layout.addWidget(self.te_label)
        self.time_assignment_layout.addWidget(self.time_estimate_selector)
        self.time_assignment_layout.addSpacing(5)
        self.time_assignment_layout.addWidget(quick_time_container)
        self.time_assignment_layout.addSpacing(8)
        self.time_assignment_layout.addLayout(count_layout)
        self.main_layout.addLayout(self.time_assignment_layout)

        ### Chunking Style (Auto / Assigned / Single) ###
        self.chunking_style_layout = QHBoxLayout()
        self.chunking_style_layout.setSpacing(2)
        self.chunking_style_layout.setContentsMargins(0, 0, 0, 0)
        self.chunking_style_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.chunking_style_group = QButtonGroup(self)
        self.chunking_buttons_container = QWidget()
        self.chunking_buttons_layout = QHBoxLayout(self.chunking_buttons_container)
        self.chunking_buttons_layout.setSpacing(2)
        self.chunking_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.auto_chunk_btn = QPushButton("Auto")
        self.assigned_chunk_btn = QPushButton("Assigned")
        self.single_chunk_btn = QPushButton("Single")

        for btn in [self.auto_chunk_btn, self.assigned_chunk_btn, self.single_chunk_btn]:
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.chunking_style_group.addButton(btn)
            self.chunking_buttons_layout.addWidget(btn)

        self.chunking_style_layout.addWidget(self.chunking_buttons_container)
        self.main_layout.addLayout(self.chunking_style_layout)

        ### Chunking Method (Time / Count) ###
        self.chunking_method_layout = QHBoxLayout()
        self.chunking_method_layout.setSpacing(2)
        self.chunking_method_layout.setContentsMargins(0, 0, 0, 0)
        self.chunking_method_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.chunking_method_group = QButtonGroup(self)
        self.chunking_method_container = QWidget()
        self.chunking_method_buttons_layout = QHBoxLayout(self.chunking_method_container)
        self.chunking_method_buttons_layout.setSpacing(2)
        self.chunking_method_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.time_chunk_btn = QPushButton("Time")
        self.count_chunk_btn = QPushButton("Count")

        for btn in [self.time_chunk_btn, self.count_chunk_btn]:
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.chunking_method_group.addButton(btn)
            self.chunking_method_buttons_layout.addWidget(btn)

        self.chunking_method_layout.addWidget(self.chunking_method_container)
        self.main_layout.addLayout(self.chunking_method_layout)

        ### Chunking Configuration for "Auto" ###
        self.chunking_config_layout = QHBoxLayout()
        self.chunking_config_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.chunking_config_layout.setSpacing(5)
        self.chunking_config_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.chunking_config_layout)

        self.min_label = QLabel("Min Time:")
        self.min_spinbox = QSpinBox()
        self.min_spinbox.setRange(1, 999999)
        self.min_spinbox.setFixedWidth(75)
        self.min_spinbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.max_label = QLabel("Max Time:")
        self.max_spinbox = QSpinBox()
        self.max_spinbox.setRange(1, 999999)
        self.max_spinbox.setFixedWidth(75)
        self.max_spinbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.chunking_config_layout.addWidget(self.min_label)
        self.chunking_config_layout.addWidget(self.min_spinbox)
        self.chunking_config_layout.addWidget(self.max_label)
        self.chunking_config_layout.addWidget(self.max_spinbox)

        ### Assigned Chunks UI (Visible only if 'Assigned') ###
        self.assigned_widget = QWidget()
        assigned_v = QVBoxLayout(self.assigned_widget)
        assigned_v.setContentsMargins(0, 0, 0, 0)
        assigned_v.setSpacing(5)

        # Sub-mode radio buttons
        self.split_evenly_btn = QRadioButton("Split Evenly")
        self.custom_assigned_btn = QRadioButton("Custom")
        self.split_evenly_btn.setChecked(True)
        self.mode_layout = QHBoxLayout()
        self.mode_layout.addWidget(self.split_evenly_btn)
        self.mode_layout.addWidget(self.custom_assigned_btn)
        assigned_v.addLayout(self.mode_layout)

        # Split Evenly container
        self.assigned_evenly_container = QWidget()
        self.assigned_evenly_layout = QHBoxLayout(self.assigned_evenly_container)
        self.assigned_evenly_layout.setSpacing(5)

        self.split_evenly_label = QLabel("Number of Chunks:")
        self.split_evenly_spinbox = QSpinBox()
        self.split_evenly_spinbox.setRange(1, 9999)
        self.split_evenly_spinbox.setValue(2)

        self.evenly_preview_label = QLabel("")
        self.assigned_evenly_layout.addWidget(self.split_evenly_label)
        self.assigned_evenly_layout.addWidget(self.split_evenly_spinbox)
        self.assigned_evenly_layout.addWidget(self.evenly_preview_label)
        self.assigned_evenly_container.setLayout(self.assigned_evenly_layout)

        assigned_v.addWidget(self.assigned_evenly_container)

        # Custom container
        self.assigned_custom_container = QWidget()
        self.assigned_custom_layout = QVBoxLayout(self.assigned_custom_container)
        self.assigned_custom_layout.setSpacing(3)
        self.assigned_custom_layout.setContentsMargins(0, 0, 0, 0)

        self.custom_controls_layout = QHBoxLayout()
        self.btn_add_chunk = QPushButton("Add Chunk")
        self.btn_add_chunk.clicked.connect(self._onAddCustomChunk)
        self.custom_controls_layout.addWidget(self.btn_add_chunk)
        self.assigned_custom_layout.addLayout(self.custom_controls_layout)

        # A scrollable area containing the FlowLayout
        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)

        self.custom_chunks_flow = FlowLayout(spacing=8)
        # We'll put the flow in a container:
        self.custom_chunks_container = QWidget()
        self.custom_chunks_container.setLayout(self.custom_chunks_flow)
        self.scroll_area.setWidget(self.custom_chunks_container)

        self.assigned_custom_layout.addWidget(self.scroll_area)
        self.assigned_custom_container.setLayout(self.assigned_custom_layout)
        assigned_v.addWidget(self.assigned_custom_container)

        self.main_layout.addWidget(self.assigned_widget)

        # Ensure assigned-widget is hidden on startup
        self.assigned_widget.setVisible(False)

        # Initialize floating chunk for custom mode
        self._floating_chunk_widget = None
        self._createFloatingChunk()

        # --- Connect signals ---
        self.split_evenly_spinbox.valueChanged.connect(self._updateEvenlyPreview)
        self.split_evenly_btn.toggled.connect(self._updateAssignedVisibility)
        self.custom_assigned_btn.toggled.connect(self._updateAssignedVisibility)

        self.auto_chunk_btn.toggled.connect(self.update_chunking_config)
        self.assigned_chunk_btn.toggled.connect(self.update_chunking_config)
        self.single_chunk_btn.toggled.connect(self.update_chunking_config)

        self.time_chunk_btn.toggled.connect(self.update_chunking_method)
        self.count_chunk_btn.toggled.connect(self.update_chunking_method)

        # For "Auto" min/max spinboxes, as well as showing/hiding logic:
        self.time_chunk_btn.toggled.connect(self._updateChunkSpinboxes)
        self.count_chunk_btn.toggled.connect(self._updateChunkSpinboxes)
        self.auto_chunk_btn.toggled.connect(self._updateChunkSpinboxes)
        self.assigned_chunk_btn.toggled.connect(self._updateChunkSpinboxes)
        self.single_chunk_btn.toggled.connect(self._updateChunkSpinboxes)

        # Default selections
        self.auto_chunk_btn.setChecked(True)
        self.time_chunk_btn.setChecked(True)
        self.update_chunking_method()
        self.update_chunking_config()
        self._updateChunkSpinboxes()
        self._updateAssignedVisibility()

        # Show the "Evenly" preview label right away if it's the default
        self._updateEvenlyPreview()

        # Hide the custom container if the default is "Split Evenly"
        self.assigned_custom_container.setVisible(False)

    # ----------------- Public API ----------------- #
    def get_chunking_style(self):
        if self.auto_chunk_btn.isChecked():
            return "auto"
        elif self.assigned_chunk_btn.isChecked():
            return "assigned"
        else:
            return "single"

    def get_chunking_method(self):
        return "time" if self.time_chunk_btn.isChecked() else "count"

    def get_chunk_sizes(self):
        if self.get_chunking_style() == "auto":
            return (self.min_spinbox.value(), self.max_spinbox.value())
        return (0, 0)

    def get_assigned_chunks(self):
        if self.get_chunking_style() != "assigned":
            return []
        if self.split_evenly_btn.isChecked():
            n = self.split_evenly_spinbox.value()
            total = self._getTotalEstimate()
            if total <= 0 or n <= 0:
                return []
            chunk_size = total // n
            leftover = total % n
            chunks = []
            for i in range(n):
                c = chunk_size + (1 if i < leftover else 0)
                chunks.append(c)
            return chunks
        else:
            results = []
            count_items = self.custom_chunks_flow.count()
            for i in range(count_items):
                item = self.custom_chunks_flow.itemAt(i)
                w = item.widget()
                if w and w.property("chunk_data"):
                    data = w.property("chunk_data")
                    chunk_type = data["type"]
                    val = self._getChunkValue(chunk_type, data["widget"])
                    if val > 0:
                        results.append(val)
            return results

    # ----------------- Internal Updates ----------------- #
    def update_chunking_config(self):
        is_auto = self.auto_chunk_btn.isChecked()
        is_assigned = self.assigned_chunk_btn.isChecked()
        self.min_label.setVisible(is_auto)
        self.min_spinbox.setVisible(is_auto)
        self.max_label.setVisible(is_auto)
        self.max_spinbox.setVisible(is_auto)
        self.assigned_widget.setVisible(is_assigned)

    def update_chunking_method(self):
        """ Update labels and ensure all assigned chunks update their units properly. """
        is_time_mode = self.time_chunk_btn.isChecked()

        self.min_label.setText("Min Time:" if is_time_mode else "Min Count:")
        self.max_label.setText("Max Time:" if is_time_mode else "Max Count:")

        # Update chunking method for assigned mode
        if self.assigned_chunk_btn.isChecked():
            if self.split_evenly_btn.isChecked():
                self._updateSplitEvenlyForModeChange()
            else:
                self._updateAssignedChunksForModeChange()

    def _updateAssignedChunksForModeChange(self):
        """Ensures all assigned chunks update their units properly when switching between Time and Count."""
        total_estimate = self._getTotalEstimate()
        is_time_mode = self.time_chunk_btn.isChecked()

        # Update all custom chunks (spinboxes)
        for item in self.custom_chunks_flow.itemList:
            widget = item.widget()
            if widget and widget.property("chunk_data"):
                data = widget.property("chunk_data")
                spinbox = data["widget"]

                # Convert old value to new unit
                old_value = spinbox.value()
                if is_time_mode:
                    new_value = min(old_value * 60, total_estimate)  # Convert count to minutes
                else:
                    new_value = min(old_value // 60, total_estimate)  # Convert minutes to count

                spinbox.setValue(new_value)
                spinbox.setRange(1, total_estimate)

        # Update floating chunk
        self._adjustFloatingChunkSize()

    def _updateSplitEvenlyForModeChange(self):
        """
        Ensures the 'Split Evenly' preview and spinbox update properly
        when switching between Time and Count.
        NOTE: We do NOT disable the count_selector or min/max spinboxes here.
        """
        total_estimate = self._getTotalEstimate()
        if total_estimate <= 0:
            return

        # Adjust the maximum possible chunks if needed (e.g., if total is 10, you can have at most 10 chunks).
        self.split_evenly_spinbox.setMaximum(max(1, total_estimate))

        # If the user had a higher chunk number set previously, clamp it
        old_n_chunks = self.split_evenly_spinbox.value()
        new_n_chunks = min(old_n_chunks, total_estimate)
        self.split_evenly_spinbox.setValue(new_n_chunks)

        # Update preview label
        self._updateEvenlyPreview()

    def _updateChunkSpinboxes(self):
        """
        Called whenever the user changes the 'auto/assigned/single' style
        or toggles time/count while in Auto mode.
        Dynamically update min/max spinboxes for 'Auto' style.
        We do NOT disable the count spinbox in count mode.
        """
        if self.get_chunking_style() != "auto":
            return

        total = self._getTotalEstimate()
        is_time_mode = self.time_chunk_btn.isChecked()

        if total <= 0:
            # Fallback
            self.min_spinbox.setValue(1)
            self.max_spinbox.setValue(1)
            return

        if is_time_mode:
            # Time-based chunking (min/max in minutes)
            min_val = 15 if total <= 30 else 30
            max_val = max(total, min_val)
        else:
            # Count-based chunking
            # e.g., 20% to 100% of count
            min_val = max(1, int(total * 0.2))
            max_val = max(total, min_val)

        self.min_spinbox.setValue(min_val)
        self.max_spinbox.setValue(max_val)

        # If "Split Evenly" is active in assigned mode, we update that logic too
        if self.split_evenly_btn.isChecked() and self.assigned_chunk_btn.isChecked():
            self._updateSplitEvenlyForModeChange()

    def _updateAssignedVisibility(self):
        """
        Show or hide the assigned widget and sub-mode containers.
        Also ensure the floating chunk is created if "Custom" is chosen.
        """
        if not self.assigned_chunk_btn.isChecked():
            self.assigned_widget.setVisible(False)
            return

        self.assigned_widget.setVisible(True)

        use_split_evenly = self.split_evenly_btn.isChecked()
        self.assigned_evenly_container.setVisible(use_split_evenly)
        self.assigned_custom_container.setVisible(not use_split_evenly)

        # If switching to custom, ensure the floating chunk is there
        if self.custom_assigned_btn.isChecked():
            self._createFloatingChunk()
            self._adjustFloatingChunkSize()

        self._updateEvenlyPreview()

    def _updateEvenlyPreview(self):
        """
        Show how large each chunk will be if 'Split Evenly' is chosen,
        including on startup (so it doesn't start empty).
        """
        if not self.assigned_chunk_btn.isChecked() or not self.split_evenly_btn.isChecked():
            self.evenly_preview_label.setText("")
            return

        n = self.split_evenly_spinbox.value()
        total = self._getTotalEstimate()
        is_time_mode = self.time_chunk_btn.isChecked()

        if n <= 0 or total <= 0:
            self.evenly_preview_label.setText("(No valid chunks)")
            return

        chunk_size = total // n
        leftover = total % n

        # For display, if time mode => 'min', else 'count'
        unit = "min" if is_time_mode else "count"
        self.evenly_preview_label.setText(f"Each ≈ {chunk_size} {unit} (+ leftover={leftover})")

    # ------------------ Custom Approach ------------------ #
    def _createFloatingChunk(self):
        """Create the floating chunk with the correct total estimate."""
        total = self._getTotalEstimate()
        if self._floating_chunk_widget:
            self._floating_chunk_widget.setRange(0, total)
            self._floating_chunk_widget.setValue(total)
            return

        chunk_type = "time" if self.get_chunking_method() == "time" else "count"

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        spin = QSpinBox(self)
        spin.setRange(0, total)
        spin.setValue(total)
        spin.setFixedWidth(80)

        container_layout.addWidget(spin)
        container.setProperty("chunk_data", {"type": chunk_type, "widget": spin, "floating": True})

        self._floating_chunk_widget = spin
        self.custom_chunks_flow.addWidget(container)

    def _onAddCustomChunk(self):
        """Adds a new chunk, ensuring the sum of all chunks always equals the total estimate."""
        leftover = self._getLeftover()
        if leftover <= 0:
            return  # Don't allow adding if no space left

        chunk_type = "time" if self.get_chunking_method() == "time" else "count"

        new_chunk_value = max(1, leftover // 2)  # Default to splitting remaining space
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        spin = QSpinBox(self)
        spin.setRange(1, leftover)  # Max cannot exceed leftover
        spin.setValue(new_chunk_value)
        spin.setFixedWidth(80)
        spin.valueChanged.connect(lambda: self._onCustomChunkChanged(spin))

        container_layout.addWidget(spin)

        remove_btn = QPushButton("x")
        remove_btn.setFixedWidth(20)
        remove_btn.setFixedHeight(25)
        remove_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        remove_btn.clicked.connect(lambda: self._removeCustomChunk(container))
        container_layout.addWidget(remove_btn)

        container.setProperty("chunk_data", {"type": chunk_type, "widget": spin, "floating": False})
        self.custom_chunks_flow.addWidget(container)

        # Ensure floating chunk updates correctly
        self._reorderFloatingChunkLast()
        self._adjustFloatingChunkSize()

    def _onCustomChunkChanged(self, changed_spinbox):
        """Ensures the total sum of chunks remains equal to the total estimate when a user changes a value."""
        total_estimate = self._getTotalEstimate()
        if total_estimate <= 0:
            return

        used_amount = sum(self._getChunkValue(data["type"], data["widget"])
                          for item in self.custom_chunks_flow.itemList
                          if (data := item.widget().property("chunk_data")) and not data["floating"])

        floating_w = self._floating_chunk_widget

        leftover = total_estimate - used_amount
        if floating_w:
            floating_w.setValue(max(0, leftover))
            floating_w.setRange(0, leftover)

        # Adjust max range for all spinboxes to prevent exceeding total
        for item in self.custom_chunks_flow.itemList:
            widget = item.widget()
            if widget and widget.property("chunk_data"):
                data = widget.property("chunk_data")
                spinbox = data["widget"]
                if not data["floating"]:
                    current_val = spinbox.value()
                    spinbox.setRange(1, current_val + leftover)  # Adjust limit to prevent over-allocation

    def _removeCustomChunk(self, container):
        self.custom_chunks_flow.removeWidget(container)
        container.setParent(None)
        container.deleteLater()
        self._adjustFloatingChunkSize()

    def _reorderFloatingChunkLast(self):
        if not self._floating_chunk_widget:
            return
        floating_container = None
        for i in range(self.custom_chunks_flow.count()):
            item = self.custom_chunks_flow.itemAt(i)
            w = item.widget()
            if w and w.property("chunk_data") and w.property("chunk_data")["floating"]:
                floating_container = w
                break
        if floating_container:
            self.custom_chunks_flow.removeWidget(floating_container)
            self.custom_chunks_flow.addWidget(floating_container)

    def _adjustFloatingChunkSize(self):
        """Ensures the sum of all chunks always equals the total estimate by dynamically adjusting the floating chunk."""
        total_estimate = self._getTotalEstimate()
        if total_estimate <= 0:
            return

        used_amount = sum(self._getChunkValue(data["type"], data["widget"])
                          for item in self.custom_chunks_flow.itemList
                          if (data := item.widget().property("chunk_data")) and not data["floating"])

        floating_w = self._floating_chunk_widget
        leftover = total_estimate - used_amount

        if floating_w:
            floating_w.setRange(0, leftover)
            floating_w.setValue(max(0, leftover))

        # If there's no leftover, remove floating chunk
        if leftover <= 0 and floating_w:
            container = floating_w.parent()
            self.custom_chunks_flow.removeWidget(container)
            container.setParent(None)
            container.deleteLater()
            self._floating_chunk_widget = None

    def _clearRemoveButton(self, container):
        layout = container.layout()
        if not layout:
            return
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            w = item.widget()
            if isinstance(w, QPushButton) and w.text() == "X":
                layout.removeWidget(w)
                w.setParent(None)
                w.deleteLater()

    def _getLeftover(self):
        """Return how much leftover is currently in the floating chunk."""
        total_estimate = self._getTotalEstimate()
        used_amount = 0
        floating_val = 0
        for i in range(self.custom_chunks_flow.count()):
            item = self.custom_chunks_flow.itemAt(i)
            w = item.widget()
            if not w or not w.property("chunk_data"):
                continue
            data = w.property("chunk_data")
            if data["floating"]:
                floating_val = self._getChunkValue(data["type"], data["widget"])
            else:
                used_amount += self._getChunkValue(data["type"], data["widget"])
        # leftover = total - used_amount is actually stored in floating
        # so we can just sum leftover + used
        return total_estimate - used_amount

    # --------------- Helpers --------------- #
    def _getTotalEstimate(self):
        if self.get_chunking_method() == "time":
            h, m = self.time_estimate_selector.get_time_estimate()
            return h * 60 + m
        else:
            return self.count_selector.value()

    def _getChunkValue(self, chunk_type, widget):
        return widget.value()

    # --------------- Spinbox changes --------------- #
    def _onTimeEstimateChanged(self, _value):
        self._uncheckQuickTimeButtons()
        self._updateChunkSpinboxes()
        self._updateEvenlyPreview()
        self._adjustFloatingChunkSize()

    def _uncheckQuickTimeButtons(self):
        for btn in self.quick_time_select.buttons():
            if btn.isChecked():
                btn.setChecked(False)

    def _handleQuickTimeSelection(self, option, checked):
        if checked:
            hrs, mins = self.quick_times_map[option]
            self.time_estimate_selector.set_time_estimate(hrs, mins)

    def get_selections(self):
        """
        Returns a dictionary with all selected values:
        - time estimate (total minutes)
        - count
        - chunk type (time or count)
        - auto chunking enabled
        - min chunk size
        - max chunk size
        - assigned chunking enabled
        - assigned chunks list
        - single chunking enabled
        """
        hours, minutes = self.time_estimate_selector.get_time_estimate()
        time_estimate = (hours * 60) + minutes  # Convert to total minutes

        count = self.count_selector.value()
        chunk_type = "time" if self.time_chunk_btn.isChecked() else "count"

        auto_chunk = self.auto_chunk_btn.isChecked()
        min_chunk_size = self.min_spinbox.value() if auto_chunk else None
        max_chunk_size = self.max_spinbox.value() if auto_chunk else None

        assigned = self.assigned_chunk_btn.isChecked()
        assigned_chunks = self.get_assigned_chunks() if assigned else []

        single_chunk = self.single_chunk_btn.isChecked()

        return {
            "time_estimate": time_estimate,
            "count": count,
            "chunk_type": chunk_type,
            "auto_chunk": auto_chunk,
            "min_chunk_size": min_chunk_size,
            "max_chunk_size": max_chunk_size,
            "assigned": assigned,
            "assigned_chunks": assigned_chunks,
            "single_chunk": single_chunk
        }


class AddTaskDialog(QDialog):
    def __init__(self, parent=None, task_list_widget=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Task")
        self.resize(500, 400)

        self.task_list_widget = task_list_widget

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Main Basic
        self.basic = QWidget()
        self.basic_layout = QHBoxLayout(self.basic)
        self.basic.setLayout(self.basic_layout)

        # Left side widgets and layout
        self.left_widgets = QWidget()
        self.left_part = QVBoxLayout(self.left_widgets)

        # Basic Fields on left side
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Enter task name")
        self.name_layout = QHBoxLayout()
        self.name_layout.addWidget(QLabel("Name*:"))
        self.name_layout.addWidget(self.name_edit)
        self.include_in_schedule_checkbox = QCheckBox()
        self.name_layout.addWidget(self.include_in_schedule_checkbox)
        self.left_part.addLayout(self.name_layout)

        self.description_edit = QTextEdit(self)
        self.description_edit.setFixedHeight(70)
        self.description_edit.setPlaceholderText("Enter task description")
        self.left_part.addWidget(self.description_edit)

        self.priority_selector = OptionSelector("Priority", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                                                default_value="5", fixed_width=30)
        self.left_part.addWidget(self.priority_selector)

        self.flexibility_selector = OptionSelector("Flexibility", ["Strict", "Flexible", "Very Flexible"],
                                                   default_value="Flexible")
        self.left_part.addWidget(self.flexibility_selector)

        self.effort_level_selector = OptionSelector("Effort Lvl", ["Low", "Medium", "High"], default_value="Medium")
        self.left_part.addWidget(self.effort_level_selector)

        tags = []
        # if a TaskListDock
        if parent.type == "dock":
            tags = parent.task_list_widget.task_list.get_task_tags()
        elif parent.type == "stack":  # if TaskListStacked
            tags = parent.get_current_task_list_widget().task_list.get_task_tags()
        self.tag_selector = TagInputWidget(tags)
        self.left_part.addWidget(self.tag_selector)

        # (Add other left-side widgets like priority, category, important_checkbox if needed)
        self.recurring_checkbox = QCheckBox("Recurring", self)
        self.left_part.addWidget(self.recurring_checkbox)

        # Recurrence Options
        self.recurrence_options_widget = QWidget()
        self.recurrence_layout = QVBoxLayout(self.recurrence_options_widget)

        self.recur_type_group = QButtonGroup(self)

        self.every_n_days_radio = QRadioButton("Every N days")
        self.specific_weekdays_radio = QRadioButton("Specific weekdays")
        self.recur_type_group.addButton(self.every_n_days_radio)
        self.recur_type_group.addButton(self.specific_weekdays_radio)

        # Horizontal layout for recurrence type selection
        self.recur_type_layout = QHBoxLayout()
        self.recur_type_layout.addWidget(self.every_n_days_radio)
        self.recur_type_layout.addWidget(self.specific_weekdays_radio)

        self.recurrence_layout.addLayout(self.recur_type_layout)

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
        self.specific_weekdays_widget = MultiOptionSelector(
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            fixed_width=47)

        self.recurrence_layout.addWidget(self.every_n_days_widget)
        self.recurrence_layout.addWidget(self.specific_weekdays_widget)

        # Initially hide recurrence detail widgets
        self.every_n_days_widget.hide()
        self.specific_weekdays_widget.hide()
        self.recurrence_options_widget.hide()

        self.left_part.addWidget(self.recurrence_options_widget)

        # Right side: Period Selector only
        self.right_widgets = QWidget()
        self.right_part = QVBoxLayout(self.right_widgets)
        self.period_selector = PeriodSelectionCalendar(self)
        self.right_part.addWidget(self.period_selector)

        self.preferred_day_of_week_selector = MultiOptionSelector(
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "Preferred Days",
            fixed_width=43)
        self.right_part.addWidget(self.preferred_day_of_week_selector)

        self.preferred_time_of_day = MultiOptionSelector(
            ["Morning", "Afternoon", "Evening", "Night"], "Preferred Time", )
        self.right_part.addWidget(self.preferred_time_of_day)

        # Add left and right widgets to the basic layout
        self.basic_layout.addWidget(self.left_widgets)
        self.basic_layout.addWidget(self.right_widgets)

        self.main_layout.addWidget(self.basic)

        # Chunking style selection layout (Horizontal)
        self.time_count_chunk_selector = ChunkingSelectionWidget(self)
        self.main_layout.addWidget(self.time_count_chunk_selector)

        # Connect signals
        self.recurring_checkbox.stateChanged.connect(self.toggle_recurrence_options)
        self.every_n_days_radio.toggled.connect(self.update_recurrence_detail_widgets)
        self.specific_weekdays_radio.toggled.connect(self.update_recurrence_detail_widgets)

        # Dialog Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

        self.name_edit.setFocus()

        # Object Names (for styling or testing)
        self.setObjectName("addTaskDialog")

    def focusOutEvent(self, event):
        print("lost focus")
        self.close()

    def keyPressEvent(self, event, **kwargs):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.tag_selector.input_field.lineEdit().hasFocus():
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
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Title cannot be empty.")
            return
        super().accept()

    def get_task_data(self):

        time_count_chunks = self.time_count_chunk_selector.get_selections()
        start_date, due_date_time = self.period_selector.getSelectedDates()

        task_data = {
            "include_in_schedule": self.include_in_schedule_checkbox.isChecked(),
            "name": self.name_edit.text(),
            "list_name": self.task_list_widget.task_list_name,
            "description": self.description_edit.toPlainText(),
            "priority": int(self.priority_selector.get_selection()),
            "flexibility":  self.flexibility_selector.get_selection(),
            "effort_level": self.effort_level_selector.get_selection(),
            "tags": self.tag_selector.get_tags(),
            "recurring": self.recurring_checkbox.isChecked(),
            "recur_every": int(
                self.every_n_days_spinbox.value()) if self.every_n_days_radio.isChecked() else self.specific_weekdays_widget.get_selected() if self.specific_weekdays_radio.isChecked() else None,
            "start_date": start_date,
            "due_datetime": due_date_time,
            "preferred_work_days": self.preferred_day_of_week_selector.get_selected(),
            "time_of_day_preference": self.preferred_time_of_day.get_selected(),
            "time_estimate": time_count_chunks.get("time_estimate"),
            "count_required": time_count_chunks.get("count"),
            "chunk_type": time_count_chunks.get("chunk_type"),
            "auto_chunk": time_count_chunks.get("auto_chunk"),
            "min_chunk_size": time_count_chunks.get("min_chunk_size"),
            "max_chunk_size": time_count_chunks.get("max_chunk_size"),
            "assigned": time_count_chunks.get("assigned"),
            "assigned_chunks": time_count_chunks.get("assigned_chunks"),
            "single_chunk": time_count_chunks.get("single_chunk")
        }

        return task_data


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

    def set_schedule(self, from_time: time, to_time: time):
        """
        Update the draggable block to use the given from_time and to_time.
        """
        # Compute datetime objects based on the base date from day_start_time
        base_date = self.day_start_time.date()
        dt_from = datetime.combine(base_date, from_time)
        dt_to = datetime.combine(base_date, to_time)
        if dt_to <= dt_from:
            dt_to += timedelta(days=1)  # allow over-midnight ranges

        # Update attributes
        self.from_time = from_time
        self.duration_hours = (dt_to - dt_from).total_seconds() / 3600.0
        self.duration_minutes = self.duration_hours * 60

        # Calculate block_start_time relative to day_start_time (in minutes)
        self.block_start_time = max(0, (dt_from - self.day_start_time).total_seconds() / 60)

        # Reposition and resize the draggable block
        self.draggable_block.move(self.draggable_block.x(), int(self.block_start_time * self.pixels_per_minute))
        self.draggable_block.setFixedHeight(int(self.duration_minutes * self.pixels_per_minute))

        # Update the time edits (blocking signals to avoid loops)
        self.from_time_edit.blockSignals(True)
        self.to_time_edit.blockSignals(True)
        self.from_time_edit.setTime(QTime(from_time.hour, from_time.minute))
        self.to_time_edit.setTime(QTime(to_time.hour, to_time.minute))
        self.from_time_edit.blockSignals(False)
        self.to_time_edit.blockSignals(False)


class SchedulePicker(QWidget):
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

    def set_day_schedule(self, day: str, from_time: time, to_time: time):
        """
        For a given day (e.g., "monday" in lowercase), update the corresponding draggable block
        with the provided from_time and to_time.
        """
        day = day.capitalize()
        if day in self.day_widgets:
            widgets = self.day_widgets[day]
            widgets["checkbox"].setChecked(True)
            widgets["block_widget"].setDisabled(False)
            widgets["block_widget"].set_schedule(from_time, to_time)


class _ClickableItem(QWidget):
    def __init__(self, text):
        super().__init__()
        self._state = 0

        self.button = QPushButton(text)
        self.button.setCheckable(False)
        self.button.setFixedSize(100, 30)
        self.button.clicked.connect(self._handle_click)

        self.button.setStyleSheet("border: 1px solid black; border-radius: 10px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)
        layout.setContentsMargins(0, 0, 0, 0)

        self._update_style()

    def _handle_click(self):
        self._state = (self._state + 1) % 3
        self._update_style()

    def _update_style(self):
        if self._state == 0:
            self.button.setStyleSheet("border: 1px solid black; border-radius: 10px; background: none;")
        elif self._state == 1:
            self.button.setStyleSheet("border: 1px solid black; border-radius: 10px; background: rgb(105, 170, 110);")
        else:
            self.button.setStyleSheet("border: 1px solid black; border-radius: 10px; background: rgb(204, 97, 65);")

    def get_state(self):
        return self._state

    def text(self):
        return self.button.text()


class CategoryTagPicker(QWidget):
    def __init__(self, categories, tags, parent=None):
        super().__init__(parent)

        self.categories = categories
        self.tags = tags
        self.category_items = []
        self.tag_items = []

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # Left side (Categories)
        cat_layout = QVBoxLayout()
        cat_label = QLabel("Task List Categories:")
        cat_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cat_label.setStyleSheet("font-weight: bold;")
        cat_layout.addWidget(cat_label)

        cat_grid = QGridLayout()
        cat_layout.addLayout(cat_grid)
        self._populate_grid(cat_grid, categories, self.category_items)

        # Left container
        cat_container = QWidget()
        cat_container.setLayout(cat_layout)
        cat_container.setMinimumWidth(200)

        # Center divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setFixedWidth(2)

        # Right side (Tags)
        tag_layout = QVBoxLayout()
        tag_label = QLabel("Task Tags:")
        tag_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tag_label.setStyleSheet("font-weight: bold;")
        tag_layout.addWidget(tag_label)

        tag_grid = QGridLayout()
        tag_layout.addLayout(tag_grid)
        self._populate_grid(tag_grid, tags, self.tag_items)

        # Right container
        tag_container = QWidget()
        tag_container.setLayout(tag_layout)
        tag_container.setMinimumWidth(200)

        main_layout.addWidget(cat_container, 1)
        main_layout.addWidget(divider)
        main_layout.addWidget(tag_container, 1)

    def _populate_grid(self, grid, items, item_list):
        max_columns = 3
        for idx, item in enumerate(items):
            row, col = divmod(idx, max_columns)
            clickable_item = _ClickableItem(item)
            grid.addWidget(clickable_item, row, col)
            item_list.append(clickable_item)

    def get_choices(self):
        def extract_choices(items):
            include, exclude = [], []
            for item in items:
                state = item.get_state()
                if state == 1:
                    include.append(item.text())
                elif state == 2:
                    exclude.append(item.text())
            return include, exclude

        include_categories, exclude_categories = extract_choices(self.category_items)
        include_tags, exclude_tags = extract_choices(self.tag_items)

        return {
            'categories': {'include': include_categories, 'exclude': exclude_categories},
            'tags': {'include': include_tags, 'exclude': exclude_tags}
        }


class AddTimeBlockDialog(QDialog):
    def __init__(self, parent=None, day_start_time=None):
        super().__init__(parent)
        self.setWindowTitle("Add Time Block")
        self.resize(500, 400)

        self.parent = parent
        self.day_start_time = day_start_time

        self.unavailable = False

        self.main_layout = QVBoxLayout(self)

        self.name_color_availability_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Time Block Name...")
        self.name_color_availability_layout.addWidget(self.name_input)
        self.picked_color = tuple(random.randint(0, 255) for _ in range(3))
        self.color_picker_button = QPushButton("Color Picker")
        self.color_picker_button.setStyleSheet(f"background-color: rgb{self.picked_color};")
        self.color_picker_button.clicked.connect(self.pick_color)
        self.name_color_availability_layout.addWidget(self.color_picker_button)
        self.unavailable_button = QPushButton("Unavailable")
        self.unavailable_button.clicked.connect(self.toggle_unavailable)
        self.name_color_availability_layout.addWidget(self.unavailable_button)

        self.main_layout.addLayout(self.name_color_availability_layout)

        self.schedule_picker = SchedulePicker(day_start_time=day_start_time, color=f"rgb{self.picked_color}")
        self.main_layout.addWidget(self.schedule_picker)

        categories = self.parent.schedule_manager.task_manager_instance.get_task_list_categories()
        tags = self.parent.schedule_manager.task_manager_instance.get_all_active_task_tags()
        self.category_tag_picker = CategoryTagPicker(categories, tags)
        self.main_layout.addWidget(self.category_tag_picker)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.picked_color = color.getRgb()[:3]
            self.color_picker_button.setStyleSheet(f"background-color: rgb{self.picked_color};")
            self.schedule_picker.refresh_color(self.picked_color)

    def toggle_unavailable(self):
        self.unavailable = not self.unavailable
        if self.unavailable:
            self.unavailable_button.setStyleSheet("background: rgb(204, 97, 65);")
        else:
            self.unavailable_button.setStyleSheet("background: none;")
        # self.schedule_picker.setDisabled(self.unavailable)
        self.category_tag_picker.setDisabled(self.unavailable)

    def get_time_block_data(self):
        name = self.name_input.text().strip()

        if self.unavailable:
            return {
                'unavailable': True,
                'name': name,
                'schedule': self.schedule_picker.get_schedule(),
                'color': self.picked_color
            }

        choices = self.category_tag_picker.get_choices()

        list_categories = choices['categories']
        task_tags = choices['tags']

        return {
            'unavailable': False,
            'name': name,
            'schedule': self.schedule_picker.get_schedule(),
            'list_categories': list_categories,
            'task_tags': task_tags,
            'color': self.picked_color
        }

    def validate_schedule(self, schedule):
        """
        Validates the schedule to ensure it contains valid time ranges.
        """
        for day, (from_time, to_time) in schedule.items():
            if from_time == to_time:
                return f"Invalid time range on {day.title()}: From {from_time} to {to_time}."
            if from_time > to_time:
                return f"Invalid time range on {day.title()}: From time ({from_time}) is after To time ({to_time})."
        return None

    def validate_and_accept(self):
        data = self.get_time_block_data()

        # Validate name
        if not data['name']:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return

        # Validate schedule
        if not data['schedule']:
            QMessageBox.warning(self, "Validation Error", "A schedule is required.")
            return

        # Validate schedule ranges
        schedule_error = self.validate_schedule(data['schedule'])
        if schedule_error:
            QMessageBox.warning(self, "Validation Error", schedule_error)
            return

        if not self.unavailable:

            # Validate categories or tags
            if not (data['list_categories']['include'] or data['task_tags']['include']):
                QMessageBox.warning(self, "Validation Error", "At least one tag or category is required.")
                return

        # If all validations pass
        self.accept()

    def edit_mode(self, block):
        # Set the name
        self.name_input.setText(block["name"])

        # Handle "unavailable" state
        self.unavailable = bool(block["unavailable"])
        if self.unavailable:
            self.unavailable_button.setStyleSheet("background: rgb(204, 97, 65);")
            self.category_tag_picker.setDisabled(True)
        else:
            self.unavailable_button.setStyleSheet("background: none;")
            self.category_tag_picker.setDisabled(False)

        # Set the color
        self.picked_color = block["color"]  # tuple like (r, g, b)
        self.color_picker_button.setStyleSheet(f"background-color: rgb{self.picked_color};")
        self.schedule_picker.refresh_color(self.picked_color)

        # Populate each day's schedule using the new set_day_schedule() helper.
        # Here we assume block["schedule"] is a dictionary with keys as day names in lowercase
        # and values as a tuple/list of two strings, e.g., ("09:00", "10:00").
        for day, widgets in self.schedule_picker.day_widgets.items():
            day = day.lower()
            if day in block["schedule"]:
                # Parse the stored strings into time objects
                from_str, to_str = block["schedule"][day]
                try:
                    from_time = datetime.strptime(from_str, "%H:%M").time()
                    to_time = datetime.strptime(to_str, "%H:%M").time()
                except Exception as e:
                    print(f"Error parsing time for {day}: {e}")
                    continue
                # Use the new helper to set this day's schedule
                self.schedule_picker.set_day_schedule(day, from_time, to_time)
            else:
                # If no schedule is stored for this day, uncheck and disable the widget.
                widgets["checkbox"].setChecked(False)
                widgets["block_widget"].setDisabled(True)
        if not self.unavailable:
            # Set categories and tags as before...
            for item in self.category_tag_picker.category_items:
                if item.text() in block["list_categories"]["include"]:
                    item._state = 1
                elif item.text() in block["list_categories"]["exclude"]:
                    item._state = 2
                else:
                    item._state = 0
                item._update_style()

            for item in self.category_tag_picker.tag_items:
                if item.text() in block["task_tags"]["include"]:
                    item._state = 1
                elif item.text() in block["task_tags"]["exclude"]:
                    item._state = 2
                else:
                    item._state = 0
                item._update_style()
