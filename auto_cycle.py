"""
Главный цикл авто-режима (отдельный поток).

Состояния: M_state (NotActive/LoadWorkpiece/Complete/Error), флаги
G1IsEmptyFlag, isMachineLoad[1,2], LastWorkpiece[1,2]. NotActive также
означает ожидание заготовки/смены полки. СТОП — немедленный hold и флаг
abort, состояние сохраняется; повторный СТАРТ продолжает с места.
"""
import threading
import time

from config import IO_POLL_SEC
from cycle_ops import CycleFlags, CycleOps
from io_map import DI, DO
from states_modes_errors import MachineState, Result, LastError


class AutoCycle(threading.Thread):
    """Поток главного цикла авто-режима."""

    def __init__(self, rc, logger, blinker, heartbeat_cb=None):
        super().__init__(daemon=True, name="AutoCycleThread")
        self.rc = rc
        self.log = logger
        self.blinker = blinker
        self.gui = logger.getChild("gui.cycle")
        self.heartbeat = heartbeat_cb
        self.stop = threading.Event()
        self.abort = threading.Event()
        self.start_request = threading.Event()
        self.running = False
        self.resume_pending = False
        self.cycle_state = 'idle'
        self.ops = CycleOps(rc, logger, blinker)
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
                    'resume_pending': self.resume_pending,
                    'is_machine_load': dict(self.flags.is_machine_load),
                    'last_workpiece': dict(self.flags.last_workpiece),
                    'pick_addr': {m: str(a) if a else None
                                  for m, a in self.flags.pick_addr.items()},
                    'machine_addr': {m: str(a) if a else None
                                     for m, a in self.flags.machine_addr.items()},
                    'place_addr': {m: str(a) if a else None
                                   for m, a in self.flags.place_addr.items()},
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
        resume = self.resume_pending

        # Сброс аварийных ламп
        self.rc.io.machine_do(1, 'LampAlarm', False) # uncomment on commissioning
        self.rc.io.machine_do(2, 'LampAlarm', False) # uncomment on commissioning
        print("lamps are on")

        # Ожидание физической кнопки СТАРТ
        if not self.rc.io.wait_di(DI.START_STOP,
                             True,
                             timeout=3600,
                             abort_event=self.abort):
            self.rc.message("Автоцикл: СТАРТ не подтверждён", 'warning')
            return

        self.rc.io.set_do(DO.M_LampRun, True)

        # Не начинаем движение, пока не подтверждён выход из станка
        if self.ops.inside_any():
            self.rc.message(
                "Автоцикл: не подтверждён выход из станка", 'error')
            self.rc.io.set_do(DO.M_LampRun, False)
            return

        # Сброс ошибок (по станкам)
        self.ops.error_reset(1, self.flags, self.abort)
        self.ops.error_reset(2, self.flags, self.abort)
        if any(self.flags.m_state[m] == MachineState.Error for m in (1, 2)):
            self.rc.message("Автоцикл: ошибка станка не сброшена", 'error')
            self.rc.io.set_do(DO.M_LampRun, False)
            return

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

        if not resume:
            self.flags.reset()

        # Инициализация движения
        if not self.ops.init_move(self.abort):
            self.rc.io.set_do(DO.M_LampRun, False)
            if not self.abort.is_set():
                self.rc.message("Автоцикл: InitMove не выполнен", 'error')
            return
        if self.abort.is_set():
            self.rc.io.set_do(DO.M_LampRun, False)
            return

        if resume:
            self.gui.info("Автоцикл: продолжение после СТОПа")
        else:
            self.gui.info("Автоцикл: новый цикл")

        # Внутренний цикл по станкам M1, M2
        try:
            self.cycle_inner(self.ops, self.flags)
        finally:
            self.resume_pending = (
                self.abort.is_set()
                and not self.stop.is_set()
                and not self.all_complete(self.flags))
            if self.resume_pending:
                self.gui.info(
                    "Автоцикл: остановлен, состояние сохранено для продолжения")
            self.rc.io.set_do(DO.M_LampRun, False)
            if not self.abort.is_set():
                self.rc.message("Автоцикл: завершён", "warning")
            self.sync_state()

    def cycle_inner(self, ops: CycleOps, flags: CycleFlags) -> None:
        while not self.abort.is_set() and not self.stop.is_set():
            # Физический СТОП: сигнал START/STOP сброшен
            if not self.rc.io.get_di(DI.START_STOP):
                self.rc.message("Автоцикл: СТОП по кнопке", "warning")
                self.abort.set()
                break

            pending_place = next(
                (m for m in (1, 2) if flags.place_addr[m] is not None), None)
            if pending_place is not None:
                if not self._flush_pending_place(pending_place, ops, flags):
                    if flags.m_state[pending_place] == MachineState.Error:
                        self.rc.message(
                            f"Автоцикл: ошибка укладки M{pending_place}, "
                            "движение остановлено", 'error')
                        self.request_stop()
                    break
                if self.abort.is_set():
                    break

            for m in (1, 2): # надо ли в цикле или лучше по отдельности???
                self.sync_state()
                if not self.machine_ready(m):
                    continue
                self.process_machine(m, ops, flags)
                if flags.m_state[m] == MachineState.Error:
                    self.rc.message(
                        f"Автоцикл: ошибка M{m}, движение остановлено",
                        'error')
                    self.request_stop()
                    break
                if self.abort.is_set():
                    break
            if self.all_complete(flags):
                break
            time.sleep(IO_POLL_SEC)

    def set_error(self, m: int, flags: CycleFlags) -> None:
        if self.abort.is_set():
            return
        flags.m_state[m] = MachineState.Error

    def set_complete(self, m: int, flags: CycleFlags) -> None:
        flags.m_state[m] = MachineState.Complete
        self.gui.info("M%d: обработка завершена", m)

    def _flush_pending_place(self, m: int, ops: CycleOps,
                             flags: CycleFlags) -> bool:
        addr = flags.place_addr[m]
        self.gui.info("M%d: отложенная укладка %s (%s)",
                      m, addr, ops.cell_state_name(addr))
        if ops.place_part_on_table(m, flags, self.abort) != Result.NoError:
            self.set_error(m, flags)
            return False
        return True

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
            if flags.machine_addr[m] is None:
                self.set_error(m, flags)
                return

            if flags.g1_is_empty:
                if ops.pallet.next_raw_cell() is not None:
                    # Заготовка на текущей полке есть: берём её ДО выгрузки,
                    # чтобы после выгрузки сразу установить новую.
                    if ops.pick_workpiece(m, flags, self.abort) != Result.NoError:
                        self.set_error(m, flags)
                        return
                    if not flags.picked[m]:
                        self.set_error(m, flags)
                        return
                else:
                    # На текущей полке заготовок нет. Сначала выгружаем и
                    # укладываем готовую деталь, иначе полку нельзя сменить.
                    if ops.unload_part(m, flags, self.abort) != Result.NoError:
                        self.set_error(m, flags)
                        return
                    if not ops.move_to_g_int(m, self.abort):
                        self.set_error(m, flags)
                        return
                    if ops.place_part_on_table(m, flags, self.abort) != Result.NoError:
                        self.set_error(m, flags)
                        return
                    if flags.last_workpiece[m]:
                        flags.m_state[m] = MachineState.Complete
                        return
                    if ops.pick_workpiece(m, flags, self.abort) != Result.NoError:
                        self.set_error(m, flags)
                        return
                    if not flags.picked[m]:
                        if flags.last_workpiece[m]:
                            flags.m_state[m] = MachineState.Complete
                        else:
                            # Ждём смену полки или возврат детали другого станка
                            flags.m_state[m] = MachineState.NotActive
                        return
                    if not ops.move_from_g_int(m, self.abort):
                        self.set_error(m, flags)
                        return
                    if ops.load_workpiece(m, flags, self.abort) != Result.NoError:
                        self.set_error(m, flags)
                        return
                    flags.m_state[m] = MachineState.LoadWorkpiece
                    return
            else:
                # Новая заготовка уже в гриппере 1 (продолжение после СТОПа)
                if flags.pick_addr[m] is None:
                    self.set_error(m, flags)
                    return

            # Новая заготовка в гриппере 1: к станку, выгрузить готовую,
            # установить новую и уложить готовую на паллет.
            if not ops.move_from_g_int(m, self.abort):
                self.set_error(m, flags)
                return
            if ops.unload_part(m, flags, self.abort) != Result.NoError:
                self.set_error(m, flags)
                return
            if not ops.move_to_safe(m, self.abort):
                self.set_error(m, flags)
                return
            if ops.load_workpiece(m, flags, self.abort) != Result.NoError:
                self.set_error(m, flags)
                return
            if ops.place_part_on_table(m, flags, self.abort) != Result.NoError:
                self.set_error(m, flags)
                return
            flags.m_state[m] = MachineState.LoadWorkpiece
            return

        # Станок не был в работе
        if flags.g1_is_empty and self.machine_ready(m) and flags.last_workpiece[m]:
            self.set_complete(m, flags)
            return
        if not flags.g1_is_empty:
            # Деталь уже взята для этого станка (продолжение после СТОПа)
            if flags.pick_addr[m] is None:
                self.set_error(m, flags)
                return
        else:
            if ops.pick_workpiece(m, flags, self.abort) != Result.NoError:
                self.set_error(m, flags)
                return
            if not flags.picked[m]:
                if flags.last_workpiece[m]:
                    self.set_complete(m, flags)
                else:
                    # Заготовок пока нет: не двигаемся к станку
                    flags.m_state[m] = MachineState.NotActive
                return

        if not ops.move_from_g_int(m, self.abort):
            self.set_error(m, flags)
            return
        if ops.load_workpiece(m, flags, self.abort) == Result.NoError:
            flags.m_state[m] = MachineState.LoadWorkpiece
        else:
            self.set_error(m, flags)

    @staticmethod
    def all_complete(flags: CycleFlags) -> bool:
        return all(flags.m_state[m] == MachineState.Complete
                   for m in (1, 2))
