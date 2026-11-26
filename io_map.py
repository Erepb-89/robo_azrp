"""
Карта физических сигналов контроллера (DI/DO).
«Блок-схема общая (26.09.28).vsdx».
"""
from enum import IntEnum
from typing import Dict, NamedTuple


class DI(IntEnum):
    """Порты ввода контроллера."""
    Check_Button = 0 # Сигнал с кнопки юстировки
    M1_DoorOpened = 1 # Станок 1. Дверь открыта
    M1_DoorClosed = 2 # Станок 1. Дверь закрыта
    M1_Ready = 3 # Станок 1 готов к загрузке/выгрузке
    M1_ChuckClamped = 4 # Станок 1. Патрон закрыт
    M1_ChuckRelaxed = 5 # Станок 1. Патрон открыт
    M1_Alarm = 6 # Станок 1. Сигнал об ошибке
    M2_Alarm = 7 # Станок 2. Сигнал об ошибке
    M2_DoorOpened = 8 # Станок 2. Дверь открыта
    M2_DoorClosed = 9 # Станок 2. Дверь закрыта
    M2_Ready = 10 # Станок 2 готов к загрузке/выгрузке
    M2_ChuckClamped = 11 # Станок 2. Патрон закрыт
    M2_ChuckRelaxed = 12 # Станок 2. Патрон открыт
    G1_Clamped = 13 # Гриппер 1 закрыт
    G1_Relaxed = 14 # Гриппер 1 открыт
    G2_Clamped = 15 # Гриппер 2 закрыт
    G2_Relaxed = 16 # Гриппер 2 открыт
    Gate_Sensor = 17 # Сигнал с калитки
    S1_Opened = 18 # Полка 1 выдвинута
    S2_Opened = 19 # Полка 2 выдвинута
    S3_Opened = 20 # Полка 3 выдвинута
    S1_Closed = 21 # Полка 1 задвинута
    S2_Closed = 22 # Полка 2 задвинута
    S3_Closed = 23 # Полка 3 задвинута


DI_DESC: Dict[DI, str] = {
    DI.Check_Button: "Сигнал с кнопки юстировки",
    DI.M1_DoorOpened: "М1: дверь открыта",
    DI.M1_DoorClosed: "М1: дверь закрыта",
    DI.M1_Ready: "М1: готов к загрузке",
    DI.M1_ChuckClamped: "М1: патрон закрыт",
    DI.M1_ChuckRelaxed: "М1: патрон открыт",
    DI.M1_Alarm: "Станок 1. Сигнал об ошибке",
    DI.M2_Alarm: "Станок 2. Сигнал об ошибке",
    DI.M2_DoorOpened: "М2: дверь открыта",
    DI.M2_DoorClosed: "М2: дверь закрыта",
    DI.M2_Ready: "М2: готов к загрузке",
    DI.M2_ChuckClamped: "М2: патрон закрыт",
    DI.M2_ChuckRelaxed: "М2: патрон открыт",
    DI.G1_Clamped: "Гриппер 1: закрыт",
    DI.G1_Relaxed: "Гриппер 1: открыт",
    DI.G2_Clamped: "Гриппер 2: закрыт",
    DI.G2_Relaxed: "Гриппер 2: открыт",
    DI.Gate_Sensor: "Калитка задвинута",
    DI.S1_Opened: "Полка 1 выдвинута",
    DI.S2_Opened: "Полка 2 выдвинута",
    DI.S3_Opened: "Полка 3 выдвинута",
    DI.S1_Closed: "Полка 1 задвинута",
    DI.S2_Closed: "Полка 2 задвинута",
    DI.S3_Closed: "Полка 3 задвинута",
}

# Modbus signals
class DIModbus(IntEnum):
    """Порты ввода Modbus модуля Reallab."""
    START_STOP = 0  # Старт/стоп работы робота («START/STOP»)
    M1_DoorAuto = 1  # Станок 1. Дверь в автоматическом режиме
    M2_DoorAuto = 2  # Станок 2. Дверь в автоматическом режиме
    Pause_Resume = 3  # Пауза/Продолжить
    C1_SensorOpened = 4  # Сигнал с концевика Поршень 1 открыт
    C1_SensorClosed = 5  # Сигнал с концевика Поршень 1 закрыт
    C2_SensorOpened = 6  # Сигнал с концевика Поршень 2 открыт
    C2_SensorClosed = 7  # Сигнал с концевика Поршень 2 закрыт
    C_Sensor = 8  # Тележка установлена


