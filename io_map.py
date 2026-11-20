"""
Карта физических сигналов контроллера (DI/DO).
«Блок-схема общая (26.09.28).vsdx».
"""
from enum import IntEnum
from typing import Dict


class DI(IntEnum):
    """Порты ввода контроллера."""
    Check_Button = 0 # Сигнал с кнопки юстировки
    M1_DoorOpenSQ = 1 # Станок 1. Дверь открыта
    M1_DoorCloseSQ = 2 # Станок 1. Дверь закрыта
    M1_Ready = 3 # Станок 1 готов к загрузке/выгрузке
    M1_ChuckClamped = 4 # Станок 1. Патрон закрыт
    M1_ChuckRelax = 5 # Станок 1. Патрон открыт
    M1_Alarm = 6 # Станок 1. Сигнал об ошибке
    M2_Alarm = 7 # Станок 2. Сигнал об ошибке
    M2_DoorOpenSQ = 8 # Станок 2. Дверь открыта
    M2_DoorCloseSQ = 9 # Станок 2. Дверь закрыта
    M2_Ready = 10 # Станок 2 готов к загрузке/выгрузке
    M2_ChuckClamped = 11 # Станок 2. Патрон закрыт
    M2_ChuckRelax = 12 # Станок 2. Патрон открыт
    G1_Clamped = 13 # Гриппер 1 закрыт
    G1_Relax = 14 # Гриппер 1 открыт
    G2_Clamped = 15 # Гриппер 2 закрыт
    G2_Relax = 16 # Гриппер 2 открыт
    Gate_Sensor = 17 # Сигнал с калитки
    S1_Open = 18 # Полка 1 выдвинута
    S2_Open = 19 # Полка 2 выдвинута
    S3_Open = 20 # Полка 3 выдвинута
    S1_Close = 21 # Полка 1 задвинута
    S2_Close = 22 # Полка 2 задвинута
    S3_Close = 23 # Полка 3 задвинута


DI_DESC: Dict[DI, str] = {
    DI.Check_Button: "Сигнал с кнопки юстировки",
    DI.M1_DoorOpenSQ: "М1: дверь открыта",
    DI.M1_DoorCloseSQ: "М1: дверь закрыта",
    DI.M1_Ready: "М1: готов к загрузке",
    DI.M1_ChuckClamped: "М1: патрон закрыт",
    DI.M1_ChuckRelax: "М1: патрон открыт",
    DI.M1_Alarm: "Станок 1. Сигнал об ошибке",
    DI.M2_Alarm: "Станок 2. Сигнал об ошибке",
    DI.M2_DoorOpenSQ: "М2: дверь открыта",
    DI.M2_DoorCloseSQ: "М2: дверь закрыта",
    DI.M2_Ready: "М2: готов к загрузке",
    DI.M2_ChuckClamped: "М2: патрон закрыт",
    DI.M2_ChuckRelax: "М2: патрон открыт",
    DI.G1_Clamped: "Гриппер 1: закрыт",
    DI.G1_Relax: "Гриппер 1: открыт",
    DI.G2_Clamped: "Гриппер 2: закрыт",
    DI.G2_Relax: "Гриппер 2: открыт",
    DI.Gate_Sensor: "Калитка задвинута",
    DI.S1_Open: "Полка 1 выдвинута",
    DI.S2_Open: "Полка 2 выдвинута",
    DI.S3_Open: "Полка 3 выдвинута",
    DI.S1_Close: "Полка 1 задвинута",
    DI.S2_Close: "Полка 2 задвинута",
    DI.S3_Close: "Полка 3 задвинута",
}

