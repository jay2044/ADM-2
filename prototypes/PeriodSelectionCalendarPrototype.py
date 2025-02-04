# Custom PeriodSelectionCalendar Widget
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


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
        self.dueTimeEdit.setTime(QTime(12, 0))
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
                self.dueTimeEdit.setTime(QTime(12, 0))
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
                self.calendar.setDateTextFormat(cur, default_fmt);
                cur = cur.addDays(1)
        if not self.due_date_time:
            self._last_highlight_start = None;
            self._last_highlight_end = None;
            return
        highlight_fmt = QTextCharFormat();
        highlight_fmt.setBackground(QBrush(QColor("lightblue")))
        if self.added_date_time and self.due_date_time:
            start = min(self.added_date_time, self.due_date_time)
            end = max(self.added_date_time, self.due_date_time)
            cur = start
            while cur <= end:
                self.calendar.setDateTextFormat(cur, highlight_fmt);
                cur = cur.addDays(1)
            self._last_highlight_start = start;
            self._last_highlight_end = end
        elif self.due_date_time:
            self.calendar.setDateTextFormat(self.due_date_time, highlight_fmt)
            self._last_highlight_start = self.due_date_time;
            self._last_highlight_end = self.due_date_time

    def _clearDates(self):
        self.added_date_time = None;
        self.due_date_time = None;
        self._state = 0
        self.calendar.setMinimumDate(QDate(1900, 1, 1));
        self._refreshDisplay()

    def getSelectedDates(self):
        return self.added_date_time, self.due_date_time

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
        self.dueTimeEdit.setTime(QTime(12, 0))
        if isinstance(self.due_date_time, QDateTime):
            self.due_date_time.setTime(QTime(12, 0))


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    calendarWidget = PeriodSelectionCalendar()
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(calendarWidget)
    window.setCentralWidget(container)
    window.show()
    sys.exit(app.exec())
