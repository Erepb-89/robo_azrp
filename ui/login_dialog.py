from PyQt5.QtWidgets import QDialog
from .ui_login import Ui_LoginDialog
from .virtual_keyboard import VirtualKeyboard

ENGINEER_LOGIN = "Admin"
ENGINEER_PASSWORD = "123"

class LoginDialog(QDialog):

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
