"""Менеджер паллета-полок.

Модель: стол с тремя выдвижными полками (верх/середина/низ) по 4 x 2 ячейки.
Полки выдвигаются роботом крючком до концевика DI.SHELF_n, порядок работы —
верх -> середина -> низ. Заготовка берётся из ячейки гриппером 1, готовая
деталь возвращается в ту же ячейку гриппером 2.

Пока параметры паллета (pallet_cfg.PALLET_CFG) — заглушки (None), логика
работает в «мягком» режиме: состояние ячеек ведётся, а движения
пропускаются. При "strict": True отсутствие параметров/точек = ошибка.
"""
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from config import MAX_G_SEC
from io_map import GRIPPER_DI
from pallet_cfg import PALLET_CFG
from pallet_errors import SHELF_ERROR_RU, ShelfError
from shelf_io import shelf_di
from shelf_motion import (
    jog_until_di,
    move_linear_pose_sync,
    move_to_named_point_sync,
)
from states_modes_errors import Result


class CellState(Enum):
    """Состояние ячейки полки."""
    Raw = 0  # на месте заготовка
    InProcess = 1  # заготовка снята, деталь у станка
    Finished = 2  # готовая деталь уложена обратно


@dataclass(frozen=True)
class CellAddr:
    """Адрес ячейки: полка (1..3), ряд (0..1), столбец (0..3)."""
    shelf: int
    row: int
    col: int

    @property
    def global_index(self) -> int:
        return (self.shelf - 1) * 8 + self.row * 4 + self.col

    def __str__(self) -> str:
        return f"S{self.shelf}R{self.row}C{self.col}"


@dataclass
class Cell:
    addr: CellAddr
    state: CellState = CellState.Raw
    machine: Optional[int] = None


