from datetime import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import sys


class ProportionalGrid(QWidget):
    def __init__(self, num_rows):
        super().__init__()
        self.num_rows = num_rows
        self.row_proportions = [1] * num_rows  # Default to equal proportions
        self.rows = []  # Store references to rows
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setup_grid()

    def setup_grid(self):
        """Initializes rows with empty QWidget placeholders."""
        for i in range(self.num_rows):
            self._add_row(i)

    def set_proportions(self, proportions):
        """Sets row height proportions."""
        if len(proportions) != self.num_rows:
            raise ValueError("Number of proportions must match the number of rows.")
        self.row_proportions = proportions
        self.update_row_heights()

    def update_row_heights(self):
        """Updates the row stretch based on proportions."""
        for i, proportion in enumerate(self.row_proportions):
            self.layout.setRowStretch(i, proportion)

    def add_widget_to_row(self, row_index, widget):
        """Adds a widget to a specific row."""
        if 0 <= row_index < self.num_rows:
            row_layout = QVBoxLayout(self.rows[row_index])
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(widget)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        else:
            raise IndexError("Row index out of range.")

    def add_row(self, proportion=1):
        """Adds a new row to the grid with an optional proportion."""
        row_index = self.num_rows
        self.num_rows += 1
        self.row_proportions.append(proportion)
        self._add_row(row_index)
        self.update_row_heights()

    def _add_row(self, row_index):
        """Private method to add a single row."""
        widget = QWidget()
        widget.setObjectName(f"Row_{row_index}")
        self.layout.addWidget(widget, row_index, 0)
        self.layout.setRowStretch(row_index, 1)
        self.rows.append(widget)

    def get_row_count(self):
        """Returns the current number of rows."""
        return self.num_rows

    def get_proportions(self):
        """Returns the current row proportions."""
        return self.row_proportions


class ScheduleViewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.time_blocks = [
            ["6:00 AM", "8:00 AM", "Morning Task"],
            ["10:00 AM", "12:00 PM", "Midday Task"],
            ["2:00 PM", "3:00 PM", "Afternoon Task"]
        ]
        self.initUI()

    def initUI(self):
        self.setFixedWidth(300)
        self.mainLayout = QVBoxLayout(self)

        # --- Top Buttons Layout ---
        topLayout = QHBoxLayout()
        self.expandBtn = QPushButton("Expand")
        self.quickTaskBtn = QPushButton("Add Quick Task")
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        topLayout.addWidget(self.expandBtn)
        topLayout.addItem(spacer)
        topLayout.addWidget(self.quickTaskBtn)
        self.mainLayout.addLayout(topLayout)

        # --- View Selector ---
        viewSelectorLayout = QHBoxLayout()
        self.prevBtn = QPushButton("<")
        self.viewLabel = QLabel("Day")
        self.nextBtn = QPushButton(">")
        viewSelectorLayout.addWidget(self.prevBtn)
        viewSelectorLayout.addWidget(self.viewLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        viewSelectorLayout.addWidget(self.nextBtn)
        self.mainLayout.addLayout(viewSelectorLayout)

        # --- Time Scale and Timeblock Area ---
        timeBlockLayout = QHBoxLayout()
        self.timeScale = QVBoxLayout()

        # Start with an empty ProportionalGrid and add rows dynamically later
        self.timeBlocksWidget = ProportionalGrid(0)

        timeBlockLayout.addLayout(self.timeScale)
        timeBlockLayout.addWidget(self.timeBlocksWidget)
        self.mainLayout.addLayout(timeBlockLayout)

        # --- Populate Initial Time Scale ---
        self.populateTimeScale()
        self.loadTimeBlocks()  # This now adds rows to the existing timeBlocksWidget

        self.setLayout(self.mainLayout)

    def populateTimeScale(self):
        """Add time labels to the time scale from 4:00 AM to 4:00 AM next day."""
        self.timeScaleLabels = []
        for hour in range(4, 28):  # 4 AM to 4 AM next day
            if hour % 2 == 0:
                display_hour = hour if hour <= 12 else hour - 12
                am_pm = "AM" if hour < 12 or hour == 24 else "PM"
                label = QLabel(f"{display_hour} {am_pm}")
                self.timeScale.addWidget(label)
                self.timeScaleLabels.append(label)

                spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
                self.timeScale.addItem(spacer)
            else:
                label = QLabel("-")
                self.timeScale.addWidget(label)
                self.timeScaleLabels.append(label)
                spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
                self.timeScale.addItem(spacer)

    def loadTimeBlocks(self):
        def time_to_minutes(time_str):
            base_time = datetime.strptime("4:00 AM", "%I:%M %p")
            current_time = datetime.strptime(time_str, "%I:%M %p")
            if current_time < base_time:
                current_time += timedelta(days=1)
            return int((current_time - base_time).total_seconds() // 60)

        total_minutes = 24 * 60
        current_position = 0

        # Clear existing rows and start fresh
        self.timeBlocksWidget.layout.setColumnStretch(0, 1)  # Make sure the column stretches
        # Adjust the parent layout stretches to ensure timeBlocksWidget fills remaining space
        # Assuming timeBlockLayout is QHBoxLayout that holds self.timeScale and self.timeBlocksWidget:
        # Find that layout and set stretches:
        parent_layout = self.mainLayout.itemAt(
            self.mainLayout.count() - 1).layout()  # The last added layout is timeBlockLayout
        parent_layout.setStretch(0, 1)  # timescale layout stretch
        parent_layout.setStretch(1, 5)  # make timeBlocksWidget fill remaining space

        for time_block in sorted(self.time_blocks, key=lambda x: time_to_minutes(x[0])):
            start_time, end_time, task_name = time_block
            start_minutes = time_to_minutes(start_time)
            end_minutes = time_to_minutes(end_time)

            # Gap block
            if start_minutes > current_position:
                gap_minutes = start_minutes - current_position
                self.timeBlocksWidget.add_row(gap_minutes)
                gap_block = QLabel(f"{4 + current_position // 60}:00 AM - {4 + start_minutes // 60}:00 AM")
                gap_block.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # Set size policy so it expands to fill available space
                gap_block.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                gap_block.setStyleSheet("background-color: rgba(240,240,240,0.5); border: 1px dashed #bdbdbd;")
                self.timeBlocksWidget.add_widget_to_row(self.timeBlocksWidget.get_row_count() - 1, gap_block)

            # Task block
            task_minutes = end_minutes - start_minutes
            self.timeBlocksWidget.add_row(task_minutes)
            block = QFrame()
            block.setFrameShape(QFrame.Shape.Box)
            # Use RGBA for translucent background
            block.setStyleSheet("background-color: rgba(224,247,250,0.5); border: 1px solid #00838f;")
            blockLayout = QVBoxLayout(block)
            blockLayout.setContentsMargins(0, 0, 0, 0)
            blockLayout.setSpacing(0)
            label = QLabel(f"{task_name}\n{start_time} - {end_time}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            block.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            blockLayout.addWidget(label)
            self.timeBlocksWidget.add_widget_to_row(self.timeBlocksWidget.get_row_count() - 1, block)

            current_position = end_minutes

        # Fill remaining gap
        if current_position < total_minutes:
            gap_minutes = total_minutes - current_position
            self.timeBlocksWidget.add_row(gap_minutes)
            gap_block = QLabel(f"{4 + current_position // 60}:00 AM - 4:00 AM")
            gap_block.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gap_block.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            gap_block.setStyleSheet("background-color: rgba(240,240,240,0.5); border: 1px dashed #bdbdbd;")
            self.timeBlocksWidget.add_widget_to_row(self.timeBlocksWidget.get_row_count() - 1, gap_block)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScheduleViewWidget()
    window.setWindowTitle("Time Schedule")
    window.show()
    sys.exit(app.exec())
