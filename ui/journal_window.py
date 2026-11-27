from PyQt5 import QtCore, QtWidgets

from .ui_journal_window import Ui_JournalWindow


class JournalWindow(QtWidgets.QMainWindow):
    shutdown_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.ui = Ui_JournalWindow()
        self.ui.setupUi(self)
        self.ui.powerOffButton.clicked.connect(self.shutdown_requested)
        self.ui.journalContent.setFocus(QtCore.Qt.OtherFocusReason)

        self.clock_timer = QtCore.QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self.update_clock)
        self.update_clock()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_clock()
        self.clock_timer.start()

    def hideEvent(self, event):
        self.clock_timer.stop()
        super().hideEvent(event)

    def update_clock(self):
        now = QtCore.QDateTime.currentDateTime()
        self.ui.timeLabel.setText(now.toString("HH:mm:ss"))
        self.ui.dateLabel.setText(now.toString("dd.MM.yyyy"))