class PalletManager:
    """Полки, ячейки и операции съёма/укладки поверх RobotController."""

    def __init__(self, rc, logger, cfg: Optional[dict] = None):
        self.rc = rc
        self.log = logger
        self.cfg = cfg or PALLET_CFG
        self.shelves = list(self.cfg.get("shelves") or [1, 2, 3])
        self.rows = int(self.cfg.get("rows", 2))
        self.cols = int(self.cfg.get("cols", 4))

        self._lock = threading.RLock()
        self.shelf_idx = 0
        self._open_shelf: Optional[int] = None
        self.cells: Dict[Tuple[int, int, int], Cell] = {}
        for shelf in self.shelves:
            for row in range(self.rows):
                for col in range(self.cols):
                    addr = CellAddr(shelf, row, col)
                    self.cells[(shelf, row, col)] = Cell(addr)

    # ── состояние ────────────────────────────────────────────────────────────

    def _error(self, err: ShelfError, level: str = 'error') -> None:
        self.rc.message(SHELF_ERROR_RU.get(err, str(err)), level)

    @property
    def current_shelf(self) -> int:
        return self.shelves[self.shelf_idx]

    @property
    def open_shelf(self) -> Optional[int]:
        return self._open_shelf

    def next_raw_cell(self) -> Optional[CellAddr]:
        """Первая ячейка текущей полки с заготовкой или None."""
        with self._lock:
            shelf = self.current_shelf
            for row in range(self.rows):
                for col in range(self.cols):
                    cell = self.cells[(shelf, row, col)]
                    if cell.state == CellState.Raw:
                        return cell.addr
        return None

    def has_raw_workpiece(self) -> bool:
        """Есть ли заготовка хотя бы в одной ячейке любой полки."""
        with self._lock:
            return any(cell.state == CellState.Raw
                       for cell in self.cells.values())

    def shelf_empty(self, shelf: Optional[int] = None) -> bool:
        """Все ячейки полки получили готовые детали обратно."""
        shelf = self.current_shelf if shelf is None else shelf
        with self._lock:
            return all(
                self.cells[(shelf, row, col)].state == CellState.Finished
                for row in range(self.rows) for col in range(self.cols)
            )

    def all_shelves_done(self) -> bool:
        """Текущая (последняя) полка исчерпана — работы больше нет."""
        with self._lock:
            return (self.current_shelf == self.shelves[-1]
                    and self.shelf_empty())

    def in_flight(self, shelf: Optional[int] = None) -> int:
        """Число ячеек полки, детали которых сейчас в работе."""
        shelf = self.current_shelf if shelf is None else shelf
        with self._lock:
            return sum(
                1 for r in range(self.rows) for c in range(self.cols)
                if self.cells[(shelf, r, c)].state == CellState.InProcess
            )

    def snapshot(self) -> Dict[str, object]:
        """Краткий снимок состояния для журнала/GUI."""
        with self._lock:
            return {
                "current_shelf": self.current_shelf,
                "open_shelf": self._open_shelf,
                "shelves": [
                    {
                        "shelf": shelf,
                        "shelf_empty": self.shelf_empty(shelf),
                        "in_flight": self.in_flight(shelf),
                    }
                    for shelf in self.shelves
                ],
            }

    # ── геометрия ────────────────────────────────────────────────────────────

    def point_taught(self, name) -> bool:
        try:
            return bool(name) and name in self.rc.data.waypoints
        except Exception:
            return False

    def missing_geometry(self):
        cfg = self.cfg
        missing = []
        for key in ("origin_point", "pitch_x", "pitch_y",
                    "cell_approach_dz", "cell_dwell_dz"):
            if cfg.get(key) is None:
                missing.append(key)
        for shelf in self.shelves:
            if (cfg.get("shelf_dz") or {}).get(shelf) is None:
                missing.append(f"shelf_dz[{shelf}]")
        if cfg.get("origin_point") and not self.point_taught(cfg["origin_point"]):
            missing.append(str(cfg["origin_point"]))
        return missing

    def strict(self) -> bool:
        return bool(self.cfg.get("strict"))

    def geometry_ready(self) -> bool:
        return not self.missing_geometry()

    def geometry_fail(self) -> Result:
        missing = self.missing_geometry()
        self.log.warning("Паллет: не заданы параметры: %s", ", ".join(missing))
        if self.strict():
            self.rc.message(
                "Паллет: не обучены параметры: " + ", ".join(missing[:6]),
                'error')
            return Result.Error
        self.rc.message("Паллет: режим заглушки (нет параметров)", 'warning')
        return Result.NoError

    def cell_pose(self, addr: CellAddr):
        """Поза ячейки = origin + (col*pitch_x, row*pitch_y, shelf_dz)."""
        origin = self.rc.data.get_tcp_pose(self.cfg["origin_point"])
        dx = addr.col * float(self.cfg["pitch_x"])
        dy = addr.row * float(self.cfg["pitch_y"])
        dz = float(self.cfg["shelf_dz"][addr.shelf])
        return (origin[0] + dx, origin[1] + dy, origin[2] + dz,
                origin[3], origin[4], origin[5])

    def approach_pose(self, addr: CellAddr):
        pose = self.cell_pose(addr)
        dz = float(self.cfg["cell_approach_dz"])
        return (pose[0], pose[1], pose[2] + dz, pose[3], pose[4], pose[5])

    def dwell_pose(self, addr: CellAddr):
        pose = self.cell_pose(addr)
        dz = float(self.cfg.get("cell_dwell_dz") or 0.0)
        return (pose[0], pose[1], pose[2] + dz, pose[3], pose[4], pose[5])

    def move_to_cell(self, addr: CellAddr, abort=None) -> bool:
        speed = float(self.cfg.get("cell_speed", 0.1))
        accel = float(self.cfg.get("cell_accel", 0.1))
        blend = float(self.cfg.get("cell_blend", 0.0))
        if not move_linear_pose_sync(self.rc, self.approach_pose(addr),
                                     speed, accel, blend, abort):
            return False
        return move_linear_pose_sync(self.rc, self.dwell_pose(addr),
                                     speed, accel, blend, abort)

    def retreat_from_cell(self, addr: CellAddr, abort=None) -> bool:
        speed = float(self.cfg.get("cell_speed", 0.1))
        accel = float(self.cfg.get("cell_accel", 0.1))
        blend = float(self.cfg.get("cell_blend", 0.0))
        return move_linear_pose_sync(self.rc, self.approach_pose(addr),
                                     speed, accel, blend, abort)

    def gripper(self, g: int, clamp: bool, abort=None) -> Result:
        if not self.rc.io.gripper_do(g, clamp):
            return Result.Error
        role = 'Clamped' if clamp else 'Relax'
        if not self.rc.io.wait_di(GRIPPER_DI[g][role], True, MAX_G_SEC, abort):
            self.rc.message(
                f"Паллет: гриппер {g} не подтвердил "
                f"{'зажим' if clamp else 'разжим'}", 'error')
            return Result.Error
        return Result.NoError

    # ── операции с ячейками ──────────────────────────────────────────────────

    def get_cell(self, addr) -> Optional[Cell]:
        try:
            key = (int(addr.shelf), int(addr.row), int(addr.col))
        except Exception:
            return None
        with self._lock:
            return self.cells.get(key)

    def depalletizing(self, addr, machine=None, abort=None) -> Result:
        """Взять заготовку из ячейки (гриппер 1)."""
        cell = self.get_cell(addr)
        if cell is None:
            self.rc.message(f"Паллет: неверный адрес {addr}", 'error')
            return Result.Error
        if cell.state != CellState.Raw:
            self.rc.message(f"Паллет: ячейка {addr} без заготовки", 'warning')
            return Result.Error

        if not self.geometry_ready():
            if self.geometry_fail() != Result.NoError:
                return Result.Error
        else:
            if not self.move_to_cell(addr, abort):
                return Result.Error
            if self.gripper(1, True, abort) != Result.NoError:
                return Result.Error
            if not self.retreat_from_cell(addr, abort):
                return Result.Error

        with self._lock:
            cell.state = CellState.InProcess
            cell.machine = machine
        self.log.info("Паллет: снята заготовка %s (станок %s)", addr, machine)
        return Result.NoError

    def palletizing(self, addr, machine=None, abort=None) -> Result:
        """Уложить готовую деталь обратно в ячейку (гриппер 2)."""
        cell = self.get_cell(addr)
        if cell is None:
            self.rc.message(f"Паллет: неверный адрес {addr}", 'error')
            return Result.Error
        if cell.state != CellState.InProcess:
            self.rc.message(f"Паллет: ячейка {addr} не в работе", 'warning')
            return Result.Error

        if not self.geometry_ready():
            if self.geometry_fail() != Result.NoError:
                return Result.Error
        else:
            if not self.move_to_cell(addr, abort):
                return Result.Error
            if self.gripper(2, False, abort) != Result.NoError:
                return Result.Error
            if not self.retreat_from_cell(addr, abort):
                return Result.Error

        with self._lock:
            cell.state = CellState.Finished
            cell.machine = None
        self.log.info("Паллет: уложена деталь %s (станок %s)", addr, machine)
        return Result.NoError

    # ── полки: выдвижение/задвигание/смена ───────────────────────────────────

    def prepare_for_pick(self, abort=None) -> Result:
        """Обеспечить открытую полку с заготовками.

        При исчерпании текущей полки (все ячейки Finished) и отсутствии
        деталей «в полёте» выполняется смена на следующую полку. Если все
        полки пройдены — возвращает NoError (следующий next_raw_cell() даст
        None).
        """
        with self._lock:
            if self.shelf_empty():
                if self.all_shelves_done():
                    return Result.NoError
                if self.in_flight() > 0:
                    self._error(ShelfError.SwitchInFlight)
                    return Result.Error
                if self.switch_to_next(abort) != Result.NoError:
                    return Result.Error
            return self.ensure_current_shelf_open(abort)

    def ensure_current_shelf_open(self, abort=None) -> Result:
        """Выдвинуть текущую полку, если она ещё не выдвинута."""
        with self._lock:
            shelf = self.current_shelf
            if self._open_shelf == shelf:
                return Result.NoError
            return self.open_shelf_for(shelf, abort)

    def switch_to_next(self, abort=None) -> Result:
        with self._lock:
            if self._open_shelf is not None:
                if self.close_shelf(abort) != Result.NoError:
                    return Result.Error
            if self.shelf_idx + 1 >= len(self.shelves):
                return Result.Error
            self.shelf_idx += 1
            self.rc.message(f"Паллет: переход на полку {self.current_shelf}")
            return self.open_shelf_for(self.current_shelf, abort)

    def hook_params(self, shelf: int):
        hook = (self.cfg.get("hook") or {}).get(shelf, {}) or {}
        return hook

    def hook_configured(self, shelf: int) -> bool:
        hook = self.hook_params(shelf)
        engage = hook.get("engage")
        return all(v is not None for v in (
            engage, self.cfg.get("pull_axis"),
            self.cfg.get("pull_dir"), self.cfg.get("pull_timeout_sec"),
        )) and self.point_taught(engage)

    def open_shelf_for(self, shelf: int, abort=None) -> Result:
        if not self.hook_configured(shelf):
            if self.strict():
                self._error(ShelfError.NotTaught)
                return Result.Error
            self.rc.message(
                f"Паллет: полка {shelf} — заглушка выдвижения", 'warning')
            self._open_shelf = shelf
            return Result.NoError

        hook = self.hook_params(shelf)
        if hook.get("approach"):
            if not move_to_named_point_sync(self.rc, hook["approach"],
                                            'line', abort):
                return Result.Error
        if not move_to_named_point_sync(self.rc, hook["engage"], 'line', abort):
            return Result.Error
        if not jog_until_di(self.rc, shelf_di(shelf), self.cfg["pull_axis"],
                            self.cfg["pull_dir"],
                            self.cfg["pull_timeout_sec"], abort):
            return Result.Error
        if hook.get("retreat"):
            if not move_to_named_point_sync(self.rc, hook["retreat"],
                                            'line', abort):
                return Result.Error

        self._open_shelf = shelf
        return Result.NoError

    def close_shelf(self, abort=None) -> Result:
        """Задвинуть текущую открытую полку в обученную точку «закрыто»."""
        with self._lock:
            if self._open_shelf is None:
                return Result.NoError
            shelf = self._open_shelf
            closed = self.hook_params(shelf).get("closed")
            if not self.point_taught(closed):
                if self.strict():
                    self.rc.message(
                        f"Паллет: точка закрытия полки {shelf} не обучена",
                        'error')
                    return Result.Error
                self.rc.message(
                    f"Паллет: закрытие полки {shelf} — заглушка", 'warning')
                self._open_shelf = None
                return Result.NoError
            if not move_to_named_point_sync(self.rc, closed, 'line', abort):
                return Result.Error
            self._open_shelf = None
            return Result.NoError
