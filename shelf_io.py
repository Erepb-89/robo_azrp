"""Доступ к концевикам полок (входы DI.S*_Open из io_map).

Верх = полка 1, середина = полка 2, низ = полка 3 (см. pallet_cfg.SHELF_ORDER).
"""
from typing import Optional

from io_map import DI, SIM_DI

#: Полка -> концевик «полка выдвинута».
SHELF_OPENED_DI = {
    1: DI.S1_Opened,   # 18
    2: DI.S2_Opened,   # 19
    3: DI.S3_Opened,   # 20
}

#: Полка -> концевик «полка выдвинута» sim.
SHELF_OPENED_DI_SIM = {
    1: SIM_DI.S1_Opened_SIM,
    2: SIM_DI.S2_Opened_SIM,
    3: SIM_DI.S3_Opened_SIM,
}

#: Полка -> концевик «полка двинута».
SHELF_CLOSED_DI = {
    1: DI.S1_Closed,   # 21
    2: DI.S2_Closed,   # 22
    3: DI.S3_Closed,   # 23
}


def shelf_opened_di(shelf: int) -> Optional[DI]:
    """Концевик выдвижения для полки (1=верх, 2=середина, 3=низ)."""
    try:
        return SHELF_OPENED_DI[int(shelf)]
    except (KeyError, TypeError, ValueError):
        return None

def shelf_closed_di(shelf: int) -> Optional[DI]:
    """Концевик движения для полки (1=верх, 2=середина, 3=низ)."""
    try:
        return SHELF_CLOSED_DI[int(shelf)]
    except (KeyError, TypeError, ValueError):
        return None