DI_MODBUS_DESC: Dict[DIModbus, str] = {
    DIModbus.START_STOP: "Старт/стоп работы робота («START/STOP»)",
    DIModbus.M1_DoorAuto: "М1: дверь в авто-режиме",
    DIModbus.M2_DoorAuto: "М2: дверь в авто-режиме",
    DIModbus.Pause_Resume: "Пауза/Продолжить",
    DIModbus.C1_SensorOpened: "Сигнал с концевика Поршень 1 открыт",
    DIModbus.C1_SensorClosed: "Сигнал с концевика Поршень 1 закрыт",
    DIModbus.C2_SensorOpened: "Сигнал с концевика Поршень 2 открыт",
    DIModbus.C2_SensorClosed: "Сигнал с концевика Поршень 2 закрыт",
    DIModbus.C_Sensor: "Тележка установлена",
}


class DO(IntEnum):
    """Порты вывода контроллера.""" # актуальные
    M1_ChuckOpen = 0  # Станок 1. Открытие патрона (захвата станка)
    M1_ChuckClose = 1  # Станок 1. Закрытие патрона (захвата станка)
    M1_StartProcess = 2  # Станок 1. Старт обработки
    M1_StopProcess = 3  # Станок 1. Завершение обработки
    M1_DoorClose = 4  # Станок 1. Закрыть дверь в автоматическом режиме от робота
    M1_DoorOpen = 5  # Станок 1. Открыть дверь в автоматическом режиме от робота
    M_AirSpray = 6  # Подача воздуха
    M2_ChuckOpen = 7  # Станок 2. Открытие патрона (захвата станка)
    M2_ChuckClose = 8  # Станок 2. Закрытие патрона (захвата станка)
    M2_StartProcess = 9  # Станок 2. Старт обработки
    M2_StopProcess = 10  # Станок 2. Завершение обработки
    M2_DoorClose = 11  # Станок 2. Закрыть дверь в автоматическом режиме от робота
    M2_DoorOpen = 12  # Станок 2. Открыть дверь в автоматическом режиме от робота
    G1_Clamp = 13  # Гриппер 1
    G2_Clamp = 14  # Гриппер 2
    C_Switch = 15 # Зажим тележки
    Cart_Lamp = 16 # Светодиод «Наличие тележки»


DO_DESC: Dict[DO, str] = { # актуальные
    DO.M1_ChuckOpen: "М1: Открытие патрона",
    DO.M1_ChuckClose: "М1: Закрытие патрона",
    DO.M1_StartProcess: "М1: Старт обработки",
    DO.M1_StopProcess: "М1: Завершение обработки",
    DO.M1_DoorClose: "М1: Закрыть дверь",
    DO.M1_DoorOpen: "М1: Открыть дверь",
    DO.M_AirSpray: "Обдув (подача воздуха)",
    DO.M2_ChuckOpen: "М2: Открытие патрона",
    DO.M2_ChuckClose: "М2: Закрытие патрона",
    DO.M2_StartProcess: "М2: Старт обработки",
    DO.M2_StopProcess: "М2: Завершение обработки",
    DO.M2_DoorClose: "М2: Закрыть дверь",
    DO.M2_DoorOpen: "М2: Открыть дверь",
    DO.G1_Clamp: "Гриппер 1: зажим",
    DO.G2_Clamp: "Гриппер 2: зажим",
    DO.C_Switch: "Зажим тележки",
    DO.Cart_Lamp: "Светодиод «Наличие тележки»",
}


class DISim(NamedTuple):
    Check_Button_SIM: bool = False
    M1_DoorOpened_SIM: bool = False
    M1_DoorClosed_SIM: bool = False
    M1_Ready_SIM: bool = False
    M1_ChuckClamped_SIM: bool = False
    M1_ChuckRelaxed_SIM: bool = False
    M1_Alarm_SIM: bool = False
    M2_Alarm_SIM: bool = False
    M2_DoorOpened_SIM: bool = False
    M2_DoorClosed_SIM: bool = False
    M2_Ready_SIM: bool = False
    M2_ChuckClamped_SIM: bool = False
    M2_ChuckRelaxed_SIM: bool = False
    G1_Clamped_SIM: bool = False
    G1_Relaxed_SIM: bool = False
    G2_Clamped_SIM: bool = False
    G2_Relaxed_SIM: bool = False
    Gate_Sensor_SIM: bool = False
    S1_Opened_SIM: bool = False
    S2_Opened_SIM: bool = False
    S3_Opened_SIM: bool = False
    S1_Closed_SIM: bool = False
    S2_Closed_SIM: bool = False
    S3_Closed_SIM: bool = False
    M1_DoorAuto_SIM : bool = False
    M2_DoorAuto_SIM : bool = False

SIM_DI = DISim

