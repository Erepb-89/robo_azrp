"""
Главный цикл авто-режима (отдельный поток).

Состояния: M_state (NotActive/LoadWorkpiece/Complite/Error), флаги
G1IsEmptyFlag, isMachineLoad[1,2], LastWorkpiece[1,2]. СТОП — немедленный
hold и флаг abort, состояние сохраняется; повторный СТАРТ продолжает с места.
"""
import threading
import time

from config import IO_POLL_SEC
from cycle_ops import CycleFlags, CycleOps
from io_map import DI, DO
from states_modes_errors import MachineState, Result, LastError


class AutoCycle(threading.Thread):
    """Поток главного цикла авто-режима."""

    def __init__(self, rc, logger, heartbeat_cb=None):
        super().__init__(daemon=True, name="AutoCycleThread")
        self.rc = rc
        self.log = logger
        self.heartbeat = heartbeat_cb
        self.stop = threading.Event()
        self.abort = threading.Event()
        self.start_request = threading.Event()
        self.running = False
        self.cycle_state = 'idle'
        self.ops = CycleOps(rc, logger)
        self.flags = CycleFlags()

    # ── управление ───────────────────────────────────────────────────────────

    def request_start(self) -> None:
        self.start_request.set()

    def request_stop(self) -> None:
        """СТОП: немедленный hold, состояние сохраняется."""
        self.abort.set()
        try:
            self.rc.manipulator_stop_drive()
        except Exception as err:
            self.rc.state.update(last_error=LastError.err_cycle_aborted)
            print(err)

    def shutdown(self) -> None:
        self.stop.set()
        self.abort.set()
        self.start_request.set()

    # ── состояние для GUI ────────────────────────────────────────────────────

    def set_cycle_state(self, value: str) -> None:
        self.cycle_state = value
        self.sync_state()

    def sync_state(self) -> None:
        try:
            self.rc.state.update(
                cycle_state=self.cycle_state,
                m_state={m: int(s.value) for m, s in self.flags.m_state.items()},
                flags={
                    'g1_is_empty': self.flags.g1_is_empty,
                    'is_machine_load': dict(self.flags.is_machine_load),
                    'last_workpiece': dict(self.flags.last_workpiece),
                },
            )
        except Exception as e:
            self.log.debug(f"AutoCycle sync state: {e}")

    # ── поток ────────────────────────────────────────────────────────────────

    def run(self) -> None:
        self.log.info("AutoCycle thread started")

        def beater():
            while not self.stop.is_set() and self.is_alive():
                if self.heartbeat:
                    try:
                        self.heartbeat('cycle')
                    except Exception as err:
                        print(err)
                time.sleep(1.0)

        threading.Thread(target=beater, name="AutoCycleHeartbeat",
                         daemon=True).start()

        while not self.stop.is_set():
            if not self.start_request.wait(timeout=0.5):
                continue
            self.start_request.clear()
            self.abort.clear()
            self.running = True
            self.set_cycle_state('running')
            try:
                self.execute_cycle()
            except Exception as e:
                self.log.exception(f"AutoCycle error: {e}")
                self.rc.message(f"Автоцикл: ошибка {e}", 'error')
            finally:
                self.running = False
                self.set_cycle_state('idle')
        self.log.info("AutoCycle thread stopped")

    # ── главный цикл (авто) ─────────────────────────────────────────────

    def execute_cycle(self) -> None:
        # Сброс аварийных ламп
        # rc.io.machine_do(1, 'LampAlarm', False) # uncomment on commissioning
        # rc.io.machine_do(2, 'LampAlarm', False) # uncomment on commissioning

        # Ожидание физической кнопки СТАРТ
        if not self.rc.io.wait_di(DI.START_STOP,
                             True,
                             timeout=3600,
                             abort_event=self.abort):
            self.rc.message("Автоцикл: СТАРТ не подтверждён", 'warning')
            return

        self.rc.io.set_do(DO.M_LampRun, True)

        # Сброс ошибок (по станкам)
        self.ops.error_reset(1, self.flags, self.abort)
        self.ops.error_reset(2, self.flags, self.abort)

        # Проверка авто-режима дверей
        door_auto = {1: self.rc.io.machine_di(1, 'DoorAuto'),
                     2: self.rc.io.machine_di(2, 'DoorAuto')}
        for m in (1, 2):
            self.rc.io.machine_do(m, 'LampAuto', door_auto[m])
        if not (door_auto[1] and door_auto[2]): # может лучше проверять отдельно???
            self.rc.message("Двери не в автоматическом режиме", 'error')
            self.rc.io.set_do(DO.M_LampRun, False)
            return

        # Перезагрузка грипперов 1, 2
        if self.rc.io.gripper_di(1, 'Switch'):
            self.ops.grippers[1].reset(self.abort)
        if self.rc.io.gripper_di(2, 'Switch'):
            self.ops.grippers[2].reset(self.abort)

        # Инициализация движения
        self.flags.reset()
        self.ops.init_move(self.abort)
        if self.abort.is_set():
            self.rc.io.set_do(DO.M_LampRun, False)
            return

        # Внутренний цикл по станкам M1, M2
        self.cycle_inner(self.ops, self.flags)

        self.rc.io.set_do(DO.M_LampRun, False)
        if not self.abort.is_set():
            self.rc.message("Автоцикл: завершён")
        self.sync_state()

    def cycle_inner(self, ops: CycleOps, flags: CycleFlags) -> None:
        while not self.abort.is_set() and not self.stop.is_set():
            # Физический СТОП: сигнал START/STOP сброшен
            if not self.rc.io.get_di(DI.START_STOP):
                self.rc.message("Автоцикл: СТОП по кнопке", 'warning')
                self.abort.set()
                break

            for m in (1, 2): # надо ли в цикле или лучше по отдельности???
                self.sync_state()
                if not self.machine_ready(m):
                    continue
                self.process_machine(m, ops, flags)
                if self.abort.is_set():
                    break
            if self.all_complete(flags):
                break
            time.sleep(IO_POLL_SEC)

    def machine_ready(self, m: int) -> bool:
        if self.flags.m_state[m] in (MachineState.Error, MachineState.Complete):
            return False
        if not self.rc.io.machine_di(m, 'DoorAuto'):
            return False
        if not self.rc.io.machine_di(m, 'Ready'):
            return False
        return True

    def process_machine(self, m: int, ops: CycleOps, flags: CycleFlags) -> None:
        if flags.is_machine_load[m]:
            # Станок уже был в работе
            if ops.unload_part(m, flags, self.abort) != Result.NoError:
                flags.m_state[m] = MachineState.Error
                return
            if not flags.last_workpiece[m]:
                # Заготовки не закончились: взять новую, загрузить, убрать готовую
                if (ops.pick_workpiece(m, flags, self.abort) == Result.NoError
                        and ops.load_workpiece(m, flags, self.abort) == Result.NoError
                        and ops.place_part_on_table(m, flags, self.abort) == Result.NoError):
                    flags.m_state[m] = MachineState.LoadWorkpiece
                else:
                    flags.m_state[m] = MachineState.Error
            else:
                # Последняя заготовка: убрать готовую деталь, станок завершил работу
                if ops.place_part_on_table(m, flags, self.abort) == Result.NoError:
                    flags.m_state[m] = MachineState.Complete
                else:
                    flags.m_state[m] = MachineState.Error
                ops.move_to_g_int(m, self.abort)
        else:
            # Станок не был в работе
            if flags.g1_is_empty and flags.last_workpiece[m]:
                # Заготовок для M больше нет, станок не загружен
                flags.m_state[m] = MachineState.Complete
                ops.move_to_g_int(m, self.abort)
                return
            # Сначала взять заготовку с паллета, затем к точке смены гриппера
            if ops.pick_workpiece(m, flags, self.abort) != Result.NoError:
                flags.m_state[m] = MachineState.Error
                return
            ops.move_from_g_int(m, self.abort)
            if ops.load_workpiece(m, flags, self.abort) == Result.NoError:
                flags.m_state[m] = MachineState.LoadWorkpiece
            else:
                flags.m_state[m] = MachineState.Error

    @staticmethod
    def all_complete(flags: CycleFlags) -> bool:
        return all(flags.m_state[m] in (MachineState.Complete,
                                        MachineState.NotActive)
                   for m in (1, 2))
