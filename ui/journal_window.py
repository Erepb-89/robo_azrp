from __future__ import annotations

from datetime import datetime
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from .ui_journal_window import Ui_JournalWindow


MAX_JOURNAL_ROWS = 2000
ALERT_LEVEL_LABELS = {
    "info": "Информация",
    "warning": "Предупреждение",
    "error": "Ошибка",
}


def _entry_palette_property(category):
    # QSS передаёт пару цветов, а роли ячеек применяют её к отдельным записям.
    def get_colors(window):
        return " ".join(brush.color().name() for brush in window._entry_brushes.get(category, ()))

    def set_colors(window, value):
        colors = [QtGui.QColor(name) for name in value.split()]
        if len(colors) == 2 and all(color.isValid() for color in colors):
            window._entry_brushes[category] = tuple(QtGui.QBrush(color) for color in colors)

    return QtCore.pyqtProperty(str, get_colors, set_colors)


class JournalWindow(QtWidgets.QMainWindow):
    shutdown_requested = QtCore.pyqtSignal()
    back_requested = QtCore.pyqtSignal()
    _entry_requested = QtCore.pyqtSignal(str, tuple, str, tuple)

    operatorEntryColors = _entry_palette_property("operator")
    warningEntryColors = _entry_palette_property("warning")
    errorEntryColors = _entry_palette_property("error")

    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self._entry_brushes = {}
        self.ui = Ui_JournalWindow()
        self.ui.setupUi(self)
        self.ensurePolished()
        self.ui.powerOffButton.clicked.connect(self.shutdown_requested)
        self.ui.exitButton.clicked.connect(self.back_requested)
        self.ui.journalTabs.setFocus(QtCore.Qt.OtherFocusReason)

        self._tables = {
            "events": self.ui.eventsTable,
            "alerts": self.ui.alertsTable,
            "technical": self.ui.technicalTable,
        }
        self._configure_table(self.ui.eventsTable, (236,))
        self._configure_table(self.ui.alertsTable, (236, 214, 150))
        self._configure_table(self.ui.technicalTable, (236, 144, 280))
        self._entry_requested.connect(self._insert_entry)

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

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot(str, str)
    @QtCore.pyqtSlot(str, str, object)
    def add_event(
        self, text: str, category: str = "system", timestamp: datetime | None = None
    ) -> None:
        stamp = self._format_timestamp(timestamp)
        self._entry_requested.emit("events", (stamp, text), category.lower(), (1,))

    @QtCore.pyqtSlot(str, str)
    @QtCore.pyqtSlot(str, str, str)
    @QtCore.pyqtSlot(str, str, str, object)
    def add_alert(
        self, code: str, text: str, severity: str = "warning", timestamp: datetime | None = None
    ) -> None:
        stamp = self._format_timestamp(timestamp)
        severity = severity.lower()
        if severity not in ALERT_LEVEL_LABELS:
            severity = "warning"
        level = ALERT_LEVEL_LABELS[severity]
        self._entry_requested.emit("alerts", (stamp, level, code, text), severity, (1, 2))

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot(str, str)
    @QtCore.pyqtSlot(str, str, str)
    @QtCore.pyqtSlot(str, str, str, object)
    def add_technical_entry(
        self, text: str, level: str = "INFO", source: str = "", timestamp: datetime | None = None
    ) -> None:
        stamp = self._format_timestamp(timestamp)
        category = {
            "WARN": "warning", "WARNING": "warning", "ERROR": "error", "CRITICAL": "error",
        }.get(level.upper(), "")
        self._entry_requested.emit("technical", (stamp, level, source, text), category, (1,))

    @staticmethod
    def _format_timestamp(timestamp):
        if timestamp is None:
            timestamp = datetime.now()
        return timestamp.strftime("%d.%m.%Y %H:%M:%S")

    @QtCore.pyqtSlot(str, tuple, str, tuple)
    def _insert_entry(self, name, values, category, accent_columns):
        table = self._tables[name]
        scrollbar = table.verticalScrollBar()
        previous_scroll = scrollbar.value()
        brushes = self._entry_brushes.get(category)
        table.insertRow(0)
        for column, value in enumerate(values):
            item = QtWidgets.QTableWidgetItem(value)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            if brushes and column in accent_columns:
                item.setForeground(brushes[0])
                item.setBackground(brushes[1])
            table.setItem(0, column, item)

        if table.rowCount() > MAX_JOURNAL_ROWS:
            table.removeRow(MAX_JOURNAL_ROWS)
        table.resizeRowToContents(0)
        table.updateGeometries()
        # При просмотре истории компенсируем высоту вставленной строки.
        scrollbar.setValue(previous_scroll + table.rowHeight(0) if previous_scroll else 0)

    def _configure_table(self, table, column_widths):
        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        for column, width in enumerate(column_widths):
            table.setColumnWidth(column, width)
        QtWidgets.QScroller.grabGesture(table.viewport(), QtWidgets.QScroller.TouchGesture)

        reflow_timer = QtCore.QTimer(table)
        reflow_timer.setSingleShot(True)
        reflow_timer.timeout.connect(partial(self._resize_table_rows, table))
        header.sectionResized.connect(lambda *_: reflow_timer.start(0))

    @staticmethod
    def _resize_table_rows(table):
        scrollbar = table.verticalScrollBar()
        top_row = table.rowAt(0) if scrollbar.value() else -1
        row_offset = -table.rowViewportPosition(top_row) if top_row >= 0 else 0
        table.resizeRowsToContents()
        table.updateGeometries()
        if top_row >= 0:
            position = table.verticalHeader().sectionPosition(top_row)
            scrollbar.setValue(position + min(row_offset, table.rowHeight(top_row) - 1))
