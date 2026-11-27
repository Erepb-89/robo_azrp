from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets

from .ui_alert_dialog import Ui_AlertDialog
from .ui_confirm_dialog import Ui_ConfirmDialog
from .ui_login import Ui_LoginDialog
from .virtual_keyboard import VirtualKeyboard


UI_DIR = Path(__file__).resolve().parent

ENGINEER_LOGIN = "Admin"
ENGINEER_PASSWORD = "123"

ALERT_TITLES = {
    "error": "Ошибка",
    "warning": "Предупреждение",
}

ALERT_RECOMMENDATIONS = {
    ("error", "E-TEST"): "Тестовое сообщение об ошибке.",
    ("warning", "W-TEST"): "Тестовое предупреждение.",
}


class PopupDialogs:
    """Модальные окна приложения. Вызывать в потоке интерфейса Qt."""

    @classmethod
    def show_alert(cls, severity, code, *, parent=None):
        """Вернуть QDialog.Accepted для «ОК» или QDialog.Rejected для «Стоп»."""
        title = ALERT_TITLES.get(severity)
        if title is None:
            raise ValueError("Тип сообщения должен быть 'error' или 'warning'")

        code = str(code)
        recommendations = ALERT_RECOMMENDATIONS.get(
            (severity, code), "Для этого кода пока нет рекомендаций."
        )
        dialog = AlertDialog(severity, title, code, recommendations, cls._dialog_parent(parent))
        return cls._exec_dialog(dialog)

    @classmethod
    def show_login(cls, *, parent=None):
        """Вернуть QDialog.Accepted после входа или QDialog.Rejected при отмене."""
        dialog = LoginDialog(cls._dialog_parent(parent))
        return cls._exec_dialog(dialog)

    @classmethod
    def confirm_shutdown(cls, *, parent=None):
        """Вернуть QDialog.Accepted для «Да» или QDialog.Rejected для «Нет»."""
        return cls.confirm_action(
            "Выключить систему?",
            QtGui.QIcon(str(UI_DIR / "power_off.png")),
            confirm_text="Да",
            cancel_text="Нет",
            title="Выключение",
            danger=True,
            parent=parent,
        )

    @classmethod
    def confirm_action(
        cls, question, icon, *, confirm_text, cancel_text,
        title="Подтверждение", danger=False, parent=None,
    ):
        """Показать универсальное подтверждение и вернуть результат QDialog."""
        dialog = QtWidgets.QDialog(cls._dialog_parent(parent))
        ui = Ui_ConfirmDialog()
        ui.setupUi(dialog)
        dialog.setWindowTitle(title)
        ui.shutdownQuestionLabel.setText(question)
        ui.confirmIcon.setPixmap(icon.pixmap(54, 54))
        ui.confirmCancelButton.setText(cancel_text)
        ui.confirmAcceptButton.setText(confirm_text)
        if danger:
            ui.confirmAcceptButton.setProperty("dialogAction", "danger")
        ui.confirmCancelButton.setFocus()
        return cls._exec_dialog(dialog)

    @staticmethod
    def _dialog_parent(parent):
        if parent is not None:
            return parent.window()
        for window in (QtWidgets.QApplication.activeModalWidget(), QtWidgets.QApplication.activeWindow()):
            if window is not None and window.isVisible():
                return window
        for window in QtWidgets.QApplication.topLevelWidgets():
            if window.isVisible() and window.windowType() == QtCore.Qt.Window:
                return window
        return None

    @staticmethod
    def _exec_dialog(dialog):
        dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        return dialog.exec_()


class LoginDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)

        self.keyboard = VirtualKeyboard(self)
        self.keyboard.attach(self.ui.loginEdit, self.ui.passwordEdit)

        self.ui.loginButton.clicked.connect(self.check_credentials)
        self.keyboard.done.connect(self.ui.loginButton.click)
        self.ui.cancelButton.clicked.connect(self.reject)

    def showEvent(self, event):
        super().showEvent(event)
        self.ui.passwordEdit.setFocus()

    def check_credentials(self):
        login = self.ui.loginEdit.text()
        password = self.ui.passwordEdit.text()

        if login == ENGINEER_LOGIN and password == ENGINEER_PASSWORD:
            self.accept()
        else:
            self.ui.errorLabel.setText("Неверный логин или пароль")
            self.ui.passwordEdit.clear()
            self.ui.passwordEdit.setFocus()
            self.keyboard.show_for_focused_field()


class AlertDialog(QtWidgets.QDialog):
    def __init__(self, severity, title, code, recommendations, parent=None):
        super().__init__(parent)
        self.setProperty("alertSeverity", severity)
        self.ui = Ui_AlertDialog()
        self.ui.setupUi(self)
        self._preferred_size = self.size()

        self.setWindowTitle(title)
        self.ui.alertTitle.setText(title)
        self.ui.alertCode.setText(code)
        self.ui.alertRecommendationText.setText(recommendations)
        self.ui.alertOkButton.setFocus()

        QtWidgets.QScroller.grabGesture(
            self.ui.alertRecommendationScroll.viewport(), QtWidgets.QScroller.TouchGesture
        )

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parentWidget()
        screen = parent.screen() if parent is not None else self.screen()
        area = screen.availableGeometry()
        self.setFixedSize(self._preferred_size.boundedTo(area.size() - QtCore.QSize(32, 32)))
        self.move(area.center() - self.rect().center())