# Modbus signals
class DIModbus(IntEnum):
    """Порты ввода Modbus модуля Reallab."""
    START_STOP = 0  # Старт/стоп работы робота («START/STOP»)
    M1_DoorAuto = 1  # Станок 1. Дверь в автоматическом режиме
    M2_DoorAuto = 2  # Станок 2. Дверь в автоматическом режиме
    G1_Switch = 3  # Переключение гриппера 1
    G2_Switch = 4  # Переключение гриппера 2
    Pause_Resume = 5  # Пауза/Продолжить
    C1_PneumoSensorOpened = 6  # Сигнал с концевика Поршень 1 открыт
    C1_PneumoSensorClosed = 7  # Сигнал с концевика Поршень 1 закрыт
    C2_PneumoSensorOpened = 8  # Сигнал с концевика Поршень 2 открыт
    C2_PneumoSensorClosed = 9  # Сигнал с концевика Поршень 2 закрыт
    C_Sensor = 10  # Тележка установлена
    M1_DoorOpen = 11  # Станок 1. Открыть дверь
    M1_DoorClose = 12  # Станок 1. Закрыть дверь
    M2_DoorOpen = 13  # Станок 2. Открыть дверь
    M2_DoorClose = 14  # Станок 2. Закрыть дверь
    C_Fix = 15  # Зафиксировать тележку


DI_MODBUS_DESC: Dict[DIModbus, str] = {
    DIModbus.START_STOP: "Старт/стоп работы робота («START/STOP»)",
    DIModbus.M1_DoorAuto: "М1: дверь в авто-режиме",
    DIModbus.M2_DoorAuto: "М2: дверь в авто-режиме",
    DIModbus.G1_Switch: "Переключение гриппера 1",
    DIModbus.G2_Switch: "Переключение гриппера 2",
    DIModbus.Pause_Resume: "Пауза/Продолжить",
    DIModbus.C1_PneumoSensorOpened: "Сигнал с концевика Поршень 1 открыт",
    DIModbus.C1_PneumoSensorClosed: "Сигнал с концевика Поршень 1 закрыт",
    DIModbus.C2_PneumoSensorOpened: "Сигнал с концевика Поршень 2 открыт",
    DIModbus.C2_PneumoSensorClosed: "Сигнал с концевика Поршень 2 закрыт",
    DIModbus.C_Sensor: "Тележка установлена",
    DIModbus.M1_DoorOpen: "Станок 1. Открыть дверь",
    DIModbus.M1_DoorClose: "Станок 1. Закрыть дверь",
    DIModbus.M2_DoorOpen: "Станок 2. Открыть дверь",
    DIModbus.M2_DoorClose: "Станок 2. Закрыть дверь",
    DIModbus.C_Fix: "Зафиксировать тележку",
}


class DO(IntEnum):
    """Порты вывода контроллера.""" # актуальные
    M1_ChuckOpen = 0  # Станок 1. Открытие патрона (захвата станка)
    M1_ChuckClose = 1  # Станок 1. Закрытие патрона (захвата станка)
    M1_StartProcess = 2  # Станок 1. Старт обработки
    M1_StopProcess = 3  # Станок 1. Завершение обработки
    M1_DoorCloseCMD = 4  # Станок 1. Закрыть дверь в автоматическом режиме от робота
    M1_DoorOpenCMD = 5  # Станок 1. Открыть дверь в автоматическом режиме от робота
    M_AirSpray = 6  # Подача воздуха
    M2_ChuckOpen = 7  # Станок 2. Открытие патрона (захвата станка)
    M2_ChuckClose = 8  # Станок 2. Закрытие патрона (захвата станка)
    M2_StartProcess = 9  # Станок 2. Старт обработки
    M2_StopProcess = 10  # Станок 2. Завершение обработки
    M2_DoorCloseCMD = 11  # Станок 2. Закрыть дверь в автоматическом режиме от робота
    M2_DoorOpenCMD = 12  # Станок 2. Открыть дверь в автоматическом режиме от робота
    G1_Clamp = 13  # Гриппер 1
    G2_Clamp = 14  # Гриппер 2
    C_Switch = 15 # Зажим тележки
    Cart_Lamp = 16 # Светодиод «Наличие тележки»


