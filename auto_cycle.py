"""
Главный цикл авто-режима (отдельный поток).

Состояния: M_state (NotActive/LoadWorkpiece/Complete/Error), флаги
G1IsEmptyFlag, isMachineLoad[1,2], LastWorkpiece[1,2]. NotActive также
означает ожидание заготовки/смены полки. ПАУЗА — немедленный hold с
сохранением состояния; СТОП — hold и полный сброс памяти цикла.
"""
import threading
import time

from config import IO_POLL_SEC
from cycle_ops import CycleFlags, CycleOps
from io_map import DIModbus
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
        self._cycle_machines = {1: True, 2: True}

        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._control = None  # 'pause' | 'stop'
        self._busy = False    # поток внутри execute_cycle

    # ── управление ───────────────────────────────────────────────────────────

    def request_start(self) -> None:
        machines = self.rc.get_active_machines()
        with self._lock:
            self._cycle_machines = dict(machines)
            if not any(self._cycle_machines.values()):
                self.start_request.clear()
                return
            if not self.running and self._control is None:
                self.set_cycle_state(
                    'waiting_resume' if self.resume_pending
                    else 'waiting_start')
            self.start_request.set()
            self._wake.set()

    def _active_machine_ids(self) -> list:
        return [m for m in (1, 2) if bool(self._cycle_machines.get(m, True))]

    def _is_machine_active(self, m: int) -> bool:
        return bool(self._cycle_machines.get(m, True))

    def request_pause(self) -> None:
        """ПАУЗА: немедленный hold, состояние сохраняется."""
        with self._lock:
            if self._control != 'stop':
                self._control = 'pause'
            self.abort.set()
            self.start_request.clear()
            self._wake.set()
        self._hold()

    def request_stop(self) -> None:
        """СТОП: немедленный hold и полный сброс памяти цикла."""
        with self._lock:
            self._control = 'stop'
            self.abort.set()
            self.start_request.clear()
            self.resume_pending = False
            self._wake.set()
        self._hold()

    def _hold(self) -> None:
        try:
            self.rc.manipulator_stop_drive()
        except Exception as err:
            self.rc.state.update(last_error=LastError.err_cycle_aborted)
            print(err)

    def _apply_reset(self) -> None:
        """Сброс логической памяти цикла. Вызывать под self._lock."""
        self.flags.reset()
        self.ops.reset_memory()
        self.resume_pending = False
        self.running = False
        self._control = None
        self.set_cycle_state('idle')
        self.gui.info("Автоцикл: память сброшена")

    def is_active(self) -> bool:
        """Есть ли запрошенный/выполняющийся цикл."""
        with self._lock:
            return bool(self._busy or self._control is not None
                        or self.cycle_state != 'idle')

    def shutdown(self) -> None:
        self.stop.set()
        self.abort.set()
        self.start_request.set()
        self._wake.set()

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
            if not self._wake.wait(timeout=0.5):
                continue
            self._wake.clear()

            with self._lock:
                if self._control == 'stop':
                    self._apply_reset()
                elif self._control == 'pause':
                    self._control = None
                    if not self._busy and self.cycle_state == 'waiting_start':
                        self.set_cycle_state('idle')

                if not self.start_request.is_set() or self.stop.is_set():
                    continue

                self.start_request.clear()
                self._busy = True
                self.abort.clear()
                self.running = False
                self.set_cycle_state(
                    'waiting_resume' if self.resume_pending
                    else 'waiting_start')

            try:
                self.execute_cycle()
            except Exception as e:
                self.log.exception(f"AutoCycle error: {e}")
                self.rc.message(f"Автоцикл: ошибка {e}", 'error')
            finally:
                with self._lock:
                    if self._control == 'stop':
                        self._apply_reset()
                    else:
                        if self.abort.is_set() and not self.stop.is_set():
                            if self.running:
                                self.resume_pending = not self.all_complete(
                                    self.flags)
                        elif not self.abort.is_set():
                            self.resume_pending = False
                        self.running = False
                        self.set_cycle_state(
                            'waiting_resume' if self.resume_pending
                            else 'idle')
                    self._busy = False
        self.log.info("AutoCycle thread stopped")

    # ── главный цикл (авто) ─────────────────────────────────────────────

    def execute_cycle(self) -> None:
        resume = self.resume_pending
        active = self._active_machine_ids()
        if not active:
            self.rc.message(
                "Автоцикл: нет активных станков — запуск отменён", 'error')
            return

        # Ожидание физической кнопки СТАРТ
        if not self.rc.wait_mb_di(DIModbus.START_STOP,
                                  True,
                                  timeout=3600,
                                  abort_event=self.abort):
            self.rc.message("Автоцикл: СТАРТ не подтверждён", 'warning')
            return
        if self.abort.is_set():
            return

        self.running = True
        self.set_cycle_state('running')

        # Не начинаем движение, пока не подтверждён выход из станка
        if self.ops.inside_any():
            self.rc.message(
                "Автоцикл: не подтверждён выход из станка", 'error')
            return

        # Сброс ошибок (только по активным станкам)
        for m in active:
            self.ops.error_reset(m, self.flags, self.abort)
        if any(self.flags.m_state[m] == MachineState.Error for m in active):
            self.rc.message("Автоцикл: ошибка станка не сброшена", 'error')
            return

        # Проверка авто-режима дверей (Reallab Modbus, только активные)
        door_auto = {m: self.rc.machine_mb_di(m, 'DoorAuto') for m in active}
        if not all(door_auto.values()):
            self.rc.message("Двери не в автоматическом режиме", 'error')
            return

        # Перезагрузка грипперов 1, 2
        if self.rc.gripper_mb_di(1, 'Switch'):
            self.ops.grippers[1].reset(self.abort)
        if self.rc.gripper_mb_di(2, 'Switch'):
            self.ops.grippers[2].reset(self.abort)

        if not resume:
            self.flags.reset()

        # Инициализация движения
        if not self.ops.init_move(self.abort):
            if not self.abort.is_set():
                self.rc.message("Автоцикл: InitMove не выполнен", 'error')
            return
        if self.abort.is_set():
            return

        if resume:
            self.gui.info("Автоцикл: продолжение после ПАУЗЫ")
        else:
            self.gui.info("Автоцикл: новый цикл")

        # Внутренний цикл по станкам M1, M2
        try:
            self.cycle_inner(self.ops, self.flags)
        finally:
            stop_requested = self._control == 'stop'
            self.resume_pending = (
                not stop_requested
                and self.abort.is_set()
                and not self.stop.is_set()
                and not self.all_complete(self.flags))
            if self.resume_pending:
                self.gui.info(
                    "Автоцикл: приостановлен, состояние сохранено для продолжения")
            if not self.abort.is_set():
                self.rc.message("Автоцикл: завершён", "warning")
            self.sync_state()

    def cycle_inner(self, ops: CycleOps, flags: CycleFlags) -> None:
        active = self._active_machine_ids()
        if not active:
            return
        while not self.abort.is_set() and not self.stop.is_set():
            # Физический СТОП: сигнал START/STOP сброшен (пауза с сохранением)
            if not self.rc.get_modbus_di(DIModbus.START_STOP):
                self.rc.message("Автоцикл: ПАУЗА по кнопке", "warning")
                self.abort.set()
                break

            pending_place = next(
                (m for m in active if flags.place_addr[m] is not None), None)
            if pending_place is not None:
                if not self._flush_pending_place(pending_place, ops, flags):
                    if flags.m_state[pending_place] == MachineState.Error:
                        self.rc.message(
                            f"Автоцикл: ошибка укладки M{pending_place}, "
                            "движение остановлено", 'error')
                        self.request_pause()
                    break
                if self.abort.is_set():
                    break

            for m in active:
                self.sync_state()
                if not self.machine_ready(m):
                    if flags.m_state[m] == MachineState.Error:
                        self.rc.message(
                            f"Автоцикл: авария M{m}, движение остановлено",
                            'error')
                        self.request_pause()
                        break
                    continue
                self.process_machine(m, ops, flags)
                if flags.m_state[m] == MachineState.Error:
                    self.rc.message(
                        f"Автоцикл: ошибка M{m}, движение остановлено",
                        'error')
                    self.request_pause()
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
        self.gui.info(f"M{m}: обработка завершена")

    def _flush_pending_place(self, m: int, ops: CycleOps,
                             flags: CycleFlags) -> bool:
        addr = flags.place_addr[m]
        self.gui.info(f"M{m}: отложенная укладка {addr} {(ops.cell_state_name(addr))})")
        if ops.place_part_on_table(m, flags, self.abort) != Result.NoError:
            self.set_error(m, flags)
            return False
        return True

    def machine_ready(self, m: int) -> bool:
        if not self._is_machine_active(m):
            return False
        if self.flags.m_state[m] in (MachineState.Error, MachineState.Complete):
            return False
        machine = self.ops.machines[m]
        if machine.alarm_active():
            self.rc.state.update(
                last_error=(LastError.err_cnc1_alarm if m == 1
                            else LastError.err_cnc2_alarm))
            machine.lamp_alarm(True)
            self.rc.message(f"M{m}: авария станка", 'error')
            self.set_error(m, self.flags)
            return False
        if not self.rc.machine_mb_di(m, 'DoorAuto'):
            return False
        if not self.rc.io.machine_di(m, 'Ready'):
            return False
        return True

    def process_machine(self, m: int, ops: CycleOps, flags: CycleFlags) -> None:
        if not self._is_machine_active(m):
            return
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
                # Новая заготовка уже в гриппере 1 (продолжение после ПАУЗЫ)
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
            # Деталь уже взята для этого станка (продолжение после ПАУЗЫ)
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

    def all_complete(self, flags: CycleFlags) -> bool:
        active = self._active_machine_ids()
        if not active:
            return False
        return all(flags.m_state[m] == MachineState.Complete
                   for m in active)
