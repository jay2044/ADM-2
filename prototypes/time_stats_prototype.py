from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class DayStatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Remaining hours label
        self.remaining_hours_label = QLabel("16hrs left today")
        self.remaining_hours_label.setStyleSheet("""
            font-size: 20px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            color: rgba(255, 255, 255, 0.85);
            letter-spacing: 0.5px;
            padding: 4px;
            transition: color 0.2s ease, text-shadow 0.2s ease;
        """)
        self.layout.addWidget(self.remaining_hours_label)

        # Progress Bar Container
        self.progress_container = QWidget()
        self.progress_layout = QVBoxLayout()
        self.progress_layout.setSpacing(2)

        self.progress_label = QLabel("Finished work: 2hr/8hr total")
        self.progress_label.setStyleSheet("""
            font-size: 14px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            color: rgba(255, 255, 255, 0.7);
            padding: 2px;
        """)
        self.progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.2);
                background-color: rgba(0, 0, 0, 0.2);
                height: 8px;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: rgba(0, 255, 255, 0.8);
                border-radius: 5px;
            }
        """)
        self.progress_bar.setMaximum(16) # Total work time
        self.progress_bar.setValue(2) # Completed work time
        self.progress_layout.addWidget(self.progress_bar)

        self.progress_container.setLayout(self.progress_layout)
        self.layout.addWidget(self.progress_container)

        # Remaining work time label
        self.remaining_worktime_label = QLabel("6hr of work left")
        self.remaining_worktime_label.setStyleSheet("""
            font-size: 16px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            color: rgba(255, 255, 255, 0.7);
            padding: 2px;
        """)
        self.layout.addWidget(self.remaining_worktime_label)

        # On schedule label
        self.on_schedule_label = QLabel("On schedule")
        self.on_schedule_label.setStyleSheet("""
            font-size: 14px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            color: rgba(0, 255, 0, 0.8);
            padding: 2px;
        """)
        self.layout.addWidget(self.on_schedule_label)

        self.setLayout(self.layout)

    def update_status(self, remaining_hours, total_worktime, remaining_worktime, finished_worktime, on_schedule):
        self.remaining_hours_label.setText(f"{remaining_hours}hrs left today")
        self.progress_label.setText(f"Finished work: {finished_worktime}hr/{total_worktime}hr")
        self.progress_bar.setMaximum(total_worktime)
        self.progress_bar.setValue(finished_worktime)
        self.remaining_worktime_label.setText(f"{remaining_worktime}hr of work left")
        self.on_schedule_label.setText("On schedule" if on_schedule else "Off schedule")
        self.on_schedule_label.setStyleSheet(f"""
            font-size: 14px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            color: {'rgba(0, 255, 0, 0.8)' if on_schedule else 'rgba(255, 0, 0, 0.8)'};
            padding: 2px;
        """)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = DayStatusWidget()
    window.update_status(16, 9, 6, 3, True)
    window.show()
    sys.exit(app.exec())
