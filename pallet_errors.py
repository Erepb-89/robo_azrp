"""Ошибки паллета (полки/ячейки).

Отдельно от states_modes_errors.LastError, чтобы не править существующий enum.
"""
from enum import Enum


class ShelfError(Enum):
    NoError = 0
    NotTaught = 1        # параметры/точки паллета не обучены
    PullTimeout = 2      # нет сигнала концевика при выдвижении полки
    SwitchInFlight = 3   # попытка смены полки при детали в работе
    InvalidCell = 4      # неверный адрес ячейки / недопустимое состояние
    MotionFailed = 5     # ошибка движения по паллету


SHELF_ERROR_RU = {
    ShelfError.NoError: "Нет ошибки",
    ShelfError.NotTaught: "Паллет: параметры/точки не обучены",
    ShelfError.PullTimeout: "Паллет: таймаут концевика выдвижения полки",
    ShelfError.SwitchInFlight: "Паллет: смена полки при детали в работе",
    ShelfError.InvalidCell: "Паллет: неверный адрес/состояние ячейки",
    ShelfError.MotionFailed: "Паллет: ошибка движения",
}
