"""
Карта физических сигналов контроллера (DI/DO).
«Блок-схема общая (26.09.28).vsdx».
"""
from enum import IntEnum
from typing import Dict


class DI(IntEnum):
    """Порты ввода контроллера."""
    M1_DoorAuto = 0  # Станок 1. Дверь в автоматическом режиме
    M1_DoorOpenSQ = 1  # Станок 1. Дверь открыта
    M1_DoorCloseSQ = 2  # Станок 1. Дверь закрыта
    M1_Ready = 3  # Станок 1 готов к загрузке/выгрузке
    M1_ChuckClamped = 4  # Станок 1. Патрон закрыт
    M1_ChuckRelax = 5  # Станок 1. Патрон открыт
    START_STOP = 6  # Старт/стоп работы робота («START/STOP»)
    M2_DoorAuto = 7  # Станок 2. Дверь в автоматическом режиме
    M2_DoorOpenSQ = 8  # Станок 2. Дверь открыта
    M2_DoorCloseSQ = 9  # Станок 2. Дверь закрыта
    M2_Ready = 10  # Станок 2 готов к загрузке/выгрузке
    M2_ChuckClamped = 11  # Станок 2. Патрон закрыт
    M2_ChuckRelax = 12  # Станок 2. Патрон открыт
    G1_Switch = 13  # Переключение гриппера 1
    G1_Clamped = 14  # Гриппер 1 закрыт
    G1_Relax = 15  # Гриппер 1 открыт
    G2_Switch = 16  # Переключение гриппера 2
    G2_Relax = 17  # Гриппер 2 открыт
    G2_Clamped = 18  # Гриппер 2 закрыт
    GATE = 19  # Сигнал с калитки
    CART = 20  # Сигнал с тележки
    SHELF_1 = 21  # Полка 1 задвинута
    SHELF_2 = 22  # Полка 2 задвинута
    SHELF_3 = 23  # Полка 3 задвинута


class DO(IntEnum):
    """Порты вывода контроллера."""
    M1_SwitchChuck = 0  # Станок 1. Переключение патрона (захвата станка)
    M1_StartProcess = 1  # Станок 1. Старт обработки
    M1_DoorCloseCMD = 2  # Станок 1. Закрыть дверь в автоматическом режиме от робота
    M1_DoorOpenCMD = 3  # Станок 1. Открыть дверь в автоматическом режиме от робота
    M1_LampAlarm = 4  # Светодиод «Авария»
    M1_LampAuto = 5  # Светодиод «Автоматический режим»
    M_AirSpray = 6  # Подача воздуха
    M2_SwitchChuck = 7  # Станок 2. Переключение патрона (захвата станка)
    M2_StartProcess = 8  # Станок 2. Старт обработки
    M2_DoorCloseCMD = 9  # Станок 2. Закрыть дверь в автоматическом режиме от робота
    M2_DoorOpenCMD = 10  # Станок 2. Открыть дверь в автоматическом режиме от робота
    M2_LampAlarm = 11  # Светодиод «Авария»
    M2_LampAuto = 12  # Светодиод «Автоматический режим»
    M_LampRun = 13  # Светодиод «В работе»
    G1_Clamp = 14  # Гриппер 1
    G2_Clamp = 15  # Гриппер 2


DI_DESC: Dict[DI, str] = {
    DI.M1_DoorAuto: "М1: дверь в авто-режиме",
    DI.M1_DoorOpenSQ: "М1: дверь открыта",
    DI.M1_DoorCloseSQ: "М1: дверь закрыта",
    DI.M1_Ready: "М1: готов к загрузке",
    DI.M1_ChuckClamped: "М1: патрон закрыт",
    DI.M1_ChuckRelax: "М1: патрон открыт",
    DI.START_STOP: "Старт/Стоп робота",
    DI.M2_DoorAuto: "М2: дверь в авто-режиме",
    DI.M2_DoorOpenSQ: "М2: дверь открыта",
    DI.M2_DoorCloseSQ: "М2: дверь закрыта",
    DI.M2_Ready: "М2: готов к загрузке",
    DI.M2_ChuckClamped: "М2: патрон закрыт",
    DI.M2_ChuckRelax: "М2: патрон открыт",
    DI.G1_Switch: "Гриппер 1: переключение",
    DI.G1_Clamped: "Гриппер 1: закрыт",
    DI.G1_Relax: "Гриппер 1: открыт",
    DI.G2_Switch: "Гриппер 2: переключение",
    DI.G2_Relax: "Гриппер 2: открыт",
    DI.G2_Clamped: "Гриппер 2: закрыт",
    DI.GATE: "Калитка",
    DI.CART: "Тележка",
    DI.SHELF_1: "Полка 1",
    DI.SHELF_2: "Полка 2",
    DI.SHELF_3: "Полка 3",
}

