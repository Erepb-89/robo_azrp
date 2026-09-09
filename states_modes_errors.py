from enum import Enum


class ControllerState(Enum):
    """
    Состояния контроллера.
    Доступные состояния контроллера:
        'idle' — Начальное состояние контроллера.
        'off' — Контроллер выключен.
        'stby' — Промежуточное состояние.
        'on' — Контроллер включен. Тормоза активированы.
            Если робот в состоянии 'run', ставит робота на тормоза.
            Если робот в состоянии 'off', включает робота, не снимая его с
            тормозов.
        'run' — Контроллер включен. Тормоза деактивированы.
        'calibration' — Вычисление смещения (для сохранения позиции робота
            после перезагрузки).
        'failure' — Фатальная ошибка контроллера.
        'force_exit' — Принудительное завершение работы ядра.

    При использовании 'on' и 'off', все имеющиеся целевые точки в памяти робота
        удаляются.
    """
    idle = 0
    off = 1
    stby = 2
    on = 3
    run = 4
    calibration = 5
    failure = 6
    force_exit = 7


class SafetyStatus(Enum):
    """
        Доступные статусы безопасности:
        'deinit' — Робот не инициализирован. Доступных операций нет.
        'recovery' — Нарушение ограничений в момент старта.
            Доступные методы перемещения: 'FreeDrive', 'Jogging'.
        'normal' — Рабочее состояние. Применены стандартные ограничения
            безопасности.
        'reduced' — Рабочее состояние. Применены повышенные ограничения
            безопасности.
            Снижена скорость.
        'safeguard_stop' — Экстренная останова 2-й категории, по нажатию кнопки
            безопасности.
            Без использования тормозов, с сохранением траектории.
        'emergency_stop' — Экстренная останова 1-й категории, по нажатию кнопки
            экстренного останова. С использованием тормозов, без сохранения
            траектории.
        'fault' — Экстренная останова 0-й категории, по причине внутренней
            ошибки робота. Отключение питания.
        'violation' — Экстренная останова 0-й категории, по причине нарушения
            ограничений безопасности. Отключение питания.
    """
    deinit = 0
    recovery = 1
    normal = 2
    reduced = 3
    safeguard_stop = 4
    emergency_stop = 5
    fault = 6
    violation = 7


class MotionMode(Enum):
    """
    Режимы движения робота.
    В режиме 'hold' недоступен режим 'pause'.

    Доступные режимы движения:
        'hold' — Удержание позиции. (Сброс траектории).
        'pause' — Удержание позиции. (Сохранение траектории).
        'move' — Начать/продолжить выполнение заданной траектории.
        'zero_gravity' — Режим FreeDrive (ручное управление).
            (Сброс траектории).
        'jog' — Декартовый джоггинг (джоггинг ЦТИ). (Сброс траектории).
        'joint_jog' — Моторный джоггинг (джоггинг каждым мотором в
            отдельности). (Сброс траектории).
    """
    no_func: int = 0
    move: int = 1
    hold: int = 2
    pause: int = 3
    zero_gravity: int = 4
    run: int = 5
    move_to_home: int = 6


class LastError(Enum):
    """Последняя ошибка контроллера робота."""
    no_errors: int = 0
    err_switching_power_state: int = 1  # Timeout switching controller power state
    err_power_control: int = 2          # Error in ManipulatorPowerControl
    err_switching_stop_mode: int = 3    # Stop Mode Switching Error
    err_switching_run_mode: int = 4     # Run Mode Switching Error
    err_switching_zero_gravity: int = 5 # Zero Gravity Mode Switching Error
    err_choose_trajectory: int = 6      # Manipulator can't be moved by the selected trajectory from current point!
    err_waypoint: int = 7               # Add waypoint error
    err_timeout_trajectory: int = 8     # Timeout while executing trajectory
    err_common_trajectory: int = 9      # EXECUTE_TRAJECTORY failed
    # сделать обработку
    err_timeout_action: int = 10        # Timeout while executing action
    err_common_action: int = 11         # EXECUTE_ACTION failed
    err_check_state: int = 12           # CheckControllerState error
    err_rc_loop: int = 13               # Unhandled error in Robot Controller loop
    err_not_ready: int = 14             # Manipulator not powered / not in run state
    err_sj_activation: int = 15         # Error Simple Joystick activation
    err_hatch_not_open: int = 16        # Hatch must be open before moving to this position
    err_vtol_lift_not_position: int = 17  # VTOL table lift must be in bottom position before approach
    err_gripper_cmd : int = 18          # GRIPPER_CMD failed
    err_shift_gripper_cmd : int = 19    # SHIFT_GRIPPER_CMD failed


