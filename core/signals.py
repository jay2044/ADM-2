from PyQt6.QtCore import QObject, pyqtSignal


class GlobalSignals(QObject):
    task_list_updated = pyqtSignal()


global_signals = GlobalSignals()
