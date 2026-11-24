import logging
from functools import partial
from pathlib import Path
from typing import Dict

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor, QIcon

from .ui_main_window import Ui_MainWindow
from .login_dialog import LoginDialog
from .engineer_window import EngineerWindow
from commands import Command, CmdType


PARTS_PER_SHELF = 8
OPERATOR_DIALOG_SIZE = QtCore.QSize(520, 336)
STYLE_PATH = Path(__file__).resolve().with_name("style.qss")


# Цвета ореола свечения вокруг светодиодов
GLOW_COLORS = {
    "green":  QColor(34, 197, 94, 160),   # Зеленое свечение
    "yellow": QColor(234, 179, 8, 160),   # Желтое свечение
    "red":    QColor(239, 68, 68, 180),   # Красное свечение
    "off":    QColor(0, 0, 0, 0)          # Без свечения
}

# Словарь цветов для ореола свечения вокруг лампочки
SYSTEM_STATUS_CONFIG = {
    "ready":   ("Готов", "green"),
    "running": ("В работе", "blue"),
    "paused":  ("Пауза", "yellow"),
    "manual":  ("Ручной режим", "yellow"),
    "error":   ("Ошибка", "red")
}

CNC_STATUS_CONFIG = {
    "inactive": ("Не активен", "off"),
    "ready":    ("Готов", "green"),
    "running":  ("В работе", "yellow"),
    "error":    ("Ошибка", "red")
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

        self.clock_timer = QtCore.QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.update_clock()
        self.clock_timer.start(1000)

        self.ui.powerOffButton.setIcon(QIcon(str(Path(__file__).resolve().with_name("power_off.png"))))
        self.ui.powerOffButton.clicked.connect(self.confirm_shutdown)
        self.init_table_controls()

        self._idle_operation_text = self.ui.operationStatusLabel.text()
        self.ui.startButton.clicked.connect(self.start)
        self.ui.pauseButton.clicked.connect(self.pause_resume)
        self.ui.stopButton.clicked.connect(self.stop)

        self.ui.speedSlider.actionTriggered.connect(self.snap_speed_slider)
        self.ui.speedSlider.valueChanged.connect(self.update_speed_label)
        self.update_speed_label(self.ui.speedSlider.value())

        self.ui.engineerButton.clicked.connect(self.open_engineer_login)

        self.ui.cnc1CheckBox.toggled.connect(lambda checked: self.on_cnc_selection_changed(1, checked))
        self.ui.cnc2CheckBox.toggled.connect(lambda checked: self.on_cnc_selection_changed(2, checked))

        self.set_cnc_status(1, "ready" if self.ui.cnc1CheckBox.isChecked() else "inactive")
        self.set_cnc_status(2, "ready" if self.ui.cnc2CheckBox.isChecked() else "inactive")
        self._set_cycle_mode("ready")

    def update_clock(self):
        now = QtCore.QDateTime.currentDateTime()
        self.ui.timeLabel.setText(now.toString("HH:mm:ss"))
        self.ui.dateLabel.setText(now.toString("dd.MM.yyyy"))

    def prepare_operator_dialog(self, dialog):
        layout = dialog.layout()
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(8)
        dialog.setFixedSize(OPERATOR_DIALOG_SIZE)
        dialog.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        dialog.setProperty("uiRole", "operatorDialog")
        try:
            style = STYLE_PATH.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            logging.getLogger(__name__).warning(
                "Не удалось загрузить стиль диалогов %s: %s", STYLE_PATH, error
            )
        else:
            dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            surface = QtWidgets.QFrame(dialog)
            surface.setObjectName("operatorDialogSurface")
            surface.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            surface.setGeometry(dialog.rect())
            surface.lower()
            dialog.setStyleSheet(style)

    def confirm_shutdown(self, *, parent=None):
        dialog = QtWidgets.QDialog(self if parent is None else parent)
        dialog.setWindowTitle("Выключение")

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addStretch()

        icon = QtWidgets.QLabel(dialog)
        icon.setPixmap(self.ui.powerOffButton.icon().pixmap(54, 54))
        icon.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(icon)

        question = QtWidgets.QLabel("Выключить систему?", dialog)
        question.setObjectName("shutdownQuestionLabel")
        question.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(question)
        layout.addStretch()

        no_button = QtWidgets.QPushButton("Нет", dialog)
        yes_button = QtWidgets.QPushButton("Да", dialog)
        no_button.clicked.connect(dialog.reject)
        yes_button.clicked.connect(dialog.accept)
        yes_button.setProperty("dialogAction", "danger")
        no_button.setDefault(True)

        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(12)
        buttons.addStretch()
        buttons.addWidget(no_button)
        buttons.addWidget(yes_button)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.prepare_operator_dialog(dialog)
        no_button.setFocus()

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Выключение компьютера в Windows:
            # import subprocess
            # subprocess.Popen(["shutdown.exe", "/s", "/t", "0"])
            QtWidgets.QApplication.closeAllWindows()

    def init_table_controls(self):
        shelves = (
            self.ui.shelf1gridLayout,
            self.ui.shelf2gridLayout,
            self.ui.shelf3gridLayout,
        )
        self._table_cells = {}
        for layout in shelves:
            for index in range(layout.count()):
                cell = layout.itemAt(index).widget()
                cell_number = int(cell.objectName().rsplit("_", 1)[1])
                self._table_cells[cell_number] = cell

        self._table_cell_states = dict.fromkeys(self._table_cells, "blank")

        shelf_label = self.ui.shelfNumLable
        part_label = self.ui.partNumLable
        self.ui.shelf_minus.clicked.connect(
            partial(self.change_table_selection, shelf_label, -1, len(shelves))
        )
        self.ui.shelf_plus.clicked.connect(
            partial(self.change_table_selection, shelf_label, 1, len(shelves))
        )
        self.ui.part_minus.clicked.connect(
            partial(self.change_table_selection, part_label, -1, PARTS_PER_SHELF)
        )
        self.ui.part_plus.clicked.connect(
            partial(self.change_table_selection, part_label, 1, PARTS_PER_SHELF)
        )

    def change_table_selection(self, label, step, maximum):
        value = min(maximum, max(1, int(label.text()) + step))
        label.setText(str(value))
        self.update_table_selection()

    def update_table_selection(self):
        shelf = int(self.ui.shelfNumLable.text())
        part = int(self.ui.partNumLable.text())
        self.current_part = (shelf - 1) * PARTS_PER_SHELF + part

        show_start = self._cycle_mode == "ready"
        for cell_number, cell in self._table_cells.items():
            state = self._table_cell_states[cell_number]
            if cell_number < self.current_part:
                state = "empty"
            elif show_start and cell_number == self.current_part and state == "blank":
                state = "start"
            if cell.property("cellState") != state:
                self.set_cell_state(cell, state)

    def set_table_cell_state(self, cell_number, state):
        """Изменить содержимое ячейки стола по сквозному номеру."""
        if cell_number not in self._table_cells:
            raise ValueError(f"Номер ячейки должен быть от 1 до {len(self._table_cells)}")
        if state not in ("empty", "blank", "done"):
            raise ValueError("Допустимые состояния ячейки: empty, blank, done")

        self._table_cell_states[cell_number] = state
        self.update_table_selection()

    # Получение состояния активности cnc
    def on_cnc_selection_changed(self, cnc_number, checked):
        status = "ready" if checked else "inactive"
        self.set_cnc_status(cnc_number, status)
        self.ui.startButton.setEnabled(self._can_start_cycle())

    def _can_start_cycle(self):
        return self._cycle_mode == "ready" and (
            self.ui.cnc1CheckBox.isChecked() or self.ui.cnc2CheckBox.isChecked()
        )

    # Управление доступностью элементов
    def set_operation_controls(self, enabled):
        self.ui.speedFrame.setEnabled(enabled)
        self.ui.shelfFrame.setEnabled(enabled)
        self.ui.partFrame.setEnabled(enabled)
        self.ui.engineerButton.setEnabled(enabled)
        self.ui.cnc1CheckBox.setEnabled(enabled)
        self.ui.cnc2CheckBox.setEnabled(enabled)

    def snap_speed_slider(self):
        slider = self.ui.speedSlider
        step = slider.singleStep()
        offset = slider.sliderPosition() - slider.minimum()
        snapped = slider.minimum() + (offset + step // 2) // step * step
        slider.setSliderPosition(snapped)

    def update_speed_label(self, value):
        self.ui.speedNumLabel.setText(f"{value}%")

    # Чтение параметров
    def read_operation_parameters(self):
        return {
            "shelf": int(self.ui.shelfNumLable.text()),
            "workpiece": int(self.ui.partNumLable.text()),
            "speed": self.ui.speedSlider.value(),
            "cnc1": self.ui.cnc1CheckBox.isChecked(),
            "cnc2": self.ui.cnc2CheckBox.isChecked()
        }

    # Управление индикаторами
    def set_indicator(self, indicator, state: str):
        indicator.setProperty("indicator", True)
        indicator.setProperty("state", state)

        indicator.style().unpolish(indicator)
        indicator.style().polish(indicator)
        indicator.update()

    def set_system_status(self, status: str):
        text, state = SYSTEM_STATUS_CONFIG[status]
        self.ui.systemStatusLabel.setText(text)
        self.set_indicator(self.ui.systemStatusIndicator, state)

    def set_cnc_status(self, cnc_number, status):
        cnc_widgets = {
            1: (self.ui.cnc1StatusIndicator, self.ui.cnc1StatusLabel, self.ui.cnc1Frame),
            2: (self.ui.cnc2StatusIndicator, self.ui.cnc2StatusLabel, self.ui.cnc2Frame),
        }

        indicator, text_label, frame = cnc_widgets[cnc_number]
        text, color = CNC_STATUS_CONFIG[status]

        text_label.setText(text)
        self.set_indicator(indicator, color)

        frame.setProperty("state", status)
        style = frame.style()
        style.unpolish(frame)
        style.polish(frame)
        frame.update()

    def _set_cycle_mode(self, mode):
        self._cycle_mode = mode
        idle = mode == "ready"
        paused = mode == "paused"

        self.ui.startButton.setEnabled(self._can_start_cycle())
        self.ui.stopButton.setEnabled(not idle)
        self.set_operation_controls(idle)

        pause_button = self.ui.pauseButton
        pause_button.setEnabled(not idle)
        pause_button.setText("Продолжить" if paused else "Пауза")
        pause_button.setProperty("state", mode)
        style = pause_button.style()
        style.unpolish(pause_button)
        style.polish(pause_button)
        pause_button.update()

        self.set_system_status(mode)
        self.ui.operationStatusLabel.setText({
            "ready": self._idle_operation_text,
            "running": "Выполняется рабочий цикл",
            "paused": "Рабочий цикл на паузе",
        }[mode])
        self.update_table_selection()

    def start(self):
        if self._can_start_cycle():
            self._set_cycle_mode("running")
            self.cmd_queue.put(
                Command(CmdType.AUTO_START, {}, source="GUI"))


    def pause_resume(self):
        if self._cycle_mode == "running":
            self._set_cycle_mode("paused")
            self.cmd_queue.put(
                Command(CmdType.AUTO_PAUSE, {}, source="GUI"))
        elif self._cycle_mode == "paused":
            self._set_cycle_mode("running")
            self.cmd_queue.put(
                Command(CmdType.AUTO_START, {}, source="GUI"))


    def stop(self):
        self._set_cycle_mode("ready")
        self.cmd_queue.put(
            Command(CmdType.AUTO_STOP, {}, source="GUI"))

    def set_cell_state(self, cell, state):
        cell.setProperty("cellState", state)
        style = cell.style()
        style.unpolish(cell)
        style.polish(cell)
        cell.update()

    def open_engineer_login(self):
        dialog = LoginDialog(self)
        self.prepare_operator_dialog(dialog)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            if self.engineer_window is None:
                self.engineer_window = EngineerWindow(self.RobotController, self)

                # Открываем файл стилей (если положили его в папку ui)
                with open("ui/style.qss", "r", encoding="utf-8") as file:
                    qss_styles = file.read()
                # Применяем стили
                self.engineer_window.setStyleSheet(qss_styles)

                self.engineer_window.shutdown_requested.connect(
                    partial(self.confirm_shutdown, parent=self.engineer_window)
                )
                self.RobotController.set_engineer_mode(True)
                eng_mode = self.RobotController.get_state_snapshot().engineer_mode
                print("engineer_mode", eng_mode)

            self.engineer_window.showFullScreen()
            self.engineer_window.raise_()
            self.engineer_window.activateWindow()