# ── Словари русских переводов для панели статуса ──────────────────────────────
CONTROLLER_STATE_RU = {
    ControllerState.idle:        ("Инициализация",        "background:#e0e0e0"),
    ControllerState.off:         ("Выключен",             "background:#ffcdd2"),
    ControllerState.stby:        ("Готовность",           "background:#fff9c4"),
    ControllerState.on:          ("Включён",              "background:#bbdefb"),
    ControllerState.run:         ("Работает",             "background:#c8e6c9"),
    ControllerState.calibration: ("Калибровка",           "background:#e1bee7"),
    ControllerState.failure:     ("ОШИБКА",               "background:#f44336;color:white;font-weight:bold"),
    ControllerState.force_exit:  ("Аварийное завершение", "background:#f44336;color:white"),
}

SAFETY_STATUS_RU = {
    SafetyStatus.deinit:         ("Не инициализирован",    "background:#e0e0e0"),
    SafetyStatus.recovery:       ("Восстановление",        "background:#fff9c4"),
    SafetyStatus.normal:         ("Норма",                 "background:#c8e6c9"),
    SafetyStatus.reduced:        ("Снижена скорость",      "background:#fff9c4"),
    SafetyStatus.safeguard_stop: ("Стоп безопасности",     "background:#ffcdd2"),
    SafetyStatus.emergency_stop: ("АВАРИЙНАЯ ОСТАНОВКА",   "background:#f44336;color:white;font-weight:bold"),
    SafetyStatus.fault:          ("ОТКАЗ",                 "background:#f44336;color:white;font-weight:bold"),
    SafetyStatus.violation:      ("НАРУШЕНИЕ",             "background:#f44336;color:white;font-weight:bold"),
}

MOTION_MODE_RU = {
    MotionMode.no_func:      ("—",                            ""),
    MotionMode.move:         ("Движение",                     "background:#bbdefb"),
    MotionMode.hold:         ("Удержание. Сброс траектории",  "background:#fff9c4"),
    MotionMode.pause:        ("Пауза. Сохранение траектории", "background:#fff9c4"),
    MotionMode.zero_gravity: ("Cвободное движение",           "background:#e1bee7"),
    MotionMode.run:          ("Выполнение",                   "background:#bbdefb"),
    MotionMode.move_to_home: ("→ Домой",                      "background:#bbdefb"),
}

LAST_ERROR_RU = {
    LastError.no_errors:                 ("Нет ошибок",                         "background:#c8e6c9"),
    LastError.err_switching_power_state: ("Тайм-аут смены питания",             "background:#ffcdd2"),
    LastError.err_power_control:         ("Ошибка управления питанием",         "background:#ffcdd2"),
    LastError.err_switching_stop_mode:   ("Ошибка перехода в стоп",             "background:#ffcdd2"),
    LastError.err_switching_run_mode:    ("Ошибка перехода в рабочий режим",    "background:#ffcdd2"),
    LastError.err_switching_zero_gravity:("Ошибка вкл-я свободного движения",   "background:#ffcdd2"),
    LastError.err_choose_trajectory:     ("Траектория недоступна",              "background:#ffcdd2"),
    LastError.err_waypoint:              ("Ошибка точки маршрута",              "background:#ffcdd2"),
    LastError.err_timeout_trajectory:    ("Тайм-аут траектории",                "background:#ffcdd2"),
    LastError.err_common_trajectory:     ("Ошибка выполнения траектории",       "background:#ffcdd2"),
    LastError.err_timeout_action:        ("Тайм-аут действия",                  "background:#ffcdd2"),
    LastError.err_check_state:           ("Ошибка проверки состояния",          "background:#ffcdd2"),
    LastError.err_rc_loop:               ("Необработанная ошибка цикла RC",     "background:#ffcdd2"),
    LastError.err_not_ready:             ("Манипулятор не готов к движению",    "background:#ffcdd2"),
    LastError.err_sj_activation:         ("Ошибка включения джойстика",         "background:#ffcdd2"),
    LastError.err_hatch_not_open:        ("Люк не открыт",                      "background:#ffcdd2"),
    LastError.err_vtol_lift_not_position:("Стол ВТОЛ не в нижней позиции",      "background:#ffcdd2"),
}
