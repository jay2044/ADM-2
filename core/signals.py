from PyQt6.QtCore import QObject, pyqtSignal


class GlobalSignals(QObject):
    task_list_updated = pyqtSignal()
    refresh_schedule_signal = pyqtSignal()


global_signals = GlobalSignals()
