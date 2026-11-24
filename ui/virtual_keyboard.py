"""Экранная клавиатура для полей QLineEdit одного окна."""

from functools import partial

from PyQt5.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QPushButton, QWidget

from .ui_virtual_keyboard import Ui_VirtualKeyboard


class VirtualKeyboard(QWidget):
    done = pyqtSignal()
    GAP = 16

    def __init__(self, owner):
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
        super().__init__(owner, flags)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.ui = Ui_VirtualKeyboard()
        self.ui.setupUi(self)
        self._owner = owner
        self._fields = []
        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self.show_for_focused_field)

        for button in self.ui.virtualKeyboardSurface.findChildren(QPushButton):
            if button.property("keyboardKey") == "character":
                button.clicked.connect(partial(self._insert, button.text()))
        self.ui.spaceButton.clicked.connect(partial(self._insert, " "))
        self.ui.backspaceButton.clicked.connect(self._backspace)
        self.ui.doneButton.clicked.connect(self._finish)
        owner.installEventFilter(self)

    def attach(self, *fields):
        """Подключить поля QLineEdit, принадлежащие окну owner."""
        for field in fields:
            if field not in self._fields:
                self._fields.append(field)
                field.installEventFilter(self)
        if self._owner.isVisible():
            self._show_timer.start(0)

    def eventFilter(self, watched, event):
        event_type = event.type()
        if watched is self._owner:
            if event_type == QEvent.Show:
                self._show_timer.start(0)
            elif event_type == QEvent.Hide:
                self.dismiss()
        elif event_type in (QEvent.FocusIn, QEvent.FocusOut, QEvent.MouseButtonPress):
            self._show_timer.start(0)
        return super().eventFilter(watched, event)

    def dismiss(self):
        self._show_timer.stop()
        self.hide()
        self.ui.shiftButton.setChecked(False)

    def _finish(self):
        self.dismiss()
        self.done.emit()

    def _focused_field(self):
        field = self._owner.focusWidget()
        if field in self._fields and field.isVisible() and field.isEnabled() and not field.isReadOnly():
            return field
        return None

    def show_for_focused_field(self):
        if not self._owner.isVisible() or self._focused_field() is None:
            self.dismiss()
        elif not self.isVisible() and self._place_windows():
            self.show()

    def _place_windows(self):
        area = self._owner.screen().availableGeometry()
        dialog_size = self._owner.frameGeometry().size()
        total_height = dialog_size.height() + self.GAP + self.height()
        if area.width() < max(dialog_size.width(), self.width()) or area.height() < total_height:
            return False

        top = area.top() + (area.height() - total_height) // 2
        dialog_left = area.left() + (area.width() - dialog_size.width()) // 2
        keyboard_left = area.left() + (area.width() - self.width()) // 2
        self._owner.move(dialog_left, top)
        self.move(keyboard_left, top + dialog_size.height() + self.GAP)
        return True

    def _insert(self, character):
        field = self._focused_field()
        if field is None:
            return
        if character.isalpha():
            if not self.ui.shiftButton.isChecked():
                character = character.lower()
            self.ui.shiftButton.setChecked(False)
        field.insert(character)

    def _backspace(self):
        field = self._focused_field()
        if field is not None:
            field.backspace()
