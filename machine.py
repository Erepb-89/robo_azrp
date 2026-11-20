"""
Функции станка M (M1/M2): двери, патрон, пуск, проверки.

Не зависит от RobotController напрямую: использует только rc.io, rc.message
и синхронные движения (ops.exit_machine / ops.move_to_safe).
"""
import time

from config import (MAX_D_SEC, MAX_C_SEC, MAX_M_SEC,
                    CHUCK_PULSE_ON_SEC, CHUCK_PULSE_OFF_SEC,
                    CNC_START_PULSE_SEC, CNC_START_SETTLE_SEC)
from io_map import MACHINE_DI
from states_modes_errors import Result, LastError


class CncMachine:
    """Станок M: двери, патрон, сигналы готовности, пуск обработки."""

    def __init__(self, m: int, rc, logger, blinker):
        self.m = m
        self.rc = rc
        self.io = rc.io
        self.log = logger
        self.blinker = blinker
        self.ops = None  # CycleOps, привязывается через bind_ops()

    def bind_ops(self, ops) -> None:
        self.ops = ops

    # ── вспомогательное ──────────────────────────────────────────────────────

    def message(self, text: str, level: str = 'warning') -> None:
        self.rc.message(text, level)

    def _move_safe(self, abort=None) -> bool:
        """MoveTo(BGM[M]P020) — точка смены гриппера при ошибке."""
        if self.ops is None:
            return False
        return self.ops.move_to_safe(self.m, abort)

    def lamp_alarm(self, on: bool) -> bool:
        """Аварийная индикация на WB-LED (красное мигание)."""
        if on:
            self.blinker.blink("R")
        return True

    def _di(self, role: str):
        return MACHINE_DI[self.m][role]

    def _alarm_error(self) -> LastError:
        return (LastError.err_cnc1_alarm if self.m == 1
                else LastError.err_cnc2_alarm)

    def alarm_active(self) -> bool:
        return self.io.machine_di(self.m, 'Alarm')

    def _check_alarm(self) -> Result:
        if not self.alarm_active():
            return Result.NoError
        self.rc.state.update(last_error=self._alarm_error())
        self.message(f"M{self.m}: авария станка", 'error')
        self.lamp_alarm(True)
        return Result.Error

    # ── проверки состояния ───────────────────────────────────────────────────

    def check_machine_state(self) -> Result:
        """Готов ли станок М к работе и открыта ли у него дверь."""
        if self._check_alarm() != Result.NoError:
            return Result.Error
        if not self.io.machine_di(self.m, 'Ready'):
            self.rc.state.update(last_error=LastError.err_cnc_not_ready)
            self.message("CNC Not Ready", 'error')
            return Result.Error
        if not self.io.machine_di(self.m, 'DoorOpenSQ'):
            self.rc.state.update(last_error=LastError.err_door_not_open)
            self.message("Door Not Open", 'error')
            return Result.Error
        return Result.NoError

    def chuck_is_open(self) -> bool:
        """Патрон открыт: ChuckRelax активен и ChuckClamped не активен."""
        if not self.io.machine_di(self.m, 'ChuckRelax'):
            return False
        if self.io.machine_di(self.m, 'ChuckClamped'):
            return False
        return True

    # ── двери ────────────────────────────────────────────────────────────────

    def open_door(self) -> None:
        self.io.machine_do(self.m, 'DoorCloseCMD', False)
        self.io.machine_do(self.m, 'DoorOpenCMD', True)

    def close_door(self) -> None:
        self.io.machine_do(self.m, 'DoorCloseCMD', True)
        self.io.machine_do(self.m, 'DoorOpenCMD', False)

    def wait_for_door_open(self, abort=None) -> Result:
        if self._check_alarm() != Result.NoError:
            return Result.Error
        if not self.io.machine_di(self.m, 'Ready'):
            self.rc.state.update(last_error=LastError.err_door_not_open)
            self.message("CNC Not Ready", 'error')
            return Result.Error
        if self.io.machine_di(self.m, 'DoorOpenSQ'):
            return Result.NoError
        self.open_door()
        if not self.io.wait_di(self._di('DoorOpenSQ'), True, MAX_D_SEC, abort):
            self.lamp_alarm(True)
            self.message("Door Not Open", 'error')
            self._move_safe(abort)
            return Result.Error
        return Result.NoError

    def wait_for_door_close(self, abort=None) -> Result:
        if self._check_alarm() != Result.NoError:
            return Result.Error
        self.close_door()
        if not self.io.wait_di(self._di('DoorCloseSQ'), True, MAX_D_SEC, abort):
            self.rc.state.update(last_error=LastError.err_door_not_close)
            self.lamp_alarm(True)
            self.message("Door Not Close", 'error')
            self._move_safe(abort)
            return Result.Error
        return Result.NoError

    # ── патрон ───────────────────────────────────────────────────────────────

    def _pulse_chuck(self, role: str) -> None:
        self.io.machine_do(self.m, role, True)
        time.sleep(CHUCK_PULSE_ON_SEC)
        self.io.machine_do(self.m, role, False)
        time.sleep(CHUCK_PULSE_OFF_SEC)

    def wait_for_chuck_relax(self, g: int, pick: bool, abort=None) -> Result:
        """Ожидание открытия патрона. При ошибке и pick==true — выход из станка,
        разжимая гриппер G"""
        if self.check_machine_state() != Result.NoError:
            return Result.Error
        if self.chuck_is_open():
            return Result.NoError

        deadline = time.monotonic() + MAX_C_SEC
        while True:
            if abort is not None and abort.is_set():
                return Result.Error
            if self.chuck_is_open():
                return Result.NoError
            if time.monotonic() >= deadline:
                self.rc.state.update(last_error=LastError.err_chuck_not_relax)
                self.lamp_alarm(True)
                self.message("Chuck Not Relax", 'error')
                can_move_safe = not pick
                if pick:
                    self.io.gripper_do(g, False)
                    if self.ops is not None:
                        can_move_safe = (
                            self.ops.exit_machine(
                                g, self.m, f"EG{g}M{self.m}P020", abort)
                            == Result.NoError)
                    if not can_move_safe:
                        self.message(
                            f"Авария: не удалось выйти из станка M{self.m}",
                            'error')
                if can_move_safe:
                    self._move_safe(abort)
                return Result.Error
            self._pulse_chuck('ChuckOpen')

    def wait_for_chuck_clamp(self, g: int, abort=None,
                             exit_on_error: bool = False) -> Result:
        """Ожидание закрытия патрона."""
        if self.check_machine_state() != Result.NoError:
            return Result.Error
        if not self.chuck_is_open():
            return Result.NoError

        deadline = time.monotonic() + MAX_C_SEC
        while True:
            if abort is not None and abort.is_set():
                return Result.Error
            if not self.chuck_is_open():
                return Result.NoError
            if time.monotonic() >= deadline:
                self.rc.state.update(last_error=LastError.err_chuck_not_clamp)
                self.lamp_alarm(True)
                self.message("Chuck Not Clamp", 'error')
                can_move_safe = not exit_on_error
                if exit_on_error:
                    if self.ops is not None:
                        can_move_safe = (
                            self.ops.exit_machine(
                                g, self.m, f"EG{g}M{self.m}P020", abort)
                            == Result.NoError)
                    if not can_move_safe:
                        self.message(
                            f"Авария: не удалось выйти из станка M{self.m}",
                            'error')
                if can_move_safe:
                    self._move_safe(abort)
                return Result.Error
            self._pulse_chuck('ChuckClose')

    # ── пуск станка ──────────────────────────────────────────────────────────

    def start_cnc(self, abort=None) -> Result:
        """Импульс StartProcess, затем ожидание Ready."""
        if self._check_alarm() != Result.NoError:
            return Result.Error
        self.io.machine_do(self.m, 'StartProcess', True)
        time.sleep(CNC_START_PULSE_SEC)
        self.io.machine_do(self.m, 'StartProcess', False)
        time.sleep(CNC_START_SETTLE_SEC)
        if not self.io.wait_di(self._di('Ready'), True, MAX_M_SEC, abort):
            self.rc.state.update(last_error=LastError.err_cnc_not_started)
            self.lamp_alarm(True)
            self.message("Not Started", 'error')
            return Result.Error
        return Result.NoError