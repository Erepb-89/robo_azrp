from PyQt5 import QtCore, QtWidgets
from typing import Dict

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QFrame, \
    QListWidget, QListWidgetItem
from PyQt5.QtGui import QColor
from datetime import datetime

from commands import Command, CmdType, RobotTrajectories, RobotActions, RobotPoints
from config import (POINTS_PATH, TRAJ_PATH, RED_COLOR,
                    LOG_STYLESHEET, LOG_COLOR_NEUTRAL, LOG_COLOR_STOP,
                    LOG_COLOR_CMD, LOG_COLOR_ERROR, LOG_COLOR_SUCCESS,
                    CONN_ONLINE_STYLE, CONN_OFFLINE_STYLE, CONN_INIT_STYLE,
                    STOP_BTN_STYLE, POWER_OFF_BTN_STYLE,
                    POWER_OFF_ACTIVE_STYLE,
                    JOURNAL_COUNT, COMMON_BTN_STYLE,
                    ACTIVATED_BTN_STYLE, LABEL_PADDING, GREEN_BTN_STYLE, MOVE_BTN_STYLE, GRIPPER_BTN_STYLE)

from ui_form import Ui_Form
from utils import atomic_write_json
from trajectory_map_widget import TrajectoryMapWidget
from available_trajectories import available_trajectories as AVAIL_TRAJS
from available_points import available_points as AVAIL_PTS
from states_modes_errors import ControllerState, SafetyStatus, MotionMode, \
    LastError, CONTROLLER_STATE_RU, \
    SAFETY_STATUS_RU, MOTION_MODE_RU, LAST_ERROR_RU


