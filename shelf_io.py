"""Доступ к концевикам полок (входы DI.S*_Open из io_map).

Верх = полка 1, середина = полка 2, низ = полка 3 (см. pallet_cfg.SHELF_ORDER).
"""
from typing import Optional

from io_map import DI

#: Полка -> концевик «полка выдвинута».
SHELF_DI = {
    1: DI.S1_Open,   # 18
    2: DI.S2_Open,   # 19
    3: DI.S3_Open,   # 20
}


def shelf_di(shelf: int) -> Optional[DI]:
    """Концевик выдвижения для полки (1=верх, 2=середина, 3=низ)."""
    try:
        return SHELF_DI[int(shelf)]
    except (KeyError, TypeError, ValueError):
        return None
