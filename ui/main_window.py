from typing import Dict

from PyQt5 import QtWidgets
from .ui_main_window import Ui_MainWindow
from .login_dialog import LoginDialog
from PyQt5.QtWidgets import QDialog
from .engineer_window import EngineerWindow
from .login_dialog import LoginDialog
from commands import Command, CmdType

SYSTEM_STATUS_CONFIG = {
    "ready":   ("Готов", "#4CAF50"),
    "running": ("Работа", "#4CAF50"),
    "paused":  ("Пауза", "#FFC107"),
    "manual":  ("Ручной режим", "#FFC107"),
    "error":   ("Ошибка", "#F44336")
}

CNC_STATUS_CONFIG = {
    "inactive": ("Не активен", "#bdbdbd"),
    "ready":    ("Готов", "#4CAF50"),
    "running":  ("В работе", "#FFC107"),
    "error":    ("Ошибка", "#F44336")
}

class MainOperWindow(QtWidgets.QMainWindow):

    def __init__(self, robot_controller, cmd_queue, command_handler,
                 heartbeat=None, cmd_log_queue=None):
        super().__init__()
        self.RobotController = robot_controller
        self.cmd_queue = cmd_queue
        self.Waypoints: Dict[str, dict] = {}
        self.Trajectories: Dict[str, dict] = {}
        self._heartbeat = heartbeat
        self._cmd_log_queue = cmd_log_queue  # очередь событий

        self.engineer_window = None
        self.InitUI()

    def InitUI(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.startPauseButton.clicked.connect(self.start_pause)
        self.ui.stopButton.clicked.connect(self.stop)

        self.set_system_status("ready")

        self.ui.engineerButton.clicked.connect(self.open_engineer_login)

        self.ui.cnc1CheckBox.toggled.connect(lambda checked: self.on_cnc_selection_changed(1, checked))
        self.ui.cnc2CheckBox.toggled.connect(lambda checked: self.on_cnc_selection_changed(2, checked))

        self.set_cnc_status(1, "ready" if self.ui.cnc1CheckBox.isChecked() else "inactive")
        self.set_cnc_status(2, "ready" if self.ui.cnc2CheckBox.isChecked() else "inactive")


    # Получение состояния активности cnc
    def on_cnc_selection_changed(self, cnc_number, checked):
        status = "ready" if checked else "inactive"
        self.set_cnc_status(cnc_number, status)

    # Управление доступностью элементов
    def set_operation_controls(self, enabled):
        self.ui.ActiveCncGroupBox.setEnabled(enabled)
        self.ui.ParametersGroupBox.setEnabled(enabled)
        self.ui.engineerButton.setEnabled(enabled)

    # Чтение параметров
    def read_operation_parameters(self):
        return {
            "shelf": self.ui.shelfSpinBox.value(),
            "workpiece": self.ui.workpieceSpinBox.value(),
            "speed": self.ui.speedSpinBox.value(),
            "cnc1": self.ui.cnc1CheckBox.isChecked(),
            "cnc2": self.ui.cnc2CheckBox.isChecked()
        }

    # Управление индикаторами
    def set_indicator(self, indicator, color):
        indicator.setStyleSheet(
            f"background-color: {color}; "
            "border-radius: 11px; "
            "border: 1px solid #777777;"
        )

    def set_system_status(self, status):
        text, color = SYSTEM_STATUS_CONFIG[status]

        self.ui.systemStatusTextLabel.setText(text)
        self.set_indicator(self.ui.systemStatusIndicator, color)

    def set_cnc_status(self, cnc_number, status):
        cnc_widgets = {
            1: (self.ui.cnc1StatusIndicator, self.ui.cnc1StatusTextLabel),
            2: (self.ui.cnc2StatusIndicator, self.ui.cnc2StatusTextLabel)
        }

        indicator, text_label = cnc_widgets[cnc_number]
        text, color = CNC_STATUS_CONFIG[status]

        text_label.setText(text)
        self.set_indicator(indicator, color)

    # Управление старт/пауза/стоп
    def start_pause(self):

        if self.ui.startPauseButton.text() == "Старт":

            params = self.read_operation_parameters()
            print("Параметры задания:", params)

            #self.set_cnc_status(1, "running" if params["cnc1"] else "inactive")
            #self.set_cnc_status(2, "running" if params["cnc2"] else "inactive")

            self.cmd_queue.put(
                Command(CmdType.AUTO_START, {}, source="GUI"))

            self.ui.startPauseButton.setText("Пауза")
            self.set_system_status("running")
            self.set_operation_controls(False)

        else:
            self.ui.startPauseButton.setText("Старт")
            self.set_system_status("paused")

            self.cmd_queue.put(
                Command(CmdType.AUTO_PAUSE, {}, source="GUI"))

            #self.set_cnc_status(1, "paused" if self.ui.cnc1CheckBox.isChecked() else "inactive")
            #self.set_cnc_status(2, "paused" if self.ui.cnc2CheckBox.isChecked() else "inactive")

    def stop(self):

        self.ui.startPauseButton.setText("Старт")
        self.set_system_status("ready")
        self.set_operation_controls(True)

        self.cmd_queue.put(
            Command(CmdType.AUTO_STOP, {}, source="GUI"))

        #self.set_cnc_status(1, "ready" if self.ui.cnc1CheckBox.isChecked() else "inactive")
        #self.set_cnc_status(2, "ready" if self.ui.cnc2CheckBox.isChecked() else "inactive")

    def open_engineer_login(self):
        dialog = LoginDialog(self)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            if self.engineer_window is None:
                self.engineer_window = EngineerWindow(self)

            self.engineer_window.show()
            self.engineer_window.raise_()
            self.engineer_window.activateWindow()