class MainWindow(QMainWindow):
    """
    Класс - основное окно пользователя.
    """

    def __init__(self, robot_controller, cmd_queue, command_handler,
                 heartbeat=None, cmd_log_queue=None):
        super().__init__()
        self.RobotController = robot_controller
        self.cmd_queue = cmd_queue
        self.Waypoints: Dict[str, dict] = {}
        self.Trajectories: Dict[str, dict] = {}
        self._heartbeat = heartbeat
        self._cmd_log_queue = cmd_log_queue  # очередь событий
        self._last_nearest_wp: str = ""
        self._log_last_cmd: str = ""
        self._log_last_traj_state: int = -1
        self._log_last_action_state: int = -1
        self._log_last_gripper_state: int = -1
        self._log_last_shift_gripper_state: int = -1
        self._log_last_err: int = 0  # для детекции новых ошибок
        self._pending_cmd: str = ""  # последняя GUI-команда (для атрибуции ошибки)

        self.manipulator_command(
            Command(CmdType.REFRESH_WAYPOINTS, {}, source="GUI"))
        self.Waypoints = self.RobotController.get_waypoints_snapshot()
        self.Trajectories = self.RobotController.get_trajectories_snapshot()
        self.Actions = self.RobotController.get_actions_snapshot()
        self.command_handler = command_handler
        self.nearest_info = self.RobotController.get_nearest_info()

        self.ZGTimer = QtCore.QTimer()
        self.ZGTimer.setInterval(100)  # мс
        self.ZGTimer.timeout.connect(self._zg_tick)

        self.PowerCheckTimer = QtCore.QTimer()
        self.PowerCheckTimer.timeout.connect(self.update_power_button_state)
        self.PowerCheckTimer.start(1000)

        self.InitUI()

    def InitUI(self):
        """Загружаем конфигурацию окна из дизайнера"""
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.ActivateZG.setCheckable(True)
        self.ui.ActivateZG.toggled.connect(self.manipulator_free_drive)
        self.ui.ActivateSJ.clicked.connect(self.start_simple_joystick)
        self.ui.MoveTrajectory.clicked.connect(self.move_by_selected_trajectory)
        self.ui.ExecuteAction.clicked.connect(self.execute_selected_action)
        self.ui.OutputControl.setCheckable(True)
        self.ui.OutputControl.toggled.connect(self.manipulator_gripper_control)
        self.ui.ShiftGripper.setCheckable(True)
        self.ui.ShiftGripper.toggled.connect(self.manipulator_shift_gripper)
        # self.ui.SavePoint.clicked.connect(self.save_current_position)
        self.ui.AddPointToTrajectory.clicked.connect(self.add_current_point_to_trajectory)
        self.ui.TrajectoriesComboBox.currentTextChanged.connect(self.trajectory_selected)
        self.ui.availableTrajectoriesComboBox.currentTextChanged.connect(self.available_trajectory_selected)
        self.ui.trajListView.clicked.connect(self.on_traj_list_clicked)
        self.ui.actionsListView.clicked.connect(self.on_actions_list_clicked)
        self.ui.StopMove.setStyleSheet(STOP_BTN_STYLE)
        self.ui.PowerOff.setStyleSheet(POWER_OFF_BTN_STYLE)
        self.ui.PowerOn.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.ActivateZG.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.ActivateSJ.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.SavePoint.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.MoveToPoint.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.AddPointToTrajectory.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.MoveTrajectory.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.ExecuteAction.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.OutputControl.setStyleSheet(COMMON_BTN_STYLE)
        self.ui.ShiftGripper.setStyleSheet(COMMON_BTN_STYLE)
        self.update_waypoints_combo_box()
        self.update_available_waypoints_combo_box()
        self.update_trajectories()
        self.update_actions()
        self._init_trajectory_map()
        self.ui.PowerOn.clicked.connect(lambda: self.cmd_queue.put(
            Command(CmdType.POWER, {'state': 1}, source="GUI")
        ))
        self.ui.PowerOff.clicked.connect(self.power_off)
        self.ui.MoveToPoint.clicked.connect(self.move_to_selected_point)
        self.ui.StopMove.clicked.connect(self.stop_drive)

        self.buttons_logging()

        self._init_op_log_tab()
        self._init_status_bar()
        self._init_top_toolbar()
        self.ui.waypointsComboBox.currentTextChanged.connect(self.waypoint_selected)
        self.ui.availableWaypointsComboBox.currentTextChanged.connect(self.available_waypoint_selected)
        try:
            self.ui.SavePoint.clicked.connect(self.save_current_position)
        except Exception as err:
            print(err)
        self.update_available_trajectories_combo_box("pHomePosition")
        self.show()

    def buttons_logging(self):
        """Прямое логирование нажатий кнопок"""
        self.ui.PowerOn.clicked.connect(
            lambda: self._add_log_entry("Питание ВКЛ", "→", LOG_COLOR_NEUTRAL))
        self.ui.MoveToPoint.clicked.connect(
            lambda: self._add_log_entry(
                f"Перемещение: {self.ui.waypointsComboBox.currentData(Qt.ItemDataRole.UserRole) or self.ui.waypointsComboBox.currentText()}",
                "→", LOG_COLOR_NEUTRAL))
        self.ui.ActivateZG.toggled.connect(
            lambda on: self._add_log_entry(
                f"Свободное движение: {'ВКЛ' if on else 'ВЫКЛ'}", "→", LOG_COLOR_NEUTRAL))
        self.ui.OutputControl.toggled.connect(
            lambda on: self._add_log_entry(
                f"Захват: {'ВКЛ' if on else 'ВЫКЛ'}", "→", LOG_COLOR_NEUTRAL))
        self.ui.ShiftGripper.toggled.connect(
            lambda on: self._add_log_entry(
                f"Смещение захвата: {'ВКЛ' if on else 'ВЫКЛ'}", "→", LOG_COLOR_NEUTRAL))

    def _init_top_toolbar(self) -> None:
        """Постоянная верхняя панель с кнопкой СТОП, видимой на всех вкладках."""
        toolbar = self.addToolBar("Аварийная остановка")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        gripper_btn = QtWidgets.QPushButton("Гриппер")
        gripper_btn.setCheckable(True)
        font = gripper_btn.font()
        font.setPointSize(14)
        font.setBold(True)
        gripper_btn.setFont(font)
        gripper_btn.setMinimumHeight(48)
        gripper_btn.setMinimumWidth(160)
        gripper_btn.setStyleSheet(GRIPPER_BTN_STYLE)
        gripper_btn.toggled.connect(self.manipulator_gripper_control)
        toolbar.addWidget(gripper_btn)

        power_off_btn = QtWidgets.QPushButton("⏻  Питание ВЫКЛ")
        power_off_btn.setFont(font)
        power_off_btn.setMinimumHeight(48)
        power_off_btn.setMinimumWidth(180)
        power_off_btn.setStyleSheet(POWER_OFF_BTN_STYLE)
        power_off_btn.clicked.connect(self.power_off)
        toolbar.addWidget(power_off_btn)

        move_to_nearest_btn = QtWidgets.QPushButton("> Двиг. к ближ. точке")
        font = move_to_nearest_btn.font()
        font.setPointSize(14)
        font.setBold(True)
        move_to_nearest_btn.setFont(font)
        move_to_nearest_btn.setMinimumHeight(48)
        move_to_nearest_btn.setMinimumWidth(160)
        move_to_nearest_btn.setStyleSheet(MOVE_BTN_STYLE)
        move_to_nearest_btn.clicked.connect(self.move_to_nearest)
        toolbar.addWidget(move_to_nearest_btn)

        self.exact_dist = QtWidgets.QLineEdit('0.1')
        self.exact_dist.setMinimumSize(QtCore.QSize(28, 28))
        self.exact_dist.setMaximumWidth(60)
        font.setPointSize(14)
        font.setBold(True)
        self.exact_dist.setFont(font)
        self.exact_dist.setObjectName("exactDistance")
        toolbar.addWidget(self.exact_dist)

        self.close_dist = QtWidgets.QLineEdit('0.2')
        self.close_dist.setMinimumSize(QtCore.QSize(28, 28))
        self.close_dist.setMaximumWidth(60)
        font.setPointSize(14)
        font.setBold(True)
        self.close_dist.setFont(font)
        self.close_dist.setObjectName("closeDistance")
        toolbar.addWidget(self.close_dist)

        move_to_btn = QtWidgets.QPushButton("> Двигаться к точке")
        font = move_to_btn.font()
        font.setPointSize(14)
        font.setBold(True)
        move_to_btn.setFont(font)
        move_to_btn.setMinimumHeight(48)
        move_to_btn.setMinimumWidth(160)
        move_to_btn.setStyleSheet(MOVE_BTN_STYLE)
        move_to_btn.clicked.connect(self.move_by_selected_trajectory)
        toolbar.addWidget(move_to_btn)

        stop_btn = QtWidgets.QPushButton("■  СТОП")
        font = stop_btn.font()
        font.setPointSize(14)
        font.setBold(True)
        stop_btn.setFont(font)
        stop_btn.setMinimumHeight(48)
        stop_btn.setMinimumWidth(160)
        stop_btn.setStyleSheet(STOP_BTN_STYLE)
        stop_btn.clicked.connect(self.stop_drive)
        toolbar.addWidget(stop_btn)

    def _init_status_bar(self) -> None:
        """Создаёт постоянную панель статуса робота в нижней строке окна."""
        sb = self.statusBar()
        sb.setSizeGripEnabled(False)

        # --- Индикаторы подключения (левая сторона) ---
        self._conn_labels: Dict[str, QLabel] = {}
        conn_items = [
            ('rc', 'RC'),
            ('handler', 'Handler'),
        ]
        for key, display in conn_items:
            lbl = QLabel(f"● {display}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            lbl.setStyleSheet(CONN_INIT_STYLE)
            sb.addWidget(lbl)
            self._conn_labels[key] = lbl

        # --- Статус робота (правая сторона) ---
        self._lbl_state = QLabel("Состояние: —")
        self._lbl_safety = QLabel("Безопасность: —")
        self._lbl_mode = QLabel("Режим: —")
        self._lbl_error = QLabel("Ошибка: —")

        for lbl in (self._lbl_state, self._lbl_safety, self._lbl_mode, self._lbl_error):
            lbl.setMinimumWidth(180)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            lbl.setStyleSheet(LABEL_PADDING)
            sb.addPermanentWidget(lbl)

        self.StatusTimer = QtCore.QTimer()
        self.StatusTimer.timeout.connect(self._update_status)
        self.StatusTimer.start(500)

    def _update_conn_indicators(self) -> None:
        """Обновляет индикаторы подключения RC и хендлера."""
        # RC и хендлер — через heartbeat
        if self._heartbeat is not None:
            hb = self._heartbeat.state()
            for key in ('rc', 'handler'):
                lbl = self._conn_labels.get(key)
                if lbl is None:
                    continue
                alive = hb.get(key, False)
                lbl.setStyleSheet(
                    CONN_ONLINE_STYLE if alive else CONN_OFFLINE_STYLE
                )

    def _update_nearest(self):
        _ = self.RobotController.find_nearest_waypoint()
        self.nearest_info = self.RobotController.get_nearest_info()
        nearest_wp = (self.nearest_info or {}).get('waypoint') or ""
        if nearest_wp and nearest_wp != self._last_nearest_wp:
            self.update_available_trajectories_combo_box(nearest_wp)
            self.update_available_waypoints_combo_box()
            self._last_nearest_wp = nearest_wp
            self.trajectory_map.set_current_position(self._last_nearest_wp)

    def _update_status(self) -> None:
        """Обновляет метки статуса на основе текущего состояния робота."""
        self._update_conn_indicators()
        try:
            state = self.RobotController.get_state_snapshot()

            cs = state.controller_state
            text, style = CONTROLLER_STATE_RU.get(getattr(ControllerState, cs), (str(cs), ""))
            self._lbl_state.setText(f"Состояние: {text}")
            self._lbl_state.setStyleSheet(LABEL_PADDING + style)

            ss = state.safety_status
            text, style = SAFETY_STATUS_RU.get(getattr(SafetyStatus, ss), (str(ss), ""))
            self._lbl_safety.setText(f"Безопасность: {text}")
            self._lbl_safety.setStyleSheet(LABEL_PADDING + style)

            mode = state.mode
            if mode is not None:
                text, style = MOTION_MODE_RU.get(getattr(MotionMode, mode), (str(mode), ""))
            else:
                text, style = "—", ""
            self._lbl_mode.setText(f"Режим: {text}")
            self._lbl_mode.setStyleSheet(LABEL_PADDING + style)

            err = state.last_error
            if not isinstance(err, LastError):
                try:
                    err = LastError(err)
                except (ValueError, TypeError):
                    err = None
            if err is not None:
                text, style = LAST_ERROR_RU.get(err, (str(err), "background:#ffcdd2"))
            else:
                text, style = "—", ""
            self._lbl_error.setText(f"Ошибка: {text}")
            self._lbl_error.setStyleSheet(LABEL_PADDING + style)

            self._update_nearest()

        except Exception as err:
            pass
            # print(err)

        # ── PLC состояния → карта ─────────────────────────────
        try:
            plat = False

            self.trajectory_map.update_plc_state(plat)

        except Exception:
            pass

        try:
            state = self.RobotController.get_state_snapshot()
            self._update_op_log(
                last_cmd=getattr(state, 'last_command', None) or "",
                trajectory_state=getattr(state, 'trajectory_state', 0) or 0,
                action_state=getattr(state, 'action_state', 0) or 0,
            )
        except Exception:
            pass

        try:
            state = self.RobotController.get_state_snapshot()
            raw_err = state.last_error
            if raw_err is not None:
                err = raw_err if isinstance(raw_err, LastError) else LastError(raw_err)
                err_val = err.value
                if err_val != 0:
                    if err_val != self._log_last_err:
                        err_text, _ = LAST_ERROR_RU.get(err, (str(err), ""))
                        context = f"{self._pending_cmd} — {err_text}" if self._pending_cmd else err_text
                        self._add_log_entry(context, "✗", LOG_COLOR_ERROR)
                    self._log_last_err = err_val
        except Exception:
            pass

        # Команды из очереди (синий цвет, префикс [CMD])
        try:
            if self._cmd_log_queue is not None:
                while not self._cmd_log_queue.empty():
                    msg = self._cmd_log_queue.get_nowait()
                    self._add_log_entry(f"[CMD]  {msg}", "→", LOG_COLOR_CMD)
        except Exception:
            pass

    # ── Журнал операций ───────────────────────────────────────
    def _init_op_log_tab(self) -> None:
        """Добавляет 4 вкладку 'Журнал' с QListWidget последних операций."""
        tab = QtWidgets.QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        hdr = QLabel(f"Журнал операций (последние {JOURNAL_COUNT})")
        hdr.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(hdr)

        self._op_log = QListWidget()
        self._op_log.setSpacing(1)
        self._op_log.setStyleSheet(LOG_STYLESHEET)
        layout.addWidget(self._op_log)

        self.ui.tabWidget.addTab(tab, "Журнал")

    def _add_log_entry(self, command: str, icon: str, fg: str) -> None:
        """Добавляет строку в журнал, удаляет лишние при переполнении."""
        if icon == "→" and not command.startswith("[CMD]"):
            self._pending_cmd = command  # запоминаем для атрибуции возможной ошибки
            self._log_last_cmd = ""  # сбрасываем, чтобы повторная та же команда детектировалась
            self._log_last_err = 0  # сбрасываем ошибку в 0, чтобы та же ошибка снова отобразилась
        ts = datetime.now().strftime("%H:%M:%S")
        text = f"{ts}  {icon}  {command}"
        item = QListWidgetItem(text)
        item.setForeground(QColor(fg))
        self._op_log.insertItem(0, item)
        while self._op_log.count() > JOURNAL_COUNT:
            self._op_log.takeItem(self._op_log.count() - 1)

    def _update_op_log(self, last_cmd: str, trajectory_state: int, action_state: int,
                       gripper_state: int = 0, shift_gripper_state: int = 0) -> None:
        """
        Добавляет запись о результате команды при изменении состояния.
        Поддерживает траектории, действия, основной схват и сдвиг схвата.
        """
        cmd_changed = last_cmd != self._log_last_cmd
        traj_changed = trajectory_state != self._log_last_traj_state
        action_changed = action_state != self._log_last_action_state
        gripper_changed = gripper_state != self._log_last_gripper_state
        shift_gripper_changed = shift_gripper_state != self._log_last_shift_gripper_state

        if not (cmd_changed or traj_changed or action_changed or
                gripper_changed or shift_gripper_changed):
            return

        # Сохраняем предыдущие состояния
        prev_traj = self._log_last_traj_state
        prev_action = self._log_last_action_state
        prev_gripper = self._log_last_gripper_state
        prev_shift = self._log_last_shift_gripper_state
        prev_cmd = self._log_last_cmd

        # Обновляем текущие состояния
        self._log_last_traj_state = trajectory_state
        self._log_last_action_state = action_state
        self._log_last_gripper_state = gripper_state
        self._log_last_shift_gripper_state = shift_gripper_state
        self._log_last_cmd = last_cmd

        label = self._pending_cmd or last_cmd or prev_cmd

        def _handle_state(prev: int, current: int, code_label: str) -> bool:
            """Обрабатывает переход состояния в терминальную зону. Возвращает True если переход был."""
            if prev < 2000 and 2000 <= current < 3000:  # EXECUTION → FINISHED
                self._add_log_entry(label, "✓", LOG_COLOR_SUCCESS)
                QtWidgets.QMessageBox.information(self, "Выполнено", f"✓  {label}")
                self._pending_cmd = ""
                return True
            elif prev < 3000 and 3000 <= current < 4000:  # EXECUTION → EXCEPTION
                self._add_log_entry(label, f"✗  ошибка ({code_label} {current})", LOG_COLOR_ERROR)
                self._pending_cmd = ""
                return True
            elif prev < 4000 and current >= 4000:  # EXECUTION → BLOCK
                self._add_log_entry(label, "✗  заблокировано", LOG_COLOR_ERROR)
                self._pending_cmd = ""
                return True
            return False

        handled = False
        if traj_changed and not handled:
            handled = _handle_state(prev_traj, trajectory_state, "traj")

        if action_changed and not handled:
            handled = _handle_state(prev_action, action_state, "action")

        if gripper_changed and not handled:
            handled = _handle_state(prev_gripper, gripper_state, "gripper")

        if shift_gripper_changed and not handled:
            handled = _handle_state(prev_shift, shift_gripper_state, "shift")

        # Не-траекторная команда (PowerOn/Off, MoveToPoint…):
        # last_command обновляется ПОСЛЕ успешного выполнения → это подтверждение "✓"
        if not handled and cmd_changed and last_cmd and \
                trajectory_state < 100 and action_state < 100 and \
                gripper_state < 100 and shift_gripper_state < 100:
            self._add_log_entry(self._pending_cmd or last_cmd, "✓", LOG_COLOR_SUCCESS)
            self._pending_cmd = ""

    def _init_trajectory_map(self) -> None:
        """Встраивает TrajectoryMapWidget в плейсхолдер 3 вкладки."""
        placeholder = self.ui.trajectoryMapPlaceholder
        layout = QVBoxLayout(placeholder)
        layout.setContentsMargins(0, 0, 0, 0)

        self.trajectory_map = TrajectoryMapWidget(placeholder)
        layout.addWidget(self.trajectory_map)

        # Клик по узлу → выбрать точку в комбобоксе Tab 1
        self.trajectory_map.node_clicked.connect(self._on_map_node_clicked)

        # Обновляем карту при смене вкладки
        self.ui.tabWidget.currentChanged.connect(self._on_tab_changed)

    def _on_map_node_clicked(self, point_name: str) -> None:
        """
        Клик по узлу карты:
        - выбирает точку в комбобоксе Tab 1
        - если текущая позиция известна, ищет прямую траекторию и подсвечивает ребро
        - синхронизирует выбор траектории с TrajectoriesComboBox Tab 1
        - Оператор видит подсветку на карте
        """
        # Синхронизация точки с Tab 1 (поиск по внутреннему имени в UserRole)
        model = self.ui.waypointsComboBox.model()
        index = next(
            (i for i in range(model.rowCount())
             if model.item(i).data(Qt.ItemDataRole.UserRole) == point_name),
            -1
        )
        if index >= 0:
            self.ui.waypointsComboBox.setCurrentIndex(index)

        src = self.trajectory_map._current_point
        if not src or src == point_name:
            return

        traj_name = self._find_direct_trajectory(src, point_name)
        if traj_name:
            # Подсветка ребра на карте
            self.trajectory_map.highlight_trajectory(src, point_name, traj_name)
            # Синхронизация с TrajectoriesComboBox и TrajectoryName на Tab 1
            tmodel = self.ui.TrajectoriesComboBox.model()
            tidx = next(
                (i for i in range(tmodel.rowCount())
                 if tmodel.item(i).data(Qt.ItemDataRole.UserRole) == traj_name),
                -1
            )
            if tidx >= 0:
                self.ui.TrajectoriesComboBox.setCurrentIndex(tidx)
            self.ui.TrajectoryName.setText(traj_name)
        else:
            # Сброс подсветки ребер на карте
            self.trajectory_map.reset_highlight()
            self.trajectory_map._info_label.setText(
                f"Нет прямой траектории: {src} → {point_name}")
            self.trajectory_map._info_label.setStyleSheet(
                RED_COLOR)

    def _find_direct_trajectory(self, src: str, dst: str) -> str | None:
        """
        Ищет прямую траекторию между src и dst через available_trajectories.
        Проверяет оба направления: src→dst и dst→src.
        """
        dst_short = dst[1:] if dst.startswith('p') else dst
        src_short = src[1:] if src.startswith('p') else src

        state = self.RobotController.get_state_snapshot()
        # Прямое направление: из src в dst
        try:
            for traj in AVAIL_TRAJS.get(src):
                if f"_To_{dst_short}" in traj and traj in self.Trajectories:
                    return traj

            # Обратное направление: из dst в src
            for traj in AVAIL_TRAJS.get(dst):
                if f"_To_{src_short}" in traj and traj in self.Trajectories:
                    return traj

        except Exception as err:
            pass

        return None

    def _on_tab_changed(self, index: int) -> None:
        """При переходе на вкладку карты — обновляем текущую позицию."""
        if index == 2:
            try:
                nearest_data = self.RobotController.find_nearest_waypoint()
                nearest_wp = (nearest_data or {}).get('waypoint') or ''
                if nearest_wp:
                    self.trajectory_map.set_current_position(nearest_wp)
            except Exception:
                pass
        else:
            # Уходим с карты — сбрасываем подсветку рёбер
            if hasattr(self, 'trajectory_map'):
                self.trajectory_map.reset_highlight()

    def move_to_nearest(self):
        self.nearest_info = self.RobotController.get_nearest_info()
        self.RobotController.log.info(
            f"Nearest waypoint: {self.nearest_info.get('waypoint')}; "
            f"distance={self.nearest_info.get('distance'):.3f}; "
            f"trajectories={self.nearest_info.get('trajectories')}"
        )

        motion = "line" if self.ui.chkLineMotion.isChecked() else "joint"
        # print("_last_nearest_wp", self._last_nearest_wp)

        if float(self.nearest_info.get('distance')) < float(self.exact_dist.text()):
            self.manipulator_command(
                Command(CmdType.MOVE_TO_POINT,
                        {'name': self._last_nearest_wp, 'motion': motion},
                        source="GUI"))
        else:
            print('Distance too long')
            self.RobotController.log.info(
                f"Distance to nearest waypoint: {self.nearest_info.get('waypoint')} "
                f"={self.nearest_info.get('distance'):.2f} too long"
            )

    def update_power_button_state(self) -> None:
        is_running = (self.RobotController.get_controller_state() == 'run')
        if is_running:
            self.ui.PowerOn.setStyleSheet(GREEN_BTN_STYLE)  # POWER_ON_ACTIVE_STYLE
            self.ui.PowerOff.setStyleSheet(POWER_OFF_BTN_STYLE)  # POWER_BTN_INACTIVE_STYLE
        else:
            self.ui.PowerOn.setStyleSheet(COMMON_BTN_STYLE)  # POWER_BTN_INACTIVE_STYLE
            self.ui.PowerOff.setStyleSheet(POWER_OFF_ACTIVE_STYLE)

    def save_waypoints(self) -> bool:
        try:
            waypoints_list = list(self.Waypoints.values())
            atomic_write_json(POINTS_PATH, {"waypoints": waypoints_list})
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error",
                                           f"Failed to save waypoints: {e}")
            return False

    def save_trajectories(self) -> bool:
        try:
            trajectories_list = list(self.Trajectories.values())
            atomic_write_json(TRAJ_PATH, {"trajectories": trajectories_list})
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error",
                                           f"Failed to save trajectories: {e}")
            return False

    def update_available_waypoints_combo_box(self) -> None:
        try:
            current_point = self.nearest_info.get('waypoint')
            items_model = QStandardItemModel()

            for point in AVAIL_PTS.get(current_point):
                item = QStandardItem(point)
                item.setData(point, Qt.ItemDataRole.UserRole)
                item.setEditable(False)
                items_model.appendRow(item)
            self.ui.availableWaypointsComboBox.setModel(items_model)
        except Exception as err:
            print(err)

    def update_available_trajectories_combo_box(self, target_point) -> None:
        self.nearest_info = self.RobotController.get_nearest_info()

        try:
            if float(self.nearest_info.get('distance')) < float(self.exact_dist.text()):
                current_point = self.nearest_info.get('waypoint')
                self.RobotController.state.update(current_point=getattr(RobotPoints, current_point).value)
                st = self.RobotController.get_state_snapshot()
                traj = self._find_direct_trajectory(current_point, target_point)

                items_model = QStandardItemModel()
                item = QStandardItem(traj)
                item.setData(traj, Qt.ItemDataRole.UserRole)
                item.setEditable(False)
                items_model.appendRow(item)
                self.ui.availableTrajectoriesComboBox.setModel(items_model)

            elif float(self.nearest_info.get('distance')) < float(self.close_dist.text()):
                current_point = self.nearest_info.get('waypoint')
                self.RobotController.state.update(current_point=getattr(RobotPoints, current_point).value + 1)
                st = self.RobotController.get_state_snapshot()
        except Exception as err:
            print(err)

    def update_waypoints_combo_box(self) -> None:
        items_model = QStandardItemModel()
        last_index = len(self.Waypoints) - 1
        for point in self.Waypoints.keys():
            item = QStandardItem(point)
            item.setData(point, Qt.ItemDataRole.UserRole)
            item.setEditable(False)
            items_model.appendRow(item)
        self.ui.waypointsComboBox.setModel(items_model)
        self.ui.waypointsComboBox.setCurrentIndex(last_index)

    def update_trajectories(self) -> None:
        items_model = QStandardItemModel()
        last_index = len(self.Trajectories) - 1
        for traj in self.Trajectories.keys():
            item = QStandardItem(traj)
            item.setData(traj, Qt.ItemDataRole.UserRole)
            item.setEditable(False)
            items_model.appendRow(item)
        self.ui.TrajectoriesComboBox.setModel(items_model)
        self.ui.trajListView.setModel(items_model)
        self.ui.TrajectoriesComboBox.setCurrentIndex(last_index)

    def update_actions(self) -> None:
        items_model = QStandardItemModel()
        for action in self.Actions.keys():
            item = QStandardItem(action)
            item.setData(action, Qt.ItemDataRole.UserRole)
            item.setEditable(False)
            items_model.appendRow(item)
        self.ui.actionsListView.setModel(items_model)

    def on_traj_list_clicked(self) -> None:
        index = self.ui.trajListView.currentIndex()
        internal = index.data(Qt.ItemDataRole.UserRole) or index.data()
        self.ui.TrajectoryName.setText(internal)

    def on_actions_list_clicked(self) -> None:
        index = self.ui.actionsListView.currentIndex()
        internal = index.data(Qt.ItemDataRole.UserRole) or index.data()
        self.ui.ActionName.setText(internal)

    def trajectory_selected(self, _display_name) -> None:
        internal = self.ui.TrajectoriesComboBox.currentData(Qt.UserRole)
        self.ui.TrajectoryName.setText(internal)

    def available_trajectory_selected(self, _display_name) -> None:
        internal = self.ui.availableTrajectoriesComboBox.currentData(Qt.ItemDataRole.UserRole)
        self.ui.TrajectoryName.setText(internal)

    def available_waypoint_selected(self, _display_name) -> None:
        point_name = self.ui.availableWaypointsComboBox.currentData(Qt.ItemDataRole.UserRole) or _display_name
        self.update_available_trajectories_combo_box(point_name)

        # self.ui.PointName.setText(point_name) # comment
        if point_name in self.Waypoints:
            wp = self.Waypoints[point_name]
            self.ui.SetSpeed.setText(str(wp.get('speed', 0.5)))
            self.ui.SetAccel.setText(str(wp.get('accel', 0.5)))
            self.ui.SetBlend.setText(str(wp.get('blend', 0.0)))

    def waypoint_selected(self, _display_name) -> None:
        point_name = self.ui.waypointsComboBox.currentData(Qt.ItemDataRole.UserRole) or _display_name
        self.update_available_waypoints_combo_box()
        self.update_available_trajectories_combo_box(point_name)
        self.available_trajectory_selected(_display_name)

        self.ui.PointName.setText(point_name)
        if point_name in self.Waypoints:
            wp = self.Waypoints[point_name]
            self.ui.SetSpeed.setText(str(wp.get('speed', 0.5)))
            self.ui.SetAccel.setText(str(wp.get('accel', 0.5)))
            self.ui.SetBlend.setText(str(wp.get('blend', 0.0)))

    # def trajectory_selected(self, trajectory_name):
    #     print(trajectory_name)

    def manipulator_command(self, cmd: Command) -> None:
        self.cmd_queue.put(cmd)

    def manipulator_gripper_control(self, clamp: bool) -> None:
        try:
            self.manipulator_command(
                Command(CmdType.GRIPPER_CMD, {'index': 0, 'value': clamp}, source="GUI"))
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "I/O error",
                                           f"Не удалось изменить состояние DO0: {e}")
            self.ui.OutputControl.setChecked(False)

    def manipulator_shift_gripper(self, shift: bool) -> None:
        try:
            self.manipulator_command(
                Command(CmdType.GRIPPER_CMD, {'index': 1, 'value': shift}, source="GUI"))
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "I/O error",
                                           f"Не удалось изменить состояние DO1: {e}")
            # self.ui.ShiftGripper.setChecked(False)

    def manipulator_free_drive(self, activate: bool) -> None:  # 2025_09_29
        try:
            self._log_last_err = 0
            if activate:
                self.ui.ActivateZG.setStyleSheet(ACTIVATED_BTN_STYLE)
                self.manipulator_command(
                    Command(CmdType.FREE_DRIVE, {'state': 1}, source="GUI")
                )
                if not self.ZGTimer.isActive():
                    self.ZGTimer.start()
            else:
                self.ui.ActivateZG.setStyleSheet(COMMON_BTN_STYLE)
                self.manipulator_command(
                    Command(CmdType.FREE_DRIVE, {'state': 2}, source="GUI")
                )
                self.ZGTimer.stop()
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error",
                                           f"Zero Gravity toggle failed: {e}")
            self.ui.ActivateZG.setChecked(False)
            if self.ZGTimer.isActive():
                self.ZGTimer.stop()

    def add_current_point_to_trajectory(self) -> None:
        point_name = self.ui.PointName.text().strip()
        if not point_name:
            QtWidgets.QMessageBox.warning(None, "Warning",
                                          "Please select existing point!")
            return

        trajectory_name = self.ui.TrajectoryName.text().strip()
        if not trajectory_name:
            QtWidgets.QMessageBox.warning(None, "Warning",
                                          "Please select trajectory!")
            return

        if point_name in self.Waypoints and trajectory_name in self.Trajectories:
            positions = self.Trajectories[trajectory_name].get('positions')
            positions.append({'name': point_name, 'motion': 'joint'})

            new_trajectory = {
                "name": trajectory_name,
                "positions": positions
            }

            self.Trajectories[trajectory_name] = new_trajectory
            if self.save_trajectories():
                QtWidgets.QMessageBox.information(
                    None,
                    "Success",
                    f"Point '{point_name}' successfully added to trajectory {trajectory_name}!")

    def save_current_position(self) -> None:
        point_name = self.ui.PointName.text().strip()
        if not point_name:
            QtWidgets.QMessageBox.warning(None, "Warning",
                                          "Please enter point name!")
            return

        try:
            tcp_position = self.RobotController.get_current_tcp_position()
            joint_position = self.RobotController.get_current_joint_position()
            speed = float(self.ui.SetSpeed.text())
            accel = float(self.ui.SetAccel.text())
            blend = float(self.ui.SetBlend.text())

            new_point = {
                "name": point_name,
                "speed": speed,
                "accel": accel,
                "blend": blend,
                "tcp": {
                    "x": tcp_position[0],
                    "y": tcp_position[1],
                    "z": tcp_position[2],
                    "Rx": tcp_position[3],
                    "Ry": tcp_position[4],
                    "Rz": tcp_position[5]
                },
                "joints": {
                    "J1": joint_position[0],
                    "J2": joint_position[1],
                    "J3": joint_position[2],
                    "J4": joint_position[3],
                    "J5": joint_position[4],
                    "J6": joint_position[5]
                }
            }

            self.Waypoints[point_name] = new_point

            if self.save_waypoints():
                self.update_waypoints_combo_box()
                QtWidgets.QMessageBox.information(None, "Success",
                                                  f"Point '{point_name}' saved successfully!")
        except ValueError:
            QtWidgets.QMessageBox.warning(None, "Warning",
                                          "Please enter valid parameters!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error",
                                           f"Failed to save point: {e}")

    def stop_drive(self) -> None:
        self._add_log_entry("Стоп", "→", LOG_COLOR_STOP)
        self.manipulator_command(
            Command(CmdType.STOP_MOVE, {}, source="GUI"))
        self.command_handler.set_trajectory(0)

    def power_off(self) -> None:
        self._add_log_entry("Питание ВЫКЛ", "→", LOG_COLOR_NEUTRAL)
        self.cmd_queue.put(Command(CmdType.POWER, {'state': 0}, source="GUI"))

    def move_to_selected_point(self) -> None:
        point_name = self.ui.PointName.text().strip()
        if not point_name:
            QtWidgets.QMessageBox.warning(None, "Warning",
                                          "Please select a point first!")
            return
        try:
            self.manipulator_command(
                Command(CmdType.REFRESH_WAYPOINTS, {}, source="GUI"))
            motion = "line" if self.ui.chkLineMotion.isChecked() else "joint"
            self.manipulator_command(
                Command(CmdType.MOVE_TO_POINT,
                        {'name': point_name, 'motion': motion},
                        source="GUI"))

            # QtWidgets.QMessageBox.information(None, "Success",
            #                                   f"Moving to point '{point_name}'")
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error",
                                           f"Failed to move to point: {e}")

    def move_by_selected_trajectory(self) -> None:
        trajectory_name = self.ui.TrajectoryName.text()
        if not trajectory_name:
            QtWidgets.QMessageBox.warning(None, "Warning",
                                          "Please select a trajectory first!")
            return

        state = self.RobotController.get_state_snapshot()
        if state.controller_state != 'run':
            self._add_log_entry(f"Траектория: {trajectory_name}", "✗  не готов", LOG_COLOR_ERROR)
            return

        try:
            traj_enum = getattr(RobotTrajectories, trajectory_name)
            self.command_handler.set_trajectory(traj_enum.value)
            self._add_log_entry(f"Траектория: {trajectory_name}", "→", LOG_COLOR_NEUTRAL)
        except Exception as e:
            self._add_log_entry(f"Траектория: {trajectory_name}", f"✗  CMD: {e}", LOG_COLOR_ERROR)

    def execute_selected_action(self) -> None:
        action_name = self.ui.ActionName.text()
        if not action_name:
            QtWidgets.QMessageBox.warning(None, "Warning",
                                          "Please select an action first!")
            return

        state = self.RobotController.get_state_snapshot()
        if state.controller_state != 'run':
            self._add_log_entry(f"Действие: {action_name}", "✗  не готов", LOG_COLOR_ERROR)
            return

        try:
            # команда через хендлер
            action_enum = getattr(RobotActions, action_name)
            self.command_handler.set_action(action_enum.value)
            self._add_log_entry(f"Действие: {action_name}", "→", LOG_COLOR_NEUTRAL)
        except Exception as e:
            self._add_log_entry(f"Действие: {action_name}", f"✗  CMD: {e}", LOG_COLOR_ERROR)

    def _zg_tick(self) -> None:  # 2025_09_29
        try:
            if self.ui.ActivateZG.isChecked():
                self.manipulator_command(
                    Command(CmdType.FREE_DRIVE, {'state': 1}, source="GUI")
                )
            else:
                self.manipulator_command(
                    Command(CmdType.FREE_DRIVE, {'state': 2}, source="GUI")
                )
                self.ZGTimer.stop()
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error",
                                           f"Zero Gravity periodic toggle failed: {e}")
            self.ui.ActivateZG.setChecked(False)
            self.ZGTimer.stop()

    def start_simple_joystick(self) -> None:
        try:
            self._log_last_err = 0
            self.manipulator_command(
                Command(CmdType.START_SIMPLE_JOYSTICK,
                        {'coord_sys': None}, source="GUI"))
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error",
                                           f"Failed to start simple joystick: {e}")