DO_DESC: Dict[DO, str] = { # актуальные
    DO.M1_ChuckOpen: "М1: Открытие патрона",
    DO.M1_ChuckClose: "М1: Закрытие патрона",
    DO.M1_StartProcess: "М1: Старт обработки",
    DO.M1_StopProcess: "М1: Завершение обработки",
    DO.M1_DoorCloseCMD: "М1: Закрыть дверь",
    DO.M1_DoorOpenCMD: "М1: Открыть дверь",
    DO.M_AirSpray: "Обдув (подача воздуха)",
    DO.M2_ChuckOpen: "М2: Открытие патрона",
    DO.M2_ChuckClose: "М2: Закрытие патрона",
    DO.M2_StartProcess: "М2: Старт обработки",
    DO.M2_StopProcess: "М2: Завершение обработки",
    DO.M2_DoorCloseCMD: "М2: Закрыть дверь",
    DO.M2_DoorOpenCMD: "М2: Открыть дверь",
    DO.G1_Clamp: "Гриппер 1: зажим",
    DO.G2_Clamp: "Гриппер 2: зажим",
    DO.C_Switch: "Зажим тележки",
    DO.Cart_Lamp: "Светодиод «Наличие тележки»",
}

# ── Шаблонные имена авто-цикла: [M]_Xxx, [G]_Xxx ─────────────────────────
MACHINE_DI: Dict[int, Dict[str, DI]] = {
    1: {"DoorOpenSQ": DI.M1_DoorOpenSQ, "DoorCloseSQ": DI.M1_DoorCloseSQ,
        "Ready": DI.M1_Ready, "ChuckClamped": DI.M1_ChuckClamped,
        "ChuckRelax": DI.M1_ChuckRelax, "Alarm": DI.M1_Alarm},
    2: {"DoorOpenSQ": DI.M2_DoorOpenSQ, "DoorCloseSQ": DI.M2_DoorCloseSQ,
        "Ready": DI.M2_Ready, "ChuckClamped": DI.M2_ChuckClamped,
        "ChuckRelax": DI.M2_ChuckRelax, "Alarm": DI.M2_Alarm},
}

MACHINE_MB_DI: Dict[int, Dict[str, DIModbus]] = {
    1: {"DoorAuto": DIModbus.M1_DoorAuto},
    2: {"DoorAuto": DIModbus.M2_DoorAuto},
}

MACHINE_DO: Dict[int, Dict[str, DO]] = {
    1: {"ChuckOpen": DO.M1_ChuckOpen, "ChuckClose": DO.M1_ChuckClose,
        "StartProcess": DO.M1_StartProcess, "StopProcess": DO.M1_StopProcess,
        "DoorCloseCMD": DO.M1_DoorCloseCMD, "DoorOpenCMD": DO.M1_DoorOpenCMD},
    2: {"ChuckOpen": DO.M2_ChuckOpen, "ChuckClose": DO.M2_ChuckClose,
        "StartProcess": DO.M2_StartProcess, "StopProcess": DO.M2_StopProcess,
        "DoorCloseCMD": DO.M2_DoorCloseCMD, "DoorOpenCMD": DO.M2_DoorOpenCMD},
}

GRIPPER_DI: Dict[int, Dict[str, DI]] = {
    1: {"Clamped": DI.G1_Clamped, "Relax": DI.G1_Relax},
    2: {"Clamped": DI.G2_Clamped, "Relax": DI.G2_Relax},
}

GRIPPER_MB_DI: Dict[int, Dict[str, DIModbus]] = {
    1: {"Switch": DIModbus.G1_Switch},
    2: {"Switch": DIModbus.G2_Switch},
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


def gripper_mb_di(g: int, role: str) -> int:
    return int(GRIPPER_MB_DI[g][role])


def gripper_do(g: int) -> int:
    return int(GRIPPER_DO[g])


def di_active(di: DI, raw: bool) -> bool:
    """Учёт полярности датчика в одном месте."""
    return (not raw) if di in DI_INVERT else raw


def di_mb_active(di: DIModbus, raw: bool) -> bool:
    """Учёт полярности датчика в одном месте."""
    return (not raw) if di in DI_MB_INVERT else raw