# ── Шаблонные имена авто-цикла: [M]_Xxx, [G]_Xxx ─────────────────────────
MACHINE_DI: Dict[int, Dict[str, DI]] = {
    1: {"DoorOpenSQ": DI.M1_DoorOpened,
        "DoorCloseSQ": DI.M1_DoorClosed,
        "Ready": DI.M1_Ready,
        "ChuckClamped": DI.M1_ChuckClamped,
        "ChuckRelax": DI.M1_ChuckRelaxed,
        "Alarm": DI.M1_Alarm},
    2: {"DoorOpenSQ": DI.M2_DoorOpened,
        "DoorCloseSQ": DI.M2_DoorClosed,
        "Ready": DI.M2_Ready,
        "ChuckClamped": DI.M2_ChuckClamped,
        "ChuckRelax": DI.M2_ChuckRelaxed,
        "Alarm": DI.M2_Alarm},
}

MACHINE_DI_SIM: Dict[int, Dict[str, bool]] = {
    1: {"DoorOpenSQ": SIM_DI.M1_DoorOpened_SIM,
        "DoorCloseSQ": SIM_DI.M1_DoorClosed_SIM,
        "Ready": SIM_DI.M1_Ready_SIM,
        "ChuckClamped": SIM_DI.M1_ChuckClamped_SIM,
        "ChuckRelax": SIM_DI.M1_ChuckRelaxed_SIM,
        "Alarm": SIM_DI.M1_Alarm_SIM,
        "DoorAuto": SIM_DI.M1_DoorAuto_SIM},
    2: {"DoorOpenSQ": SIM_DI.M2_DoorOpened_SIM,
        "DoorCloseSQ": SIM_DI.M2_DoorClosed_SIM,
        "Ready": SIM_DI.M2_Ready_SIM,
        "ChuckClamped": SIM_DI.M2_ChuckClamped_SIM,
        "ChuckRelax": SIM_DI.M2_ChuckRelaxed_SIM,
        "Alarm": SIM_DI.M2_Alarm_SIM,
        "DoorAuto": SIM_DI.M2_DoorAuto_SIM},
}

MACHINE_MB_DI: Dict[int, Dict[str, DIModbus]] = {
    1: {"DoorAuto": DIModbus.M1_DoorAuto},
    2: {"DoorAuto": DIModbus.M2_DoorAuto},
}

MACHINE_DO: Dict[int, Dict[str, DO]] = {
    1: {"ChuckOpen": DO.M1_ChuckOpen,
        "ChuckClose": DO.M1_ChuckClose,
        "StartProcess": DO.M1_StartProcess,
        "StopProcess": DO.M1_StopProcess,
        "DoorCloseCMD": DO.M1_DoorClose,
        "DoorOpenCMD": DO.M1_DoorOpen},
    2: {"ChuckOpen": DO.M2_ChuckOpen,
        "ChuckClose": DO.M2_ChuckClose,
        "StartProcess": DO.M2_StartProcess,
        "StopProcess": DO.M2_StopProcess,
        "DoorCloseCMD": DO.M2_DoorClose,
        "DoorOpenCMD": DO.M2_DoorOpen},
}

GRIPPER_DI: Dict[int, Dict[str, DI]] = {
    1: {"Clamped": DI.G1_Clamped, "Relax": DI.G1_Relaxed},
    2: {"Clamped": DI.G2_Clamped, "Relax": DI.G2_Relaxed},
}

GRIPPER_DI_SIM: Dict[int, Dict[str, bool]] = {
    1: {"Clamped": SIM_DI.G1_Clamped_SIM, "Relax": SIM_DI.G1_Relaxed_SIM},
    2: {"Clamped": SIM_DI.G2_Clamped_SIM, "Relax": SIM_DI.G2_Relaxed_SIM},
}

GRIPPER_DO: Dict[int, DO] = {1: DO.G1_Clamp, 2: DO.G2_Clamp}

# Инверсные датчики (заполняется после прозвонки, логика не правится).
DI_INVERT: frozenset = frozenset()
DI_MB_INVERT: frozenset = frozenset() # reallab

IO_COUNT = 24


def machine_di(m: int, role: str) -> int:
    return int(MACHINE_DI[m][role])


def machine_do(m: int, role: str) -> int:
    return int(MACHINE_DO[m][role])


def machine_mb_di(m: int, role: str) -> int:
    return int(MACHINE_MB_DI[m][role])


def gripper_di(g: int, role: str) -> int:
    return int(GRIPPER_DI[g][role])


def gripper_do(g: int) -> int:
    return int(GRIPPER_DO[g])


def di_active(di: DI, raw: bool) -> bool:
    """Учёт полярности датчика в одном месте."""
    return (not raw) if di in DI_INVERT else raw


def di_mb_active(di: DIModbus, raw: bool) -> bool:
    """Учёт полярности датчика в одном месте."""
    return (not raw) if di in DI_MB_INVERT else raw
