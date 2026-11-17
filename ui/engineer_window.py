from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtCore, QtWidgets
from .ui_engineer_window import Ui_EngineerWindow


class EngineerWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.InitUI()

        self.ui.di_M1_Ready.setChecked(True)
        self.ui.di_M1_Alarm.setChecked(True)
        # self.ui.do_G1_Clamp.setChecked(True)

    def InitUI(self):
        self.ui = Ui_EngineerWindow()
        self.ui.setupUi(self)
        self.setup_indicator_style()
        self.setup_inputs_readonly()
        self.ui.exitButton.clicked.connect(self.close)

    def setup_indicator_style(self):
        self.setStyleSheet("""
            QCheckBox::indicator,
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #777777;
                background-color: #bdbdbd;
            }

            QCheckBox::indicator:checked,
            QRadioButton::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #388E3C;
            }
        """)

    def setup_inputs_readonly(self):

        for checkbox in self.findChildren(QtWidgets.QCheckBox):

            name = checkbox.objectName()

            if name.startswith(("di_", "mbtcp_")):
                checkbox.setAttribute(
                    QtCore.Qt.WA_TransparentForMouseEvents, True
                )

                checkbox.setFocusPolicy(QtCore.Qt.NoFocus)