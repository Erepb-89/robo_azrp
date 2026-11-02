"""
Операции авто-цикла: движения и загрузка/выгрузка станка.

CycleFlags — единое хранилище флагов схемы (G1IsEmptyFlag, isMachineLoad,
LastWorkpiece, M_state, адреса). CycleOps собирает машины, грипперы и паллет
и реализует функции LoadWorkpiece / UnloadPart / PickWorkpiece /
PlacePartOnTable / InMachineG1/G2 / ExitMachine / ChuckAirBlast.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional

from commands import RobotTrajectories
from gripper import Gripper
from io_map import DO
from machine import CncMachine
from pallet_manager import PalletManager
from states_modes_errors import MachineState, Result


@dataclass
class CycleFlags:
    """Флаги (глобальное состояние авто-цикла)."""
    g1_is_empty: bool = True
    is_machine_load: Dict[int, bool] = field(
        default_factory=lambda: {1: False, 2: False})
    last_workpiece: Dict[int, bool] = field(
        default_factory=lambda: {1: False, 2: False})
    m_state: Dict[int, MachineState] = field(
        default_factory=lambda: {1: MachineState.NotActive,
                                 2: MachineState.NotActive})
    cur_addr: Dict[int, Optional[int]] = field(
        default_factory=lambda: {1: None, 2: None})
    pick_addr: Dict[int, Optional[int]] = field(
        default_factory=lambda: {1: None, 2: None})
    place_addr: Dict[int, Optional[int]] = field(
        default_factory=lambda: {1: None, 2: None})

    def reset(self) -> None:
        self.g1_is_empty = True
        for m in (1, 2):
            self.is_machine_load[m] = False
            self.last_workpiece[m] = False
            self.m_state[m] = MachineState.NotActive
            self.cur_addr[m] = None
            self.pick_addr[m] = None
            self.place_addr[m] = None


class CycleOps:
    """Операции цикла поверх RobotController (синхронные)."""

    def __init__(self, rc, logger, pallet=None):
        self.rc = rc
        self.log = logger
        self.machines = {1: CncMachine(1, rc, logger),
                         2: CncMachine(2, rc, logger)}
        self.grippers = {1: Gripper(1, rc, logger),
                         2: Gripper(2, rc, logger)}
        self.pallet = pallet or PalletManager(logger, rc.message)
        for m in (1, 2):
            self.machines[m].bind_ops(self)

    # ── траектории ───────────────────────────────────────────────────────────

    def traj(self, name: str):
        return RobotTrajectories[name]

    # ── глобальные движения (MoveTo/LinTo из схемы) ─────────────────────────

    def init_move(self, abort=None) -> bool:
        """InitMove(): MoveTo(BGIntP011); MoveTo(BGIntP010)."""
        return self.rc.execute_trajectory_sync(
            self.traj('tBGIntP010_To_BGIntP011'), abort)

    def move_from_g_int(self, m: int, abort=None) -> bool:
        """MoveFromGInt(M): LinTo(BG[M]P010); LinTo(BG[M]P020)."""
        return self.rc.execute_trajectory_sync(
            self.traj(f"tBGIntP010_To_BG{m}P020"), abort)

    def move_to_g_int(self, m: int, abort=None) -> bool:
        """MoveToGInt(M): возврат в исходную точку."""
        return self.rc.execute_trajectory_sync(
            self.traj(f"tBG{m}P020_To_BGIntP010"), abort)

    def move_to_safe(self, m: int, abort=None) -> bool:
        """MoveTo(BG[M]P020) — точка смены гриппера."""
        return self.rc.move_to_point_sync(f"BG{m}P020", 'joint', abort)

    def exit_machine(self, g: int, m: int, from_point, abort=None) -> Result:
        """ExitMachine(G,M): из точки внутри станка — в точку готовности B[G][M]P010."""
        p010 = f"EG{g}M{m}P010"
        if from_point and from_point != p010:
            if g == 1:
                suffix = from_point[-4:]
                if not self.rc.execute_trajectory_sync(
                        self.traj(f"tEG{g}M{m}{suffix}_To_EG{g}M{m}P010"), abort):
                    return Result.Error
            else:
                if not self.rc.execute_trajectory_sync(
                        self.traj(f"tEG2M{m}P020_To_EG2M{m}P010"), abort):
                    return Result.Error
        if not self.rc.execute_trajectory_sync(
                self.traj(f"tEG{g}M{m}P010_To_BG{g}M{m}P010"), abort):
            return Result.Error
        return Result.NoError

    # ── движение внутри станка ──────────────────────────────────────────────

    def in_machine_g1(self, m: int, abort=None) -> Result:
        """InMachineG1(M): LinTo(EG1M[m]P0i), i=10..40, проверка состояния."""
        for i in (10, 20, 30, 40):
            if i == 10:
                seg = f"tBG1M{m}P010_To_EG1M{m}P010"
            else:
                seg = f"tEG1M{m}P0{i - 10}_To_EG1M{m}P0{i}"
            if not self.rc.execute_trajectory_sync(self.traj(seg), abort):
                return Result.Error
            if self.machines[m].check_machine_state() != Result.NoError:
                self.exit_machine(1, m, f"EG1M{m}P0{i}", abort)
                return Result.Error
        return Result.NoError

    def in_machine_g2(self, m: int, abort=None) -> Result:
        """InMachineG2(M): LinTo(EG2M[m]P0i), i=10..20, проверка состояния."""
        for i in (10, 20):
            if i == 10:
                seg = f"tBG2M{m}P010_To_EG2M{m}P010"
            else:
                seg = f"tEG2M{m}P010_To_EG2M{m}P020_S"
            if not self.rc.execute_trajectory_sync(self.traj(seg), abort):
                return Result.Error
            if self.machines[m].check_machine_state() != Result.NoError:
                self.exit_machine(2, m, f"EG2M{m}P0{i}", abort)
                return Result.Error
        return Result.NoError

    # ── обдув патрона ───────────────────────────────────────────────────────

    def chuck_air_blast(self, m: int, abort=None) -> Result:
        """ChuckAirBlast(M): обдув патрона круговым проходом."""
        if not self.rc.execute_trajectory_sync(
                self.traj(f"tBG{m}P020_To_BA{m}P015"), abort):
            return Result.Error
        if not self.rc.execute_trajectory_sync(
                self.traj(f"tBA{m}P015_To_EA{m}P000"), abort):
            return Result.Error
        self.rc.io.set_do(DO.M_AirSpray, True)
        for step in (10, 20, 30, 40):
            if not self.rc.execute_trajectory_sync(
                    self.traj(f"tEA{m}P000_To_EA{m}P0{step}_S"), abort):
                self.rc.io.set_do(DO.M_AirSpray, False)
                return Result.Error
            if self.machines[m].check_machine_state() != Result.NoError:
                self.rc.io.set_do(DO.M_AirSpray, False)
                self.machines[m].lamp_alarm(True)
                return Result.Error
        self.rc.io.set_do(DO.M_AirSpray, False)
        if not self.rc.execute_trajectory_sync(
                self.traj(f"tEA{m}P000_To_BA{m}P015"), abort):
            return Result.Error
        if not self.rc.execute_trajectory_sync(
                self.traj(f"tBA{m}P015_To_BA{m}P010"), abort):
            return Result.Error
        return Result.NoError

    # ── паллет ───────────────────────────────────────────────────────────────

    def pick_workpiece(self, m: int, flags: CycleFlags, abort=None) -> Result:
        """PickWorkpiece(M): взять заготовку с паллета для станка M."""
        if not flags.g1_is_empty:
            return Result.NoError
        addr = self.pallet.get_next_address()
        if addr is None:
            flags.last_workpiece[m] = True
            return Result.NoError
        if self.pallet.depalletizing(addr) != Result.NoError:
            return Result.Error
        flags.pick_addr[m] = addr
        flags.g1_is_empty = False
        self.pallet.take_next()
        if self.pallet.get_next_address() is None:
            flags.last_workpiece[m] = True
        return Result.NoError

    def place_part_on_table(self, m: int, flags: CycleFlags,
                            abort=None) -> Result:
        """PlacePartOnTable(M): положить готовую деталь на паллет."""
        if not self.rc.execute_trajectory_sync(
                self.traj('tBGIntP010_To_BG2IntP010'), abort):
            return Result.Error
        if self.pallet.palletizing(flags.place_addr[m]) != Result.NoError:
            return Result.Error
        if not self.rc.execute_trajectory_sync(
                self.traj('tBG2IntP010_To_BGIntP010'), abort):
            return Result.Error
        return Result.NoError

    # ── станочные операции ───────────────────────────────────────────────────

    def load_workpiece(self, m: int, flags: CycleFlags, abort=None) -> Result:
        """LoadWorkpiece(M): загрузка заготовки в станок, старт обработки."""
        if flags.g1_is_empty:
            # «Если гриппер1 пуст — выходим из функции без ошибки»
            return Result.NoError

        if self.machines[m].wait_for_door_open(abort) != Result.NoError:
            return Result.Error
        if self.machines[m].wait_for_chuck_relax(1, False, abort) != Result.NoError:
            return Result.Error
        if self.machines[m].check_machine_state() != Result.NoError:
            return Result.Error
        if self.in_machine_g1(m, abort) != Result.NoError:
            return Result.Error

        # Разжатие гриппера 1 у патрона, установка флага
        self.rc.io.gripper_do(1, False)
        flags.g1_is_empty = True
        if self.exit_machine(1, m, f"EG1M{m}P040", abort) != Result.NoError:
            return Result.Error
        if self.machines[m].wait_for_chuck_clamp(1, abort) != Result.NoError:
            return Result.Error
        if not self.rc.move_to_point_sync(f"BG{m}P020", 'joint', abort):
            return Result.Error
        if self.machines[m].wait_for_door_close(abort) != Result.NoError:
            return Result.Error
        if self.machines[m].start_cnc(abort) != Result.NoError:
            return Result.Error
        flags.is_machine_load[m] = True
        if not self.move_to_g_int(m, abort):
            return Result.Error
        return Result.NoError

    def unload_part(self, m: int, flags: CycleFlags, abort=None) -> Result:
        """UnloadPart(M): выгрузка готовой детали из станка."""
        if self.machines[m].wait_for_door_open(abort) != Result.NoError:
            return Result.Error
        if self.chuck_air_blast(m, abort) != Result.NoError:
            return Result.Error
        if not self.rc.move_to_point_sync(f"BG{m}P020", 'joint', abort):
            return Result.Error
        if not self.rc.execute_trajectory_sync(
                self.traj(f"tBG{m}P020_To_BG2{m}P010"), abort):
            return Result.Error
        if self.in_machine_g2(m, abort) != Result.NoError:
            return Result.Error
        if self.machines[m].check_machine_state() != Result.NoError:
            return Result.Error

        # Захват детали гриппером 2
        if self.grippers[2].clamp(abort) != Result.NoError:
            return Result.Error
        if self.machines[m].wait_for_chuck_relax(2, True, abort) != Result.NoError:
            return Result.Error
        if self.exit_machine(2, m, f"EG2M{m}P020", abort) != Result.NoError:
            return Result.Error

        flags.is_machine_load[m] = False
        flags.place_addr[m] = flags.cur_addr[m]
        flags.cur_addr[m] = flags.pick_addr[m]
        if not self.rc.move_to_point_sync(f"BG{m}P020", 'joint', abort):
            return Result.Error
        if self.chuck_air_blast(m, abort) != Result.NoError:
            return Result.Error
        return Result.NoError

    def error_reset(self, m: int, flags: CycleFlags, abort=None) -> None:
        """ErrorReset(M): при ошибке — сброс гриппера 1, возврат в исходную."""
        if flags.m_state[m] != MachineState.Error:
            return
        if self.rc.execute_trajectory_sync(
                self.traj('tBGIntP010_To_BG1IntP010'), abort):
            self.rc.io.gripper_do(1, False)
            self.rc.execute_trajectory_sync(
                self.traj('tBG1IntP010_To_BGIntP010'), abort)
        flags.m_state[m] = MachineState.NotActive