DO_DESC: Dict[DO, str] = {
    DO.M1_SwitchChuck: "М1: переключение патрона",
    DO.M1_StartProcess: "М1: старт обработки",
    DO.M1_DoorCloseCMD: "М1: закрыть дверь",
    DO.M1_DoorOpenCMD: "М1: открыть дверь",
    DO.M1_LampAlarm: "М1: лампа «Авария»",
    DO.M1_LampAuto: "М1: лампа «Авто-режим»",
    DO.M_AirSpray: "Обдув (подача воздуха)",
    DO.M2_SwitchChuck: "М2: переключение патрона",
    DO.M2_StartProcess: "М2: старт обработки",
    DO.M2_DoorCloseCMD: "М2: закрыть дверь",
    DO.M2_DoorOpenCMD: "М2: открыть дверь",
    DO.M2_LampAlarm: "М2: лампа «Авария»",
    DO.M2_LampAuto: "М2: лампа «Авто-режим»",
    DO.M_LampRun: "Лампа «В работе»",
    DO.G1_Clamp: "Гриппер 1: зажим",
    DO.G2_Clamp: "Гриппер 2: зажим",
}

# ── Шаблонные имена авто-цикла: [M]_Xxx, [G]_Xxx ─────────────────────────
MACHINE_DI: Dict[int, Dict[str, DI]] = {
    1: {"DoorAuto": DI.M1_DoorAuto, "DoorOpenSQ": DI.M1_DoorOpenSQ,
        "DoorCloseSQ": DI.M1_DoorCloseSQ, "Ready": DI.M1_Ready,
        "ChuckClamped": DI.M1_ChuckClamped, "ChuckRelax": DI.M1_ChuckRelax},
    2: {"DoorAuto": DI.M2_DoorAuto, "DoorOpenSQ": DI.M2_DoorOpenSQ,
        "DoorCloseSQ": DI.M2_DoorCloseSQ, "Ready": DI.M2_Ready,
        "ChuckClamped": DI.M2_ChuckClamped, "ChuckRelax": DI.M2_ChuckRelax},
}

MACHINE_DO: Dict[int, Dict[str, DO]] = {
    1: {"SwitchChuck": DO.M1_SwitchChuck, "StartProcess": DO.M1_StartProcess,
        "DoorCloseCMD": DO.M1_DoorCloseCMD, "DoorOpenCMD": DO.M1_DoorOpenCMD,
        "LampAlarm": DO.M1_LampAlarm, "LampAuto": DO.M1_LampAuto},
    2: {"SwitchChuck": DO.M2_SwitchChuck, "StartProcess": DO.M2_StartProcess,
        "DoorCloseCMD": DO.M2_DoorCloseCMD, "DoorOpenCMD": DO.M2_DoorOpenCMD,
        "LampAlarm": DO.M2_LampAlarm, "LampAuto": DO.M2_LampAuto},
}

GRIPPER_DI: Dict[int, Dict[str, DI]] = {
    1: {"Switch": DI.G1_Switch, "Clamped": DI.G1_Clamped, "Relax": DI.G1_Relax},
    2: {"Switch": DI.G2_Switch, "Clamped": DI.G2_Clamped, "Relax": DI.G2_Relax},
}

GRIPPER_DO: Dict[int, DO] = {1: DO.G1_Clamp, 2: DO.G2_Clamp}

# Инверсные датчики (заполняется после прозвонки, логика не правится).
DI_INVERT: frozenset = frozenset()

IO_COUNT = 24


def machine_di(m: int, role: str) -> int:
    return int(MACHINE_DI[m][role])


def machine_do(m: int, role: str) -> int:
    return int(MACHINE_DO[m][role])


def gripper_di(g: int, role: str) -> int:
    return int(GRIPPER_DI[g][role])


def gripper_do(g: int) -> int:
    return int(GRIPPER_DO[g])


def di_active(di: DI, raw: bool) -> bool:
    """Учёт полярности датчика в одном месте."""
    return (not raw) if di in DI_INVERT else raw
