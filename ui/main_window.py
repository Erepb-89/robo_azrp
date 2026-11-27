from functools import partial
from typing import Dict

from PyQt5 import QtCore, QtWidgets

from .engineer_window import EngineerWindow
from .journal_window import JournalWindow
from .popup_dialogs import PopupDialogs
from .ui_main_window import Ui_MainWindow


PARTS_PER_SHELF = 8


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

# Состояния станка из автоцикла (auto_cycle.MachineState) -> статус ЧПУ
MACHINE_STATE_TO_CNC_STATUS = {
    0: "ready",     # NotActive (станок включён в задание и ждёт)
    1: "running",   # LoadWorkpiece
    2: "ready",     # Complete
    3: "error",     # Error
}

# Состояние автоцикла -> режим окна оператора
CYCLE_STATE_TO_MODE = {
    "idle": "ready",
    "waiting_start": "running",
    "waiting_resume": "running",
    "running": "running",
    "paused": "paused",
}

class MainOperWindow(QtWidgets.QMainWindow):

    def __init__(self, robot_controller=None, cmd_queue=None, command_handler=None,
                 heartbeat=None, cmd_log_queue=None):
        super().__init__()
        # None means an isolated UI preview: no robot connection or commands.
        self._preview = robot_controller is None
        self.RobotController = robot_controller
        self.cmd_queue = cmd_queue
        self.command_handler = command_handler
        self.Waypoints: Dict[str, dict] = {}
        self.Trajectories: Dict[str, dict] = {}
        self._heartbeat = heartbeat
        self._cmd_log_queue = cmd_log_queue  # очередь событий

        self._last_error_val = 0
        self._last_cycle_state = None
        self._last_cnc_status: Dict[int, str] = {}

        self.engineer_window = None
        self.journal_window = None
        self._journal_source = None
        self.InitUI()

    def InitUI(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Shared fullscreen container for operator, engineering, and journal pages.
        self._operator_page = self.takeCentralWidget()
        self._screens = QtWidgets.QStackedWidget(self)
        self._screens.addWidget(self._operator_page)
        self.setCentralWidget(self._screens)

        self.clock_timer = QtCore.QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.update_clock()
        self.clock_timer.start(1000)

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
        self.ui.journalButton.clicked.connect(self.open_journal)

        self.ui.cnc1CheckBox.toggled.connect(lambda checked: self.on_cnc_selection_changed(1, checked))
        self.ui.cnc2CheckBox.toggled.connect(lambda checked: self.on_cnc_selection_changed(2, checked))

        self.set_cnc_status(1, "ready" if self.ui.cnc1CheckBox.isChecked() else "inactive")
        self.set_cnc_status(2, "ready" if self.ui.cnc2CheckBox.isChecked() else "inactive")
        self._set_cycle_mode("ready")

        if not self._preview:
            self.StatusTimer = QtCore.QTimer(self)
            self.StatusTimer.timeout.connect(self._update_status)
            self.StatusTimer.start(500)

    def update_clock(self):
        now = QtCore.QDateTime.currentDateTime()
        self.ui.timeLabel.setText(now.toString("HH:mm:ss"))
        self.ui.dateLabel.setText(now.toString("dd.MM.yyyy"))

    @QtCore.pyqtSlot(str, str, result=int)
    def show_alert(self, severity, code):
        """Совместимость с вызовами через главное окно."""
        return PopupDialogs.show_alert(severity, code)

    def confirm_shutdown(self, *, parent=None):
        if PopupDialogs.confirm_shutdown(parent=parent or self) == QtWidgets.QDialog.Accepted:
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
    def on_cnc_selection_changed(self, cnc_number: int, checked: bool):
        """Переключение активности станка до запуска цикла"""
        status = "ready" if checked else "inactive"
        self.set_cnc_status(cnc_number, status)
        self.ui.startButton.setEnabled(self._can_start_cycle())
        if self._preview:
            return

        box = self.ui.cnc1CheckBox if cnc_number == 1 else self.ui.cnc2CheckBox
        try:
            accepted = self.RobotController.set_machine_active(cnc_number, checked)
        except Exception as exc:
            accepted = False
            self.RobotController.log.error(
                f"set_machine_active M{cnc_number}: {exc}")
        if accepted:
            return
        box.blockSignals(True)
        try:
            box.setChecked(not checked)
        finally:
            box.blockSignals(False)
        try:
            self.RobotController.message(
                f"М{cnc_number}: переключение недоступно "
                "(цикл запущен или станок занят)", 'warning')
        except Exception:
            pass

    def _on_machine_active_toggled(self, m: int, checked: bool):
        """Переключение активности станка (совместимо с ui_form_wp_gen)."""
        self.on_cnc_selection_changed(m, checked)

    def _can_start_cycle(self):
        return self._cycle_mode == "ready" and (
            self.ui.cnc1CheckBox.isChecked() or self.ui.cnc2CheckBox.isChecked()
        )

    def _set_actual_speed(self):
        if self._preview:
            return
        try:
            self.RobotController.set_actual_speed(int(self.ui.speedSlider.value()))
        except Exception:
            pass

    def _update_cycle_panel(self):
        """Синхронизирует панель автоцикла с текущим состоянием робота."""
        try:
            state = self.RobotController.get_state_snapshot()
        except Exception:
            return

        cycle_state = getattr(state, 'cycle_state', 'idle') or 'idle'
        active = getattr(state, 'active_machines', None)
        if not isinstance(active, dict):
            try:
                active = self.RobotController.get_active_machines()
            except Exception:
                active = {1: True, 2: True}
        m_state = getattr(state, 'm_state', {}) or {}

        idle = cycle_state == 'idle'
        for m, box in ((1, self.ui.cnc1CheckBox), (2, self.ui.cnc2CheckBox)):
            value = bool(active.get(m, True))
            if box.isChecked() != value:
                box.blockSignals(True)
                try:
                    box.setChecked(value)
                finally:
                    box.blockSignals(False)
            box.setEnabled(idle)

            if not value:
                status = "inactive"
            else:
                status = MACHINE_STATE_TO_CNC_STATUS.get(
                    m_state.get(m, 0), "ready")
            if self._last_cnc_status.get(m) != status:
                self.set_cnc_status(m, status)
                self._last_cnc_status[m] = status

        state_changed = cycle_state != self._last_cycle_state
        self._last_cycle_state = cycle_state
        if state_changed:
            target_mode = CYCLE_STATE_TO_MODE.get(cycle_state, "running")
            if self._cycle_mode == "paused" and cycle_state != "idle":
                target_mode = "paused"
            if target_mode != self._cycle_mode:
                self._set_cycle_mode(target_mode)

    def _update_status(self):
        """Периодически обновляет статусы окна по снимку состояния."""
        if self._preview:
            return
        from states_modes_errors import LastError, LAST_ERROR_RU
        self._update_cycle_panel()

        try:
            state = self.RobotController.get_state_snapshot()
            raw_err = getattr(state, 'last_error', 0)
            if raw_err is not None:
                err = raw_err if isinstance(raw_err, LastError) else LastError(raw_err)
                err_val = err.value
            else:
                err = None
                err_val = 0

            if err_val != 0:
                if err_val != self._last_error_val:
                    text, _ = LAST_ERROR_RU.get(err, (str(err), ""))
                    self.set_system_status("error")
                    self.ui.operationStatusLabel.setText(f"Ошибка: {text}")
                self._last_error_val = err_val
            elif self._last_error_val != 0:
                self._last_error_val = 0
                self._set_cycle_mode(self._cycle_mode)
        except Exception:
            pass

        self._set_actual_speed()

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
        self._set_actual_speed()

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

    def _send_command(self, command_name, payload=None):
        """Only the real robot mode may send commands to the controller."""
        if self._preview:
            return
        from commands import Command, CmdType
        self.cmd_queue.put(Command(getattr(CmdType, command_name), payload or {}, source="GUI"))

    def manipulator_command(self, cmd):
        if not self._preview:
            self.cmd_queue.put(cmd)

    def power_off(self):
        self._send_command("POWER", {"state": 0})

    def pause_drive(self):
        self._send_command("PAUSE")

    def stop_drive(self):
        self._send_command("STOP_MOVE")
        if not self._preview:
            try:
                self.command_handler.set_trajectory(0)
            except Exception:
                pass

    def start(self):
        if self._can_start_cycle():
            self._set_cycle_mode("running")
            self._send_command("AUTO_START")

    def pause_resume(self):
        if self._cycle_mode == "running":
            self._set_cycle_mode("paused")
            self._send_command("AUTO_PAUSE")
        elif self._cycle_mode == "paused":
            self._set_cycle_mode("running")
            self._send_command("AUTO_START")

    def stop(self):
        self._set_cycle_mode("ready")
        self._send_command("AUTO_STOP")

    def set_cell_state(self, cell, state):
        cell.setProperty("cellState", state)
        style = cell.style()
        style.unpolish(cell)
        style.polish(cell)
        cell.update()

    def open_engineer_login(self):
        # No authentication is skipped in production. Preview mode is offline-only.
        if not self._preview and PopupDialogs.show_login(parent=self) != QtWidgets.QDialog.Accepted:
            return

        if self.engineer_window is None:
            self.engineer_window = EngineerWindow(
                None if self._preview else self.RobotController, parent=self
            )
            self.engineer_window.setWindowFlags(QtCore.Qt.Widget)
            self._screens.addWidget(self.engineer_window)
            self.engineer_window.shutdown_requested.connect(
                partial(self.confirm_shutdown, parent=self.engineer_window)
            )
            self.engineer_window.journal_requested.connect(self.open_journal)
            self.engineer_window.exit_requested.connect(
                partial(self._screens.setCurrentWidget, self._operator_page)
            )
            if not self._preview:
                self.RobotController.set_engineer_mode(True)

        self._screens.setCurrentWidget(self.engineer_window)

    def open_journal(self):
        if self.journal_window is None:
            self.journal_window = JournalWindow(self)
            self.journal_window.setWindowFlags(QtCore.Qt.Widget)
            self._screens.addWidget(self.journal_window)
            self.journal_window.shutdown_requested.connect(
                partial(self.confirm_shutdown, parent=self.journal_window)
            )
            self.journal_window.back_requested.connect(self._return_from_journal)

        current = self._screens.currentWidget()
        if current is self.journal_window:
            return
        self._journal_source = current
        self._screens.setCurrentWidget(self.journal_window)

    def _return_from_journal(self):
        target = self._journal_source or self._operator_page
        self._screens.setCurrentWidget(target)
        self._journal_source = None